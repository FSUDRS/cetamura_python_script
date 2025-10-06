# Post-Processing Validation Implementation Plan

## Overview
This document outlines the implementation of comprehensive post-processing validation for the Cetamura batch processing script. The validation system addresses critical gaps in output verification while maintaining backward compatibility.

## Problem Statement

### Current State
- System tracks processing attempts (`success_count`, `error_count`)
- CSV report logs one row per file processed
- Detailed logging per file operation
-**No verification that expected ZIPs were actually created**
-**No ZIP content integrity validation**
- **No reconciliation of input count vs output count**

### Gap Scenarios (Files Can Be Silently Missed)
1. **Missing JPG files**: XML skipped with WARNING, no ZIP created, success_count unchanged
2. **Processing exceptions**: ERROR logged, no ZIP created, error_count increments but no verification
3. **ZIP creation failures**: TIFF/XML renamed but ZIP creation fails, success_count increments anyway
4. **Disk full mid-processing**: Some ZIPs created, later ones fail silently, partial success

### Solution: Comprehensive Validation System
Add post-processing validation that verifies:
- Expected number of ZIPs match actual ZIPs created
- Each ZIP contains correct structure (TIFF, XML, manifest.ini)
- Input XML count reconciles with output ZIP count
- Pre-flight checks prevent predictable failures

---

## Architecture Design

### Module Structure
Create new `src/validation.py` module with four primary functions:

```python
# src/validation.py

from pathlib import Path
from typing import NamedTuple, List
import zipfile
import shutil

class ValidationResult(NamedTuple):
    """Immutable validation result"""
    passed: bool
    expected_count: int
    actual_count: int
    valid_zips: int
    invalid_zips: List[str]
    missing_count: int
    errors: List[str]
    warnings: List[str]

class ReconciliationReport(NamedTuple):
    """Immutable reconciliation report"""
    input_xml_count: int
    csv_success_rows: int
    actual_zip_count: int
    valid_zip_count: int
    discrepancies: List[str]
    orphaned_files: List[str]

class PreFlightResult(NamedTuple):
    """Immutable pre-flight check result"""
    passed: bool
    disk_space_gb: float
    required_space_gb: float
    orphaned_tiff_count: int
    orphaned_xml_count: int
    warnings: List[str]
    blockers: List[str]
```

---

## Function Specifications

### 1. `verify_zip_contents(zip_path: Path) -> tuple[bool, list[str]]`

**Purpose**: Validate individual ZIP file structure and contents

**Logic**:
```python
def verify_zip_contents(zip_path: Path) -> tuple[bool, list[str]]:
    """
    Verify ZIP contains exactly 3 files: TIFF, XML, manifest.ini
    
    Returns:
        (is_valid, errors) tuple
    """
    errors = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            
            # Check file count
            if len(files) != 3:
                errors.append(f"Expected 3 files, found {len(files)}")
            
            # Check required files
            has_tiff = any(f.lower().endswith('.tif') or f.lower().endswith('.tiff') for f in files)
            has_xml = any(f.lower().endswith('.xml') for f in files)
            has_manifest = 'manifest.ini' in files
            
            if not has_tiff:
                errors.append("Missing TIFF file")
            if not has_xml:
                errors.append("Missing XML file")
            if not has_manifest:
                errors.append("Missing manifest.ini")
                
    except zipfile.BadZipFile:
        errors.append("Corrupted ZIP file")
    except Exception as e:
        errors.append(f"Unexpected error: {e}")
    
    return (len(errors) == 0, errors)
```

**Integration Point**: Called by `validate_batch_output()` for each ZIP

**Tests Required**:
- Valid ZIP with TIFF, XML, manifest.ini → `(True, [])`
- ZIP missing TIFF → `(False, ["Missing TIFF file"])`
- ZIP with 4 files → `(False, ["Expected 3 files, found 4"])`
- Corrupted ZIP → `(False, ["Corrupted ZIP file"])`

---

### 2. `validate_batch_output(photo_sets, output_dir, success_count, dry_run) -> ValidationResult`

**Purpose**: Post-processing validation of batch output

**Logic**:
```python
def validate_batch_output(
    photo_sets: List[PhotoSet],
    output_dir: Path,
    success_count: int,
    dry_run: bool
) -> ValidationResult:
    """
    Validate batch processing output matches expectations
    
    Returns:
        ValidationResult with pass/fail and detailed breakdown
    """
    errors = []
    warnings = []
    invalid_zips = []
    
    # Dry run should have no ZIPs
    if dry_run:
        actual_zips = list(output_dir.glob("*.zip"))
        if actual_zips:
            errors.append(f"Dry run created {len(actual_zips)} ZIPs (expected 0)")
        return ValidationResult(
            passed=len(errors) == 0,
            expected_count=0,
            actual_count=len(actual_zips),
            valid_zips=0,
            invalid_zips=[],
            missing_count=0,
            errors=errors,
            warnings=warnings
        )
    
    # Production: verify ZIP count and contents
    expected_count = success_count
    actual_zip_paths = list(output_dir.glob("*.zip"))
    actual_count = len(actual_zip_paths)
    
    # Check count mismatch
    if actual_count != expected_count:
        errors.append(
            f"ZIP count mismatch: expected {expected_count}, found {actual_count}"
        )
    
    # Verify each ZIP's contents
    valid_zips = 0
    for zip_path in actual_zip_paths:
        is_valid, zip_errors = verify_zip_contents(zip_path)
        if is_valid:
            valid_zips += 1
        else:
            invalid_zips.append(f"{zip_path.name}: {', '.join(zip_errors)}")
    
    # Calculate missing count
    missing_count = max(0, expected_count - valid_zips)
    
    passed = (len(errors) == 0 and len(invalid_zips) == 0)
    
    return ValidationResult(
        passed=passed,
        expected_count=expected_count,
        actual_count=actual_count,
        valid_zips=valid_zips,
        invalid_zips=invalid_zips,
        missing_count=missing_count,
        errors=errors,
        warnings=warnings
    )
```

**Integration Point**: End of `batch_process_with_safety_nets()`, line ~1069

**Tests Required**:
- Matching counts, all valid ZIPs → `passed=True`
- Fewer ZIPs than expected → `passed=False, missing_count > 0`
- More ZIPs than expected → `passed=False, errors contains mismatch`
- Invalid ZIP contents → `passed=False, invalid_zips not empty`
- Dry run with no ZIPs → `passed=True`
- Dry run with ZIPs created → `passed=False, errors contains dry run violation`

---

### 3. `generate_reconciliation_report(photo_sets, csv_path, output_dir) -> ReconciliationReport`

**Purpose**: Reconcile input count vs output count with detailed breakdown

**Logic**:
```python
def generate_reconciliation_report(
    photo_sets: List[PhotoSet],
    csv_path: Path,
    output_dir: Path
) -> ReconciliationReport:
    """
    Generate reconciliation report comparing input vs output
    
    Returns:
        ReconciliationReport with detailed breakdown
    """
    import csv
    
    # Count input XML files
    input_xml_count = sum(len(ps.xml_files) for ps in photo_sets)
    
    # Count CSV SUCCESS rows
    csv_success_rows = 0
    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_success_rows = sum(1 for row in reader if row.get('status') == 'SUCCESS')
    
    # Count actual ZIPs created
    actual_zip_count = len(list(output_dir.glob("*.zip")))
    
    # Validate each ZIP
    valid_zip_count = 0
    for zip_path in output_dir.glob("*.zip"):
        is_valid, _ = verify_zip_contents(zip_path)
        if is_valid:
            valid_zip_count += 1
    
    # Find orphaned files (TIFF/XML without corresponding ZIP)
    orphaned_files = []
    processed_tiffs = list(output_dir.glob("*_PROC.tif"))
    processed_xmls = list(output_dir.glob("*_PROC.xml"))
    
    for tiff in processed_tiffs:
        # Check if corresponding ZIP exists
        base_name = tiff.stem.replace('_PROC', '')
        zip_name = f"{base_name}.zip"
        if not (output_dir / zip_name).exists():
            orphaned_files.append(str(tiff))
    
    for xml in processed_xmls:
        base_name = xml.stem.replace('_PROC', '')
        zip_name = f"{base_name}.zip"
        if not (output_dir / zip_name).exists():
            orphaned_files.append(str(xml))
    
    # Identify discrepancies
    discrepancies = []
    if input_xml_count != csv_success_rows:
        discrepancies.append(
            f"Input XML count ({input_xml_count}) != CSV SUCCESS rows ({csv_success_rows})"
        )
    if csv_success_rows != actual_zip_count:
        discrepancies.append(
            f"CSV SUCCESS rows ({csv_success_rows}) != Actual ZIP count ({actual_zip_count})"
        )
    if actual_zip_count != valid_zip_count:
        discrepancies.append(
            f"Actual ZIP count ({actual_zip_count}) != Valid ZIP count ({valid_zip_count})"
        )
    
    return ReconciliationReport(
        input_xml_count=input_xml_count,
        csv_success_rows=csv_success_rows,
        actual_zip_count=actual_zip_count,
        valid_zip_count=valid_zip_count,
        discrepancies=discrepancies,
        orphaned_files=orphaned_files
    )
```

**Integration Point**: End of `batch_process_with_safety_nets()`, add to CSV summary

**Tests Required**:
- Perfect reconciliation → `discrepancies=[]`
- Missing ZIPs → `discrepancies contains count mismatch`
- Orphaned files → `orphaned_files not empty`
- Invalid ZIPs → `actual_zip_count != valid_zip_count`

---

### 4. `pre_flight_checks(photo_sets, output_dir) -> PreFlightResult`

**Purpose**: Validate environment before processing starts

**Logic**:
```python
def pre_flight_checks(
    photo_sets: List[PhotoSet],
    output_dir: Path
) -> PreFlightResult:
    """
    Perform pre-flight checks before batch processing
    
    Returns:
        PreFlightResult with pass/fail and warnings
    """
    warnings = []
    blockers = []
    
    # Check disk space
    stat = shutil.disk_usage(output_dir)
    disk_space_gb = stat.free / (1024**3)
    
    # Estimate required space (assume 10 MB per ZIP, conservative)
    total_files = sum(len(ps.xml_files) for ps in photo_sets)
    required_space_gb = (total_files * 10) / 1024  # MB to GB
    
    if disk_space_gb < required_space_gb:
        blockers.append(
            f"Insufficient disk space: {disk_space_gb:.2f} GB available, "
            f"{required_space_gb:.2f} GB required"
        )
    elif disk_space_gb < required_space_gb * 1.5:
        warnings.append(
            f"Low disk space: {disk_space_gb:.2f} GB available, "
            f"{required_space_gb:.2f} GB estimated"
        )
    
    # Check for orphaned files from previous runs
    orphaned_tiff = list(output_dir.glob("*_PROC.tif"))
    orphaned_xml = list(output_dir.glob("*_PROC.xml"))
    
    if orphaned_tiff or orphaned_xml:
        warnings.append(
            f"Found orphaned files: {len(orphaned_tiff)} TIFF, {len(orphaned_xml)} XML"
        )
    
    # Check write permissions
    try:
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        blockers.append(f"No write permission to output directory: {e}")
    
    passed = (len(blockers) == 0)
    
    return PreFlightResult(
        passed=passed,
        disk_space_gb=disk_space_gb,
        required_space_gb=required_space_gb,
        orphaned_tiff_count=len(orphaned_tiff),
        orphaned_xml_count=len(orphaned_xml),
        warnings=warnings,
        blockers=blockers
    )
```

**Integration Point**: Beginning of `batch_process_with_safety_nets()`, before processing starts

**Tests Required**:
- Sufficient disk space → `passed=True`
- Insufficient disk space → `passed=False, blockers contains disk space error`
- Orphaned files present → `warnings contains orphaned files`
- No write permission → `passed=False, blockers contains permission error`

---

## Integration into main.py

### Integration Points

#### 1. Pre-Flight Checks (Line ~1020, start of batch_process_with_safety_nets)
```python
def batch_process_with_safety_nets(
    photo_sets: List[PhotoSet],
    output_dir: Path,
    dry_run: bool = False
) -> None:
    """Process batches with safety nets and comprehensive validation"""
    
    from .validation import pre_flight_checks  # NEW
    
    # PRE-FLIGHT CHECKS (NEW)
    preflight = pre_flight_checks(photo_sets, output_dir)
    if not preflight.passed:
        for blocker in preflight.blockers:
            logging.error(f"Pre-flight check failed: {blocker}")
        raise RuntimeError("Pre-flight checks failed. Aborting batch processing.")
    
    for warning in preflight.warnings:
        logging.warning(f"Pre-flight warning: {warning}")
    
    # Existing code continues...
    success_count = 0
    error_count = 0
    # ... rest of processing loop ...
```

#### 2. Post-Processing Validation (Line ~1069, end of batch_process_with_safety_nets)
```python
    # ... existing processing loop completes ...
    
    # POST-PROCESSING VALIDATION (NEW)
    from .validation import validate_batch_output, generate_reconciliation_report
    
    validation_result = validate_batch_output(
        photo_sets=photo_sets,
        output_dir=output_dir,
        success_count=success_count,
        dry_run=dry_run
    )
    
    if not validation_result.passed:
        logging.error("Post-processing validation FAILED:")
        for error in validation_result.errors:
            logging.error(f"  - {error}")
        for invalid_zip in validation_result.invalid_zips:
            logging.error(f"  - Invalid ZIP: {invalid_zip}")
    else:
        logging.info(f"[PASS] Post-processing validation: {validation_result.valid_zips} valid ZIPs")
    
    # RECONCILIATION REPORT (NEW)
    if not dry_run:
        csv_path = output_dir / "batch_summary.csv"
        reconciliation = generate_reconciliation_report(
            photo_sets=photo_sets,
            csv_path=csv_path,
            output_dir=output_dir
        )
        
        logging.info("=== Reconciliation Report ===")
        logging.info(f"Input XML files: {reconciliation.input_xml_count}")
        logging.info(f"CSV SUCCESS rows: {reconciliation.csv_success_rows}")
        logging.info(f"Actual ZIP files: {reconciliation.actual_zip_count}")
        logging.info(f"Valid ZIP files: {reconciliation.valid_zip_count}")
        
        if reconciliation.discrepancies:
            logging.warning("Discrepancies found:")
            for discrepancy in reconciliation.discrepancies:
                logging.warning(f"  - {discrepancy}")
        
        if reconciliation.orphaned_files:
            logging.warning(f"Orphaned files found: {len(reconciliation.orphaned_files)}")
            for orphaned in reconciliation.orphaned_files[:5]:  # Limit to first 5
                logging.warning(f"  - {orphaned}")
    
    logging.info(f"Batch processing completed: {success_count} success, {error_count} errors")
```

---

## Testing Strategy

### Test File: `tests/test_validation.py`

Create comprehensive test coverage for all validation functions:

```python
# tests/test_validation.py

import pytest
from pathlib import Path
import zipfile
import tempfile
import shutil
from src.validation import (
    verify_zip_contents,
    validate_batch_output,
    generate_reconciliation_report,
    pre_flight_checks,
    ValidationResult,
    ReconciliationReport,
    PreFlightResult
)
from src.main import PhotoSet

class TestVerifyZipContents:
    """Test ZIP content verification"""
    
    def test_valid_zip_passes(self, tmp_path):
        """Valid ZIP with TIFF, XML, manifest.ini passes"""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("image.tiff", b"fake tiff data")
            zf.writestr("metadata.xml", b"<xml/>")
            zf.writestr("manifest.ini", b"[manifest]")
        
        is_valid, errors = verify_zip_contents(zip_path)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_tiff_fails(self, tmp_path):
        """ZIP missing TIFF file fails"""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("metadata.xml", b"<xml/>")
            zf.writestr("manifest.ini", b"[manifest]")
        
        is_valid, errors = verify_zip_contents(zip_path)
        assert is_valid is False
        assert "Missing TIFF file" in errors
    
    def test_wrong_file_count_fails(self, tmp_path):
        """ZIP with wrong number of files fails"""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("image.tiff", b"fake tiff data")
            zf.writestr("metadata.xml", b"<xml/>")
            zf.writestr("manifest.ini", b"[manifest]")
            zf.writestr("extra.txt", b"extra file")
        
        is_valid, errors = verify_zip_contents(zip_path)
        assert is_valid is False
        assert any("Expected 3 files" in e for e in errors)
    
    def test_corrupted_zip_fails(self, tmp_path):
        """Corrupted ZIP file fails gracefully"""
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_bytes(b"not a zip file")
        
        is_valid, errors = verify_zip_contents(zip_path)
        assert is_valid is False
        assert any("Corrupted" in e for e in errors)


class TestValidateBatchOutput:
    """Test batch output validation"""
    
    def test_matching_counts_passes(self, tmp_path):
        """Matching expected vs actual ZIP count passes"""
        # Create 3 valid ZIPs
        for i in range(3):
            zip_path = tmp_path / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f"image_{i}.tiff", b"fake tiff")
                zf.writestr(f"metadata_{i}.xml", b"<xml/>")
                zf.writestr("manifest.ini", b"[manifest]")
        
        photo_sets = []  # Not needed for this test
        result = validate_batch_output(photo_sets, tmp_path, success_count=3, dry_run=False)
        
        assert result.passed is True
        assert result.expected_count == 3
        assert result.actual_count == 3
        assert result.valid_zips == 3
        assert len(result.errors) == 0
    
    def test_missing_zips_fails(self, tmp_path):
        """Fewer ZIPs than expected fails"""
        # Create only 2 ZIPs but expect 3
        for i in range(2):
            zip_path = tmp_path / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f"image_{i}.tiff", b"fake tiff")
                zf.writestr(f"metadata_{i}.xml", b"<xml/>")
                zf.writestr("manifest.ini", b"[manifest]")
        
        result = validate_batch_output([], tmp_path, success_count=3, dry_run=False)
        
        assert result.passed is False
        assert result.expected_count == 3
        assert result.actual_count == 2
        assert result.missing_count == 1
        assert any("mismatch" in e.lower() for e in result.errors)
    
    def test_dry_run_no_zips_passes(self, tmp_path):
        """Dry run with no ZIPs created passes"""
        result = validate_batch_output([], tmp_path, success_count=0, dry_run=True)
        
        assert result.passed is True
        assert result.expected_count == 0
        assert result.actual_count == 0
    
    def test_dry_run_with_zips_fails(self, tmp_path):
        """Dry run with ZIPs created fails"""
        # Create a ZIP during dry run (shouldn't happen)
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("image.tiff", b"fake tiff")
            zf.writestr("metadata.xml", b"<xml/>")
            zf.writestr("manifest.ini", b"[manifest]")
        
        result = validate_batch_output([], tmp_path, success_count=0, dry_run=True)
        
        assert result.passed is False
        assert any("Dry run created" in e for e in result.errors)


class TestReconciliationReport:
    """Test reconciliation reporting"""
    
    def test_perfect_reconciliation(self, tmp_path):
        """Perfect reconciliation with matching counts"""
        # Create photo_sets with 2 XML files
        photo_sets = [
            PhotoSet(
                jpg_files=[Path("img1.jpg"), Path("img2.jpg")],
                xml_files=[Path("meta1.xml"), Path("meta2.xml")]
            )
        ]
        
        # Create CSV with 2 SUCCESS rows
        csv_path = tmp_path / "batch_summary.csv"
        csv_path.write_text("status\nSUCCESS\nSUCCESS\n")
        
        # Create 2 valid ZIPs
        for i in range(2):
            zip_path = tmp_path / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f"image_{i}.tiff", b"fake tiff")
                zf.writestr(f"metadata_{i}.xml", b"<xml/>")
                zf.writestr("manifest.ini", b"[manifest]")
        
        report = generate_reconciliation_report(photo_sets, csv_path, tmp_path)
        
        assert report.input_xml_count == 2
        assert report.csv_success_rows == 2
        assert report.actual_zip_count == 2
        assert report.valid_zip_count == 2
        assert len(report.discrepancies) == 0
    
    def test_discrepancy_detection(self, tmp_path):
        """Detects discrepancies in counts"""
        photo_sets = [
            PhotoSet(jpg_files=[Path("img1.jpg")], xml_files=[Path("meta1.xml")])
        ]
        
        # CSV shows 1 SUCCESS
        csv_path = tmp_path / "batch_summary.csv"
        csv_path.write_text("status\nSUCCESS\n")
        
        # But no ZIPs created
        
        report = generate_reconciliation_report(photo_sets, csv_path, tmp_path)
        
        assert report.input_xml_count == 1
        assert report.csv_success_rows == 1
        assert report.actual_zip_count == 0
        assert len(report.discrepancies) > 0
        assert any("CSV SUCCESS rows" in d and "Actual ZIP count" in d for d in report.discrepancies)


class TestPreFlightChecks:
    """Test pre-flight checks"""
    
    def test_sufficient_disk_space_passes(self, tmp_path):
        """Sufficient disk space passes pre-flight"""
        photo_sets = [
            PhotoSet(jpg_files=[Path("img1.jpg")], xml_files=[Path("meta1.xml")])
        ]
        
        result = pre_flight_checks(photo_sets, tmp_path)
        
        # Should pass (we have disk space in temp dir)
        assert result.passed is True
        assert result.disk_space_gb > 0
    
    def test_orphaned_files_warning(self, tmp_path):
        """Orphaned files trigger warning"""
        # Create orphaned files
        (tmp_path / "old_PROC.tif").write_bytes(b"fake tiff")
        (tmp_path / "old_PROC.xml").write_bytes(b"<xml/>")
        
        photo_sets = []
        result = pre_flight_checks(photo_sets, tmp_path)
        
        assert result.orphaned_tiff_count == 1
        assert result.orphaned_xml_count == 1
        assert any("orphaned" in w.lower() for w in result.warnings)
```

### Test Coverage Goals
- **Target**: 8-10 new validation tests
- **Total Test Count**: ~35 tests (current 25 + new 10)
- **Coverage**: All validation functions, all failure scenarios

### Regression Tests
Add to existing test files:
- **test_main.py**: Ensure validation doesn't break existing batch processing
- **test_batch_direct.py**: Validate integration with direct batch mode
- **test_core_safety.py**: Ensure validation respects dry_run mode

---

## CI/CD Integration

### Update `.github/workflows/ci.yml`

Add validation-specific test job:

```yaml
validation-tests:
  name: Validation Module Tests
  runs-on: windows-latest
  strategy:
    matrix:
      python-version: ["3.9", "3.11"]
  
  steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/requirements.txt
        pip install -r requirements/requirements-dev.txt
    
    - name: Run validation tests
      run: |
        pytest tests/test_validation.py -v --tb=short
    
    - name: Test pre-flight checks
      run: |
        python -c "from src.validation import pre_flight_checks; from pathlib import Path; result = pre_flight_checks([], Path('.')); print('[PASS] Pre-flight checks work correctly' if result else '[FAIL]')"
    
    - name: Test reconciliation logic
      run: |
        python -c "from src.validation import generate_reconciliation_report; from pathlib import Path; report = generate_reconciliation_report([], Path('nonexistent.csv'), Path('.')); print('[PASS] Reconciliation handles missing CSV' if report.csv_success_rows == 0 else '[FAIL]')"
```

---

## Documentation Updates

### 1. Update `docs/SYSTEM_FLOW.md` - Add Validation Architecture

Add new section after "Safety Nets and Error Handling":

```markdown
## Post-Processing Validation

### Architecture
The validation system runs AFTER batch processing completes to verify outputs match expectations.

**Validation Invariants**:
- `input_xml_count == csv_success_rows` (all files attempted were logged)
- `csv_success_rows == actual_zip_count` (all successes created ZIPs)
- `actual_zip_count == valid_zip_count` (all ZIPs are valid)

**Validation Functions**:
1. `verify_zip_contents()`: Validate individual ZIP structure (3 files: TIFF, XML, manifest.ini)
2. `validate_batch_output()`: Compare expected vs actual ZIP counts
3. `generate_reconciliation_report()`: Reconcile input vs output with discrepancy detection
4. `pre_flight_checks()`: Verify disk space, permissions, orphaned files before processing

### Guardrails
- Pre-flight checks BLOCK processing if critical issues found (disk space, permissions)
- Post-processing validation REPORTS discrepancies but doesn't fail the batch
- Dry run validation ensures NO ZIPs created during dry runs
- Validation respects existing data structures (PhotoSet, FilePair)
```

### 2. Update `docs/TEST_COVERAGE.md` - Add Validation Tests

```markdown
## Validation Tests (`tests/test_validation.py`)

### ZIP Content Verification
- `test_valid_zip_passes`: Valid ZIP with TIFF, XML, manifest.ini passes
- `test_missing_tiff_fails`: ZIP missing TIFF fails
- `test_wrong_file_count_fails`: ZIP with != 3 files fails
- `test_corrupted_zip_fails`: Corrupted ZIP handled gracefully

### Batch Output Validation
- `test_matching_counts_passes`: Expected == actual ZIP count passes
- `test_missing_zips_fails`: Fewer ZIPs than expected fails
- `test_dry_run_no_zips_passes`: Dry run with no ZIPs passes
- `test_dry_run_with_zips_fails`: Dry run with ZIPs created fails

### Reconciliation Reporting
- `test_perfect_reconciliation`: All counts match
- `test_discrepancy_detection`: Detects mismatched counts

### Pre-Flight Checks
- `test_sufficient_disk_space_passes`: Adequate space passes
- `test_orphaned_files_warning`: Orphaned files trigger warnings
```

### 3. Update `README.md` - Add Validation Features

```markdown
## Post-Processing Validation (New)

The script now includes comprehensive post-processing validation:

**Features**:
-  Verify expected ZIP count matches actual ZIP count
-  Validate ZIP contents (TIFF, XML, manifest.ini)
-  Reconciliation report (input vs output counts)
-  Pre-flight checks (disk space, permissions, orphaned files)

**Validation Reports**:
```
=== Reconciliation Report ===
Input XML files: 25
CSV SUCCESS rows: 25
Actual ZIP files: 25
Valid ZIP files: 25
No discrepancies found.
```

**Pre-Flight Checks**:
- Disk space validation (blocks if insufficient)
- Orphaned file detection (warns if found)
- Write permission verification (blocks if denied)
```

---

## Safe Integration Strategy

### Phase 1: Non-Blocking Warnings (Current Branch)
- Implement validation functions
- Integration runs validation but only logs warnings
- No blocking behavior (existing scripts still work)
- User can review validation output

### Phase 2: Opt-In Strict Mode (Future)
Add `--strict-validation` flag:
```python
if args.strict_validation:
    if not validation_result.passed:
        raise RuntimeError("Validation failed in strict mode")
```

### Phase 3: Gradual Rollout
1. **Week 1**: Deploy with warnings only, monitor real data validation
2. **Week 2**: Enable strict mode for test runs (X:\Cetamura\1990\1990)
3. **Week 3**: Enable strict mode for production if no issues found

---

## Backward Compatibility Guarantees

### Non-Breaking Changes
-  Validation runs AFTER processing (doesn't affect processing loop)
-  Validation failures don't raise exceptions (only log warnings)
-  Dry run behavior unchanged (validation just confirms no ZIPs created)
-  Existing data structures unchanged (PhotoSet, FilePair, BatchContext)
-  CSV report format unchanged (validation adds to logs, not CSV)

### Integration Points
- Pre-flight checks run before processing loop (can block)
- Post-processing validation runs after processing loop (only warns)
- Reconciliation report adds to logging output (doesn't modify CSV)

---

## Implementation Checklist

### Development
- [ ] Create `src/validation.py` with NamedTuples
- [ ] Implement `verify_zip_contents()`
- [ ] Implement `validate_batch_output()`
- [ ] Implement `generate_reconciliation_report()`
- [ ] Implement `pre_flight_checks()`
- [ ] Integrate into `batch_process_with_safety_nets()`

### Testing
- [ ] Create `tests/test_validation.py`
- [ ] Add ZIP verification tests (4 tests)
- [ ] Add batch validation tests (4 tests)
- [ ] Add reconciliation tests (2 tests)
- [ ] Add pre-flight tests (2 tests)
- [ ] Run all existing tests (ensure no regression)

### CI/CD
- [ ] Add validation-tests job to `.github/workflows/ci.yml`
- [ ] Add pre-flight check verification
- [ ] Add reconciliation logic test

### Documentation
- [ ] Update `docs/SYSTEM_FLOW.md` with validation architecture
- [ ] Update `docs/TEST_COVERAGE.md` with validation tests
- [ ] Update `README.md` with validation features
- [ ] Add inline docstrings to validation functions

### Validation
- [ ] Test against real data (X:\Cetamura\1990\1990)
- [ ] Verify dry run still works correctly
- [ ] Verify no regression in existing functionality
- [ ] Confirm validation catches missing ZIPs
- [ ] Confirm validation catches corrupted ZIPs

---

## Success Criteria

### Functional Requirements
-  Pre-flight checks detect disk space issues
-  Post-processing validation detects missing ZIPs
-  ZIP content verification detects corrupted ZIPs
-  Reconciliation report identifies discrepancies
-  Validation respects dry run mode

### Non-Functional Requirements
-  No breaking changes to existing functionality
-  Validation adds < 5% overhead to processing time
-  Test coverage > 90% for validation module
-  CI pipeline validates all validation functions
-  Documentation complete and accurate

### User Experience
-  Clear validation output in logs
-  Reconciliation report easy to understand
-  Pre-flight warnings actionable (tell user what to fix)
-  Validation failures don't stop processing (warnings only)

---

## Risk Mitigation

### Risk 1: Validation Breaks Existing Scripts
**Mitigation**: 
- Validation runs in non-blocking mode (warnings only)
- Comprehensive regression testing
- Feature branch for isolated development

### Risk 2: False Positives in Validation
**Mitigation**:
- Handle legitimate WARNING cases (missing JPG)
- Reconciliation accepts `csv_success_rows <= input_xml_count`
- Orphaned files are warnings, not blockers

### Risk 3: Performance Overhead
**Mitigation**:
- Validation runs AFTER processing (doesn't slow core loop)
- ZIP verification is fast (just check file count and names)
- Pre-flight checks run once (not per file)

### Risk 4: CI Failures Due to Encoding
**Mitigation**:
- Use ASCII-only output in validation ([PASS], [FAIL])
- Test validation output on Windows CI runners
- Avoid Unicode characters in validation messages

---

## Next Steps

1. **Mark Plan as In-Progress**  (You are here)
2. **Implement Validation Module** → Create `src/validation.py`
3. **Add Validation Tests** → Create `tests/test_validation.py`
4. **Integrate into Main** → Update `batch_process_with_safety_nets()`
5. **Update CI Pipeline** → Add validation-tests job
6. **Update Documentation** → SYSTEM_FLOW.md, TEST_COVERAGE.md, README.md
7. **Test Against Real Data** → X:\Cetamura\1990\1990 dry run
8. **Review and Merge** → Create PR for review

---

**End of Plan**

"""
Post-Processing Validation Module

This module provides comprehensive validation functions for the Cetamura batch processing script.
It addresses critical gaps in output verification while maintaining backward compatibility.

Functions:
    - verify_zip_contents(): Validate individual ZIP file structure
    - validate_batch_output(): Post-processing validation of batch output
    - generate_reconciliation_report(): Reconcile input vs output counts
    - pre_flight_checks(): Environment validation before processing starts

Data Structures:
    - ValidationResult: Immutable validation result
    - ReconciliationReport: Immutable reconciliation report
    - PreFlightResult: Immutable pre-flight check result
"""

from pathlib import Path
from typing import NamedTuple, List
import zipfile
import shutil
import logging
import csv


class ValidationResult(NamedTuple):
    """Immutable validation result from batch output validation"""
    passed: bool
    expected_count: int
    actual_count: int
    valid_zips: int
    invalid_zips: List[str]
    missing_count: int
    errors: List[str]
    warnings: List[str]


class ReconciliationReport(NamedTuple):
    """Immutable reconciliation report comparing input vs output"""
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


def verify_zip_contents(zip_path: Path) -> tuple[bool, list[str]]:
    """
    Verify ZIP contains exactly 3 files: TIFF, XML, manifest.ini
    
    Args:
        zip_path: Path to ZIP file to validate
    
    Returns:
        Tuple of (is_valid, errors) where:
            - is_valid: True if ZIP structure is valid
            - errors: List of error messages (empty if valid)
    
    Example:
        >>> is_valid, errors = verify_zip_contents(Path("output.zip"))
        >>> if is_valid:
        ...     print("ZIP is valid")
        ... else:
        ...     for error in errors:
        ...         print(f"Error: {error}")
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
            has_manifest = any(f.lower() == 'manifest.ini' for f in files)
            
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


def validate_batch_output(
    photo_sets: List,
    output_dir: Path,
    success_count: int,
    dry_run: bool
) -> ValidationResult:
    """
    Validate batch processing output matches expectations
    
    This function performs post-processing validation to ensure:
    - Expected number of ZIPs match actual ZIPs created
    - Each ZIP contains correct structure (TIFF, XML, manifest.ini)
    - Dry run mode created no files
    
    Args:
        photo_sets: List of PhotoSet objects processed
        output_dir: Directory containing output ZIPs
        success_count: Number of successful file processings
        dry_run: Whether this was a dry run (should have no ZIPs)
    
    Returns:
        ValidationResult with detailed validation outcome
    
    Example:
        >>> result = validate_batch_output(photo_sets, output_dir, 25, False)
        >>> if result.passed:
        ...     print(f"Validation passed: {result.valid_zips} valid ZIPs")
        ... else:
        ...     for error in result.errors:
        ...         print(f"Error: {error}")
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


def generate_reconciliation_report(
    photo_sets: List,
    csv_path: Path,
    output_dir: Path
) -> ReconciliationReport:
    """
    Generate reconciliation report comparing input vs output
    
    This function reconciles:
    - Input XML file count
    - CSV SUCCESS row count
    - Actual ZIP file count
    - Valid ZIP file count
    
    And identifies:
    - Discrepancies between counts
    - Orphaned files (TIFF/XML without corresponding ZIP)
    
    Args:
        photo_sets: List of PhotoSet objects processed
        csv_path: Path to CSV summary file
        output_dir: Directory containing output files
    
    Returns:
        ReconciliationReport with detailed breakdown
    
    Example:
        >>> report = generate_reconciliation_report(photo_sets, csv_path, output_dir)
        >>> print(f"Input: {report.input_xml_count}, Output: {report.valid_zip_count}")
        >>> for discrepancy in report.discrepancies:
        ...     print(f"Discrepancy: {discrepancy}")
    """
    # Count input XML files
    input_xml_count = sum(len(ps.xml_files) for ps in photo_sets)
    
    # Count CSV SUCCESS rows
    csv_success_rows = 0
    if csv_path.exists():
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                csv_success_rows = sum(1 for row in reader if row.get('Status') == 'SUCCESS')
        except Exception as e:
            logging.warning(f"Could not read CSV file: {e}")
    
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


def pre_flight_checks(
    photo_sets: List,
    output_dir: Path
) -> PreFlightResult:
    """
    Perform pre-flight checks before batch processing
    
    This function validates:
    - Sufficient disk space available
    - Write permissions to output directory
    - Identifies orphaned files from previous runs
    
    Args:
        photo_sets: List of PhotoSet objects to process
        output_dir: Directory where output will be written
    
    Returns:
        PreFlightResult with pass/fail and warnings/blockers
    
    Example:
        >>> result = pre_flight_checks(photo_sets, output_dir)
        >>> if not result.passed:
        ...     for blocker in result.blockers:
        ...         print(f"BLOCKER: {blocker}")
        ...     raise RuntimeError("Pre-flight checks failed")
        >>> for warning in result.warnings:
        ...     print(f"WARNING: {warning}")
    """
    warnings = []
    blockers = []
    
    # Check disk space
    try:
        stat = shutil.disk_usage(output_dir)
        disk_space_gb = stat.free / (1024**3)
    except Exception as e:
        blockers.append(f"Cannot check disk space: {e}")
        disk_space_gb = 0.0
    
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

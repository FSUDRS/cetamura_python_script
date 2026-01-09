"""
Comprehensive tests for the validation module

Tests cover:
- ZIP content verification (valid/invalid ZIPs)
- Batch output validation (matching/mismatched counts)
- Reconciliation reporting (discrepancy detection)
- Pre-flight checks (disk space, orphaned files)
"""

import pytest
from pathlib import Path
import zipfile
import tempfile
import shutil
import csv
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
    
    def test_valid_zip_with_tif_extension(self, tmp_path):
        """Valid ZIP with .tif extension (not .tiff) passes"""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("image.tif", b"fake tiff data")
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
    
    def test_missing_xml_fails(self, tmp_path):
        """ZIP missing XML file fails"""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("image.tiff", b"fake tiff data")
            zf.writestr("manifest.ini", b"[manifest]")
        
        is_valid, errors = verify_zip_contents(zip_path)
        assert is_valid is False
        assert "Missing XML file" in errors
    
    def test_missing_manifest_fails(self, tmp_path):
        """ZIP missing manifest.ini fails"""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("image.tiff", b"fake tiff data")
            zf.writestr("metadata.xml", b"<xml/>")
        
        is_valid, errors = verify_zip_contents(zip_path)
        assert is_valid is False
        assert "Missing manifest.ini" in errors
    
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
    
    def test_too_few_files_fails(self, tmp_path):
        """ZIP with too few files fails"""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("image.tiff", b"fake tiff data")
        
        is_valid, errors = verify_zip_contents(zip_path)
        assert is_valid is False
        assert any("Expected 3 files" in e for e in errors)
        assert "Missing XML file" in errors
        assert "Missing manifest.ini" in errors
    
    def test_corrupted_zip_fails(self, tmp_path):
        """Corrupted ZIP file fails gracefully"""
        zip_path = tmp_path / "corrupted.zip"
        zip_path.write_bytes(b"not a zip file")
        
        is_valid, errors = verify_zip_contents(zip_path)
        assert is_valid is False
        assert any("Corrupted" in e for e in errors)
    
    def test_empty_zip_fails(self, tmp_path):
        """Empty ZIP file fails"""
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass  # Create empty ZIP
        
        is_valid, errors = verify_zip_contents(zip_path)
        assert is_valid is False
        assert any("Expected 3 files, found 0" in e for e in errors)


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
    
    def test_extra_zips_fails(self, tmp_path):
        """More ZIPs than expected fails"""
        # Create 4 ZIPs but expect only 2
        for i in range(4):
            zip_path = tmp_path / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f"image_{i}.tiff", b"fake tiff")
                zf.writestr(f"metadata_{i}.xml", b"<xml/>")
                zf.writestr("manifest.ini", b"[manifest]")
        
        result = validate_batch_output([], tmp_path, success_count=2, dry_run=False)
        
        assert result.passed is False
        assert result.expected_count == 2
        assert result.actual_count == 4
        assert any("mismatch" in e.lower() for e in result.errors)
    
    def test_invalid_zip_contents_fails(self, tmp_path):
        """Invalid ZIP contents cause validation to fail"""
        # Create 2 valid ZIPs and 1 invalid
        for i in range(2):
            zip_path = tmp_path / f"test_{i}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr(f"image_{i}.tiff", b"fake tiff")
                zf.writestr(f"metadata_{i}.xml", b"<xml/>")
                zf.writestr("manifest.ini", b"[manifest]")
        
        # Invalid ZIP (missing TIFF)
        zip_path = tmp_path / "test_invalid.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("metadata.xml", b"<xml/>")
            zf.writestr("manifest.ini", b"[manifest]")
        
        result = validate_batch_output([], tmp_path, success_count=3, dry_run=False)
        
        assert result.passed is False
        assert result.valid_zips == 2
        assert len(result.invalid_zips) == 1
        assert any("test_invalid.zip" in iz for iz in result.invalid_zips)
    
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
    
    def test_zero_success_count_passes(self, tmp_path):
        """Zero expected ZIPs with no actual ZIPs passes"""
        result = validate_batch_output([], tmp_path, success_count=0, dry_run=False)
        
        assert result.passed is True
        assert result.expected_count == 0
        assert result.actual_count == 0
        assert result.valid_zips == 0


class TestReconciliationReport:
    """Test reconciliation reporting"""
    
    def test_perfect_reconciliation(self, tmp_path):
        """Perfect reconciliation with matching counts"""
        # Create photo_sets with 2 XML files
        photo_sets = [
            PhotoSet(
                base_directory=tmp_path,
                image_files=[Path("img1.jpg"), Path("img2.jpg")],
                xml_files=[Path("meta1.xml"), Path("meta2.xml")],
                manifest_file=Path("manifest.txt"),
                structure_type='standard'
            )
        ]
        
        # Create CSV with 2 SUCCESS rows
        csv_path = tmp_path / "batch_summary.csv"
        csv_path.write_text("Status\nSUCCESS\nSUCCESS\n")
        
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
    
    def test_discrepancy_detection_missing_zips(self, tmp_path):
        """Detects discrepancies when ZIPs are missing"""
        photo_sets = [
            PhotoSet(
                base_directory=tmp_path,
                image_files=[Path("img1.jpg")],
                xml_files=[Path("meta1.xml")],
                manifest_file=Path("manifest.txt"),
                structure_type='standard'
            )
        ]
        
        # CSV shows 1 SUCCESS
        csv_path = tmp_path / "batch_summary.csv"
        csv_path.write_text("Status\nSUCCESS\n")
        
        # But no ZIPs created (output directory is empty)
        
        report = generate_reconciliation_report(photo_sets, csv_path, tmp_path)
        
        assert report.input_xml_count == 1
        assert report.csv_success_rows == 1
        assert report.actual_zip_count == 0
        assert len(report.discrepancies) > 0
        assert any("CSV SUCCESS rows" in d and "Actual ZIP count" in d for d in report.discrepancies)
    
    def test_discrepancy_detection_invalid_zips(self, tmp_path):
        """Detects discrepancies when ZIPs are invalid"""
        photo_sets = [
            PhotoSet(
                base_directory=tmp_path,
                image_files=[Path("img1.jpg"), Path("img2.jpg")],
                xml_files=[Path("meta1.xml"), Path("meta2.xml")],
                manifest_file=Path("manifest.txt"),
                structure_type='standard'
            )
        ]
        
        csv_path = tmp_path / "batch_summary.csv"
        csv_path.write_text("Status\nSUCCESS\nSUCCESS\n")
        
        # Create 1 valid ZIP and 1 invalid ZIP
        zip_path = tmp_path / "test_0.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("image.tiff", b"fake tiff")
            zf.writestr("metadata.xml", b"<xml/>")
            zf.writestr("manifest.ini", b"[manifest]")
        
        # Invalid ZIP (missing TIFF)
        zip_path = tmp_path / "test_1.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("metadata.xml", b"<xml/>")
            zf.writestr("manifest.ini", b"[manifest]")
        
        report = generate_reconciliation_report(photo_sets, csv_path, tmp_path)
        
        assert report.actual_zip_count == 2
        assert report.valid_zip_count == 1
        assert any("Actual ZIP count" in d and "Valid ZIP count" in d for d in report.discrepancies)
    
    def test_orphaned_files_detection(self, tmp_path):
        """Detects orphaned _PROC files without corresponding ZIPs"""
        photo_sets = []
        csv_path = tmp_path / "batch_summary.csv"
        csv_path.write_text("status\n")
        
        # Create orphaned files
        (tmp_path / "file1_PROC.tif").write_bytes(b"fake tiff")
        (tmp_path / "file2_PROC.xml").write_bytes(b"<xml/>")
        
        # No ZIPs created
        
        report = generate_reconciliation_report(photo_sets, csv_path, tmp_path)
        
        assert len(report.orphaned_files) == 2
        assert any("file1_PROC.tif" in of for of in report.orphaned_files)
        assert any("file2_PROC.xml" in of for of in report.orphaned_files)
    
    def test_missing_csv_file(self, tmp_path):
        """Handles missing CSV file gracefully"""
        photo_sets = [
            PhotoSet(
                base_directory=tmp_path,
                image_files=[Path("img1.jpg")],
                xml_files=[Path("meta1.xml")],
                manifest_file=Path("manifest.txt"),
                structure_type='standard'
            )
        ]
        
        csv_path = tmp_path / "nonexistent.csv"
        
        report = generate_reconciliation_report(photo_sets, csv_path, tmp_path)
        
        assert report.input_xml_count == 1
        assert report.csv_success_rows == 0  # CSV doesn't exist
        assert report.actual_zip_count == 0


class TestPreFlightChecks:
    """Test pre-flight checks"""
    
    def test_sufficient_disk_space_passes(self, tmp_path):
        """Sufficient disk space passes pre-flight"""
        photo_sets = [
            PhotoSet(
                base_directory=tmp_path,
                image_files=[Path("img1.jpg")],
                xml_files=[Path("meta1.xml")],
                manifest_file=Path("manifest.txt"),
                structure_type='standard'
            )
        ]
        
        result = pre_flight_checks(photo_sets, tmp_path)
        
        # Should pass (we have disk space in temp dir)
        assert result.passed is True
        assert result.disk_space_gb > 0
        assert result.required_space_gb >= 0
    
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
    
    def test_multiple_orphaned_files(self, tmp_path):
        """Multiple orphaned files are counted correctly"""
        # Create multiple orphaned files
        (tmp_path / "file1_PROC.tif").write_bytes(b"fake tiff")
        (tmp_path / "file2_PROC.tif").write_bytes(b"fake tiff")
        (tmp_path / "file3_PROC.tif").write_bytes(b"fake tiff")
        (tmp_path / "file1_PROC.xml").write_bytes(b"<xml/>")
        (tmp_path / "file2_PROC.xml").write_bytes(b"<xml/>")
        
        photo_sets = []
        result = pre_flight_checks(photo_sets, tmp_path)
        
        assert result.orphaned_tiff_count == 3
        assert result.orphaned_xml_count == 2
        assert any("3 TIFF" in w for w in result.warnings)
        assert any("2 XML" in w for w in result.warnings)
    
    def test_write_permission_check(self, tmp_path):
        """Write permission is validated"""
        photo_sets = []
        
        result = pre_flight_checks(photo_sets, tmp_path)
        
        # Should have write permission to tmp_path
        assert result.passed is True
        assert len(result.blockers) == 0
    
    def test_no_orphaned_files_no_warning(self, tmp_path):
        """No orphaned files means no warnings"""
        photo_sets = []
        
        result = pre_flight_checks(photo_sets, tmp_path)
        
        assert result.orphaned_tiff_count == 0
        assert result.orphaned_xml_count == 0
        # Should either have no warnings or warnings not about orphaned files
        orphan_warnings = [w for w in result.warnings if "orphaned" in w.lower()]
        assert len(orphan_warnings) == 0
    
    def test_large_batch_disk_space_estimation(self, tmp_path):
        """Large batch estimates disk space correctly"""
        # Create photo sets with many files
        photo_sets = [
            PhotoSet(
                base_directory=tmp_path,
                image_files=[Path(f"img{i}.jpg") for i in range(100)],
                xml_files=[Path(f"meta{i}.xml") for i in range(100)],
                manifest_file=Path("manifest.txt"),
                structure_type='standard'
            )
        ]
        
        result = pre_flight_checks(photo_sets, tmp_path)
        
        # Should estimate space for 100 files
        # 100 files * 10 MB / 1024 = ~0.98 GB
        assert result.required_space_gb > 0.9
        assert result.required_space_gb < 1.0

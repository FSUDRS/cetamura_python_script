import pytest
import shutil
import os
from pathlib import Path
from src.main import batch_process_with_safety_nets
import zipfile

# Determine test environment paths
TEST_ROOT = Path("test_sandbox")
SRC_DIR = Path("src")

@pytest.fixture
def setup_sandbox(tmp_path):
    """
    Creates a sandbox environment for testing Global Recovery.
    Structure:
    - root/
        - folder_a/
            - target.xml (IID: TEST_IID_001)
            - MANIFEST.ini
        - folder_b/
            - TEST_IID_001.jpg (Physically separated from XML)
    """
    root = tmp_path / "global_recovery_test"
    root.mkdir()
    
    folder_a = root / "folder_a"
    folder_a.mkdir()
    
    folder_b = root / "folder_b"
    folder_b.mkdir()
    
    # Create XML in Folder A
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<mods xmlns="http://www.loc.gov/mods/v3">
    <identifier type="IID">TEST_IID_001</identifier>
</mods>"""
    (folder_a / "TEST_IID_001.xml").write_text(xml_content)
    (folder_a / "MANIFEST.ini").write_text("[Manifest]\nKey=Value")
    
    # Create Image in Folder B (The "Misplaced" File)
    # We create a valid small JPEG to pass validation
    from PIL import Image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(folder_b / "TEST_IID_001.jpg")
    
    return root

def test_global_recovery_strategy(setup_sandbox):
    """
    Test that batch_process_with_safety_nets correctly finds an image
    that is located in a different directory than its XML.
    """
    root_dir = setup_sandbox
    
    # Run the batch process
    # We expect it to find the XML in folder_a, fail local lookup,
    # then use global index to find the JPG in folder_b.
    batch_process_with_safety_nets(str(root_dir), dry_run=False, staging=False)
    
    # Validation
    # The script was run against root_dir, so output sits in root_dir/output
    output_dir = root_dir / "output"
    
    # 1. Check if output directory was created
    assert output_dir.exists(), f"Output directory should be created at {output_dir}"
    
    # 2. Check if ZIP was created
    expected_zip = output_dir / "TEST_IID_001.zip"
    assert expected_zip.exists(), "ZIP file should be created despite cross-folder separation"
    
    # 3. Check ZIP content
    with zipfile.ZipFile(expected_zip, 'r') as z:
        filenames = z.namelist()
        assert "TEST_IID_001.tiff" in filenames, "ZIP should contain the converted TIFF"
        assert "TEST_IID_001.xml" in filenames, "ZIP should contain the XML"
        assert "MANIFEST.ini" in filenames, "ZIP should contain the Manifest"

def test_global_recovery_reporting(setup_sandbox):
    """
    Test that the CSV report correctly logs the CROSS_LINK warning.
    """
    root_dir = setup_sandbox
    batch_process_with_safety_nets(str(root_dir), dry_run=False, staging=False)
    
    # Find the report csv in root_dir/output
    output_dir = root_dir / "output"
    csv_files = list(output_dir.glob("batch_report_*.csv"))
    assert len(csv_files) > 0, "CSV Report should be generated"
    
    report_content = csv_files[0].read_text()
    
    # We expect "CROSS_LINK" status in the CSV
    assert "CROSS_LINK" in report_content, "Report should log 'CROSS_LINK' warning"
    assert "folder_b" in report_content, "Report should mention the source folder of the recovered image"

"""
Tests for the core functions in main.py
Focused on functions actually used by the GUI application
"""
import pytest
from pathlib import Path
from PIL import Image
from src.main import (
    find_photo_sets,
    convert_jpg_to_tiff,
    rename_files,
    package_to_zip,
    extract_iid_from_xml,
    sanitize_name,
)

@pytest.fixture
def setup_test_directory(tmp_path):
    """Setup temporary directory structure for testing find_photo_sets."""
    valid_dir = tmp_path / "valid_set"
    valid_dir.mkdir()
    
    # Create JPG file
    jpg_file = valid_dir / "test.jpg"
    jpg_file.touch()
    
    # Create XML file
    xml_file = valid_dir / "test.xml"
    xml_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
    <mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
        <mods:identifier type="IID">FSU_Cetamura_photos_20060523_46N3W_001</mods:identifier>
    </mods:mods>""")
    
    # Create INI file
    ini_file = valid_dir / "manifest.ini"
    ini_file.touch()
    
    return tmp_path

def test_find_photo_sets(setup_test_directory):
    """Test that find_photo_sets identifies valid directory sets."""
    result = find_photo_sets(str(setup_test_directory))
    assert len(result) == 1
    directory, jpg_files, xml_files, ini_files = result[0]
    assert str(directory) == str(setup_test_directory / "valid_set")

def test_convert_jpg_to_tiff(tmp_path):
    """Test JPG to TIFF conversion."""
    # Create a small test JPG image
    jpg_path = tmp_path / "test.jpg"
    image = Image.new('RGB', (10, 10), color='red')
    image.save(jpg_path, 'JPEG')
    
    result = convert_jpg_to_tiff(jpg_path)
    assert result is not None
    assert result.suffix == '.tiff'
    assert result.exists()

def test_extract_iid_from_xml_namespaced(tmp_path):
    """Test IID extraction from namespaced XML."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
        <mods:identifier type="IID">FSU_Cetamura_photos_20060523_46N3W_001</mods:identifier>
    </mods:mods>"""
    
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content)
    
    result = extract_iid_from_xml(xml_file)
    assert result == "FSU_Cetamura_photos_20060523_46N3W_001"

def test_extract_iid_from_xml_non_namespaced(tmp_path):
    """Test IID extraction from non-namespaced XML."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <mods>
        <identifier type="IID">FSU_Cetamura_photos_20060523_46N3W_002</identifier>
    </mods>"""
    
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content)
    
    result = extract_iid_from_xml(xml_file)
    assert result == "FSU_Cetamura_photos_20060523_46N3W_002"

def test_sanitize_name():
    """Test sanitize_name function."""
    invalid_name = "test<>:\"/\\|?*name"
    sanitized = sanitize_name(invalid_name)
    assert sanitized == "test_name"

@pytest.mark.parametrize("input_name,expected_name", [
    ("normal_name", "normal_name"),
    ("name with spaces", "name_with_spaces"),
    ("name<>with:invalid/chars", "name_with_invalid_chars"),
])
def test_sanitize_name_cases(input_name, expected_name):
    assert sanitize_name(input_name) == expected_name

def test_rename_files(tmp_path):
    """Test file renaming functionality."""
    # Setup
    tiff_file = tmp_path / "original.tiff"
    xml_file = tmp_path / "original.xml"
    tiff_file.touch()
    xml_file.touch()
    
    iid = "FSU_Cetamura_photos_20060523_46N3W_001"
    
    # Execute
    new_tiff, new_xml = rename_files(tmp_path, tiff_file, xml_file, iid)
    
    # Verify
    assert new_tiff.name == f"{iid}.tiff"
    assert new_xml.name == f"{iid}.xml"
    assert new_tiff.exists()
    assert new_xml.exists()
    assert not tiff_file.exists()  # Original should be moved
    assert not xml_file.exists()   # Original should be moved

def test_package_to_zip(tmp_path):
    """Test zip packaging functionality."""
    # Setup files
    tiff_file = tmp_path / "test.tiff"
    xml_file = tmp_path / "test.xml"
    manifest_file = tmp_path / "MANIFEST.ini"
    output_folder = tmp_path / "output"
    output_folder.mkdir()
    
    # Create test files
    tiff_file.write_text("fake tiff content")
    xml_file.write_text("fake xml content")
    manifest_file.write_text("fake manifest content")
    
    # Execute
    zip_path = package_to_zip(tiff_file, xml_file, manifest_file, output_folder)
    
    # Verify
    assert zip_path.exists()
    assert zip_path.suffix == '.zip'
    
    # Verify zip contents
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        names = zip_file.namelist()
        assert any(name.endswith('.tiff') for name in names)
        assert any(name.endswith('.xml') for name in names)
        assert any(name.endswith('.ini') for name in names)


def test_full_workflow(tmp_path):
    """Integration test for complete workflow without update_manifest"""
    # Setup files
    tiff_file = tmp_path / "original.tiff"
    xml_file = tmp_path / "original.xml"
    manifest_path = tmp_path / "MANIFEST.ini"
    tiff_file.touch()
    xml_file.touch()
    
    # Create manifest
    import configparser
    config = configparser.ConfigParser()
    config.write(manifest_path.open('w'))
    
    # Execute workflow
    base_name = "FSU_Cetamura_photos_20060523_46N3W_001"
    
    new_tiff, new_xml = rename_files(tmp_path, tiff_file, xml_file, base_name)
    output_zip = package_to_zip(new_tiff, new_xml, manifest_path, tmp_path)
    
    # Verify complete state
    assert new_tiff.exists()
    assert new_xml.exists()
    assert manifest_path.exists()
    assert output_zip.exists()
    assert output_zip.suffix == '.zip'

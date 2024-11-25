import pytest
from pathlib import Path
from PIL import Image
import zipfile
import configparser
from src.utils import (
    find_photo_sets,
    convert_jpg_to_tiff,
    update_manifest,
    rename_files,
    package_to_zip,
    extract_iid_from_xml,
    sanitize_filename,
)

@pytest.fixture
def setup_test_directory(tmp_path):
    """Setup temporary directory structure for testing find_photo_sets."""
    valid_dir = tmp_path / "valid_set"
    valid_dir.mkdir()
    (valid_dir / "photo.jpg").touch()
    (valid_dir / "metadata.xml").write_text(
        """<mods:root xmlns:mods="http://www.loc.gov/mods/v3">
               <mods:identifier type="IID">unique-id-123</mods:identifier>
           </mods:root>"""
    )
    (valid_dir / "manifest.ini").touch()

    incomplete_dir = tmp_path / "incomplete_set"
    incomplete_dir.mkdir()
    (incomplete_dir / "photo.jpg").touch()

    return tmp_path


def test_find_photo_sets(setup_test_directory):
    """Test finding valid photo sets in a directory."""
    photo_sets = find_photo_sets(setup_test_directory)
    assert len(photo_sets) == 1, "Expected 1 valid photo set"
    valid_dir = str(setup_test_directory / "valid_set")
    detected_dirs = [str(photo_set[0]) for photo_set in photo_sets]
    assert valid_dir in detected_dirs, f"Expected {valid_dir} to be detected as a valid photo set"


def test_convert_jpg_to_tiff(tmp_path):
    """Test converting a .jpg file to .tiff with actual image data."""
    jpg_path = tmp_path / "photo.jpg"
    Image.new("RGB", (10, 10)).save(jpg_path, "JPEG")
    tiff_path = convert_jpg_to_tiff(jpg_path)
    assert tiff_path.exists(), "Converted TIFF file should exist"
    assert not jpg_path.exists(), "Original JPG file should be deleted"


def test_extract_iid_from_xml_namespaced(tmp_path):
    """Test extracting the IID from a namespaced XML file."""
    xml_file = tmp_path / "metadata.xml"
    xml_file.write_text(
        """<mods:root xmlns:mods="http://www.loc.gov/mods/v3">
               <mods:identifier type="IID">unique-id-123</mods:identifier>
           </mods:root>"""
    )
    iid = extract_iid_from_xml(xml_file)
    assert iid == "unique-id-123", "IID should match the content of the <identifier> tag"


def test_extract_iid_from_xml_non_namespaced(tmp_path):
    """Test extracting the IID from a non-namespaced XML file."""
    xml_file = tmp_path / "metadata.xml"
    xml_file.write_text(
        """<root>
           <identifier type="IID">unique-id-456</identifier>
        </root>"""
    )
    iid = extract_iid_from_xml(xml_file)
    assert iid == "unique-id-456", "IID should match the content of the <identifier> tag"


def test_update_manifest(tmp_path):
    """
    Test manifest file updating functionality
    
    Tests:
    - Creation of package section
    - Correct email update
    - Content model setting
    - Parent collection naming format
    - File path handling
    
    Args:
        tmp_path: pytest fixture providing temporary directory
    """
    manifest_path = tmp_path / "manifest.ini"
    manifest_path.write_text(
        """[package]
submitter_email=old_email@domain.com
content_model=old_model
parent_collection=old_value
"""
    )
    collection_name = "2006"
    trench_name = "46N-3W"

    update_manifest(manifest_path, collection_name, trench_name)

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(manifest_path)

    assert config.has_section('package'), "Manifest should have a [package] section"
    assert config.get('package', 'submitter_email') == 'mhunter2@fsu.edu', "submitter_email should be updated"
    assert config.get('package', 'content_model') == 'islandora:sp_large_image_cmodel', "content_model should be updated"
    expected_parent_collection = f"fsu:cetamuraExcavations_trenchPhotos_{collection_name}_{trench_name}"
    assert config.get('package', 'parent_collection') == expected_parent_collection, "parent_collection should be updated"


def test_update_manifest_invalid_path(tmp_path):
    """Test handling of invalid manifest path"""
    with pytest.raises(FileNotFoundError) as exc_info:
        update_manifest(tmp_path / "nonexistent.ini", "2006", "46N-3W")
    assert "manifest file not found" in str(exc_info.value).lower()


def test_sanitize_filename():
    """Test sanitizing invalid characters from filenames."""
    invalid_name = "unique:<>*id|?123/\\\""
    expected_name = "uniqueid123"
    sanitized = sanitize_filename(invalid_name)
    assert sanitized == expected_name, f"Sanitized name should be '{expected_name}', got '{sanitized}'"


@pytest.mark.parametrize("input_name,expected_name", [
    ("file:name*", "filename"),
    ("test/\\file", "testfile"),
    ("", ""),  # Edge case: empty string
    ("   spaces   ", "spaces"),  # Edge case: whitespace
    ("file.name.ext", "filenameext"),  # Edge case: dots
    ("αβγδε", ""),  # Edge case: non-ASCII
])
def test_sanitize_filename_cases(input_name, expected_name):
    assert sanitize_filename(input_name) == expected_name


def test_rename_files(tmp_path):
    """Test renaming files using the base name, ensuring no unnecessary suffixes are added."""
    tiff_file = tmp_path / "photo.tiff"
    xml_file = tmp_path / "metadata.xml"
    tiff_file.touch()
    xml_file.touch()

    base_name = "FSU_Cetamura_photos_20060523_46N3W_001"
    sanitized_base_name = sanitize_filename(base_name)

    # Rename without conflict
    new_tiff_path, new_xml_path = rename_files(tmp_path, tiff_file, xml_file, base_name)

    assert new_tiff_path.name == f"{sanitized_base_name}.tiff", "TIFF file should use base name without suffix"
    assert new_xml_path.name == f"{sanitized_base_name}.xml", "XML file should use base name without suffix"

    # Create duplicates to force conflict
    tiff_file_duplicate = tmp_path / "photo_duplicate.tiff"
    xml_file_duplicate = tmp_path / "metadata_duplicate.xml"
    tiff_file_duplicate.touch()
    xml_file_duplicate.touch()

    new_tiff_path_duplicate, new_xml_path_duplicate = rename_files(
        tmp_path, tiff_file_duplicate, xml_file_duplicate, base_name
    )

    assert new_tiff_path_duplicate.name == f"{sanitized_base_name}_a.tiff", "Second TIFF file should have '_a' suffix"
    assert new_xml_path_duplicate.name == f"{sanitized_base_name}_a.xml", "Second XML file should have '_a' suffix"

    # Create a third set to test additional conflicts
    tiff_file_third = tmp_path / "photo_third.tiff"
    xml_file_third = tmp_path / "metadata_third.xml"
    tiff_file_third.touch()
    xml_file_third.touch()

    new_tiff_path_third, new_xml_path_third = rename_files(
        tmp_path, tiff_file_third, xml_file_third, base_name
    )

    assert new_tiff_path_third.name == f"{sanitized_base_name}_b.tiff", "Third TIFF file should have '_b' suffix"
    assert new_xml_path_third.name == f"{sanitized_base_name}_b.xml", "Third XML file should have '_b' suffix"


def test_package_to_zip(tmp_path):
    """Test creating a zip package with renamed files and manifest."""
    tiff_path = tmp_path / "photo.tiff"
    xml_path = tmp_path / "metadata.xml"
    manifest_path = tmp_path / "manifest.ini"

    tiff_path.touch()
    xml_path.touch()
    manifest_path.touch()

    output_folder = tmp_path / "output"
    zip_path = package_to_zip(tiff_path, xml_path, manifest_path, output_folder)

    assert zip_path.exists(), "ZIP file should be created"
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        names = zipf.namelist()
        assert tiff_path.name in names, "TIFF file should be in the zip"
        assert xml_path.name in names, "XML file should be in the zip"
        assert manifest_path.name in names, "Manifest file should be in the zip"


def test_full_workflow(tmp_path):
    """Integration test for complete workflow"""
    # Setup files
    tiff_file = tmp_path / "original.tiff"
    xml_file = tmp_path / "original.xml"
    manifest_path = tmp_path / "MANIFEST.ini"
    tiff_file.touch()
    xml_file.touch()
    
    # Create manifest
    config = configparser.ConfigParser()
    config.write(manifest_path.open('w'))
    
    # Execute workflow
    collection = "2006"
    trench = "46N-3W"
    base_name = "FSU_Cetamura_photos_20060523_46N3W_001"
    
    update_manifest(manifest_path, collection, trench)
    new_tiff, new_xml = rename_files(tmp_path, tiff_file, xml_file, base_name)
    
    # Verify complete state
    assert new_tiff.exists()
    assert new_xml.exists()
    assert manifest_path.exists()
    # Add more assertions for complete workflow verification

import pytest
from pathlib import Path
from PIL import Image
import zipfile
from src.utils import find_photo_sets, convert_jpg_to_tiff, update_manifest, rename_files, package_to_zip, extract_iid_from_xml

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
    # Create a simple black square image to use as the test JPEG
    Image.new("RGB", (10, 10)).save(jpg_path, "JPEG")
    tiff_path = convert_jpg_to_tiff(jpg_path)
    assert tiff_path.exists(), "Converted TIFF file should exist"
    assert not jpg_path.exists(), "Original JPG file should be deleted"

def test_extract_iid_from_namespaced_xml(tmp_path):
    """Test extracting the IID from a namespaced XML file."""
    xml_file = tmp_path / "metadata.xml"
    xml_file.write_text(
        """<mods:root xmlns:mods="http://www.loc.gov/mods/v3">
               <mods:identifier type="IID">unique-id-123</mods:identifier>
           </mods:root>"""
    )
    iid = extract_iid_from_xml(xml_file)
    assert iid == "unique-id-123", "IID should match the content of the <identifier> tag"

def test_extract_iid_from_non_namespaced_xml(tmp_path):
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
    """Test updating the manifest with correct fields."""
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

    # Update the manifest
    update_manifest(manifest_path, collection_name, trench_name)

    expected_content = """[package]
submitter_email = mhunter2@fsu.edu
content_model = islandora:sp_large_image_cmodel
parent_collection = fsu:cetamuraExcavations_trenchPhotos_2006_46N-3W"""

    updated_content = manifest_path.read_text().strip()

    assert updated_content == expected_content, "Manifest content should match the expected format"

def test_rename_files(tmp_path):
    """Test renaming files using the extracted IID."""
    tiff_file = tmp_path / "photo.tiff"
    xml_file = tmp_path / "metadata.xml"
    tiff_file.touch()
    xml_file.touch()

    iid = "unique-id-123"

    new_tiff_path, new_xml_path = rename_files(tmp_path, tiff_file, xml_file, iid)

    assert new_tiff_path.name == f"{iid}.tiff", "TIFF file should be renamed using IID"
    assert new_xml_path.name == f"{iid}.xml", "XML file should be renamed using IID"

def test_package_to_zip(tmp_path):
    """Test creating a zip package with renamed files and manifest."""
    tiff_path = tmp_path / "photo.tiff"
    xml_path = tmp_path / "metadata.xml"
    manifest_path = tmp_path / "manifest.ini"

    # Create sample files
    tiff_path.touch()
    xml_path.touch()
    manifest_path.write_text(
        """[package]
        submitter_email=mhunter2@fsu.edu
        content_model=islandora:sp_large_image_cmodel
        parent_collection=old_value
        """
    )

    output_folder = tmp_path / "output"
    zip_path = package_to_zip(tiff_path, xml_path, manifest_path, output_folder)

    # Verify the zip file
    assert zip_path.exists(), "ZIP file should be created"
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        names = zipf.namelist()
        assert "photo.tiff" in names, "TIFF file should be in the zip"
        assert "metadata.xml" in names, "XML file should be in the zip"
        assert "manifest.ini" in names, "Manifest file should be in the zip"

def test_rename_files_with_duplicates(tmp_path):
    """Test renaming files with duplicate names using letter suffixes."""
    tiff_file_1 = tmp_path / "photo1.tiff"
    xml_file_1 = tmp_path / "metadata1.xml"
    tiff_file_2 = tmp_path / "photo2.tiff"
    xml_file_2 = tmp_path / "metadata2.xml"
    tiff_file_1.touch()
    xml_file_1.touch()
    tiff_file_2.touch()
    xml_file_2.touch()

    iid = "unique-id-123"

    # First renaming should work without issues
    new_tiff_path_1, new_xml_path_1 = rename_files(tmp_path, tiff_file_1, xml_file_1, iid)

    # Second renaming should append a suffix to avoid conflicts
    new_tiff_path_2, new_xml_path_2 = rename_files(tmp_path, tiff_file_2, xml_file_2, iid)

    assert new_tiff_path_1.name == f"{iid}.tiff", "First TIFF file should not have a suffix"
    assert new_xml_path_1.name == f"{iid}.xml", "First XML file should not have a suffix"
    assert new_tiff_path_2.name == f"{iid}_a.tiff", "Second TIFF file should have an '_a' suffix"
    assert new_xml_path_2.name == f"{iid}_a.xml", "Second XML file should have an '_a' suffix"

    # Add a third file to test subsequent letters
    tiff_file_3 = tmp_path / "photo3.tiff"
    xml_file_3 = tmp_path / "metadata3.xml"
    tiff_file_3.touch()
    xml_file_3.touch()

    new_tiff_path_3, new_xml_path_3 = rename_files(tmp_path, tiff_file_3, xml_file_3, iid)

    assert new_tiff_path_3.name == f"{iid}_b.tiff", "Third TIFF file should have a '_b' suffix"
    assert new_xml_path_3.name == f"{iid}_b.xml", "Third XML file should have a '_b' suffix"
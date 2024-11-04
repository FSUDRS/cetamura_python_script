import pytest  
from pathlib import Path
from PIL import Image
import zipfile
from src.utils import find_photo_sets, convert_jpg_to_tiff, update_manifest, rename_files, package_to_zip



@pytest.fixture
def setup_test_directory(tmp_path):
    """Setup temporary directory structure for testing find_photo_sets."""
    valid_dir = tmp_path / "valid_set"
    valid_dir.mkdir()
    (valid_dir / "photo.jpg").touch()
    (valid_dir / "metadata.xml").touch()
    (valid_dir / "manifest.ini").touch()

    incomplete_dir = tmp_path / "incomplete_set"
    incomplete_dir.mkdir()
    (incomplete_dir / "photo.jpg").touch()

    extra_dir = tmp_path / "extra_set"
    extra_dir.mkdir()
    (extra_dir / "photo1.jpg").touch()
    (extra_dir / "photo2.jpg").touch()
    (extra_dir / "metadata.xml").touch()
    (extra_dir / "manifest.ini").touch()

    return tmp_path


def test_find_photo_sets(setup_test_directory):
    photo_sets = find_photo_sets(setup_test_directory)
    assert len(photo_sets) == 2, "Expected 2 valid photo sets"
    valid_dirs = [str(setup_test_directory / "valid_set"), str(setup_test_directory / "extra_set")]
    detected_dirs = [str(photo_set[0]) for photo_set in photo_sets]
    for dir in valid_dirs:
        assert dir in detected_dirs, f"Expected {dir} to be detected as a valid photo set"


def test_convert_jpg_to_tiff(tmp_path):
    """Test converting a .jpg file to .tiff with actual image data."""
    jpg_path = tmp_path / "photo.jpg"
    # Create a simple black square image to use as the test JPEG
    Image.new("RGB", (10, 10)).save(jpg_path, "JPEG")
    tiff_path = convert_jpg_to_tiff(jpg_path)
    assert tiff_path.exists(), "Converted TIFF file should exist"
    assert not jpg_path.exists(), "Original JPG file should be deleted"


def test_update_manifest(tmp_path):
    manifest_path = tmp_path / "manifest.ini"
    manifest_path.write_text("parent_collection = old_value")
    update_manifest(manifest_path, "new_collection")
    updated_content = manifest_path.read_text()
    assert "parent_collection = fsu:new_collection" in updated_content, "Manifest should contain the updated collection name"


def test_rename_files(tmp_path):
    tiff_file = tmp_path / "photo.tiff"
    xml_file = tmp_path / "metadata.xml"
    tiff_file.touch()
    xml_file.touch()
    trench_name = "TrenchName"
    photo_number = "001"
    date = "20220101"
    new_tiff_path, new_xml_path = rename_files(tmp_path, tiff_file, xml_file, trench_name, photo_number, date)
    assert new_tiff_path.name == f"FSU_Cetamura_photos_{date}_{trench_name}_{photo_number}.tiff"
    assert new_xml_path.name == f"FSU_Cetamura_photos_{date}_{trench_name}_{photo_number}.xml"


def test_package_to_zip(tmp_path):
    tiff_path = tmp_path / "photo.tiff"
    xml_path = tmp_path / "metadata.xml"
    manifest_path = tmp_path / "manifest.ini"
    for file in [tiff_path, xml_path, manifest_path]:
        file.touch()
    output_folder = tmp_path / "output"
    zip_path = package_to_zip(tiff_path, xml_path, manifest_path, output_folder)
    assert zip_path.exists(), "ZIP file should be created"
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        names = zipf.namelist()
        assert "photo.tiff" in names, "TIFF file should be in the zip"
        assert "metadata.xml" in names, "XML file should be in the zip"
        assert "manifest.ini" in names, "Manifest file should be in the zip"


def test_rename_files_with_duplicates(tmp_path):
    tiff_file_1 = tmp_path / "photo1.tiff"
    xml_file_1 = tmp_path / "metadata1.xml"
    tiff_file_2 = tmp_path / "photo2.tiff"
    xml_file_2 = tmp_path / "metadata2.xml"
    tiff_file_1.touch()
    xml_file_1.touch()
    tiff_file_2.touch()
    xml_file_2.touch()

    trench_name = "Trench"
    photo_number = "001"
    date = "20220101"

    new_tiff_path_1, new_xml_path_1 = rename_files(tmp_path, tiff_file_1, xml_file_1, trench_name, photo_number, date)
    new_tiff_path_2, new_xml_path_2 = rename_files(tmp_path, tiff_file_2, xml_file_2, trench_name, photo_number, date)

    assert new_tiff_path_1 != new_tiff_path_2, "Duplicate TIFF files should not overwrite each other"
    assert new_xml_path_1 != new_xml_path_2, "Duplicate XML files should not overwrite each other"

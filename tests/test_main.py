"""
Tests for the core functions in main.py
Focused on functions actually used by the GUI application
"""
import pytest
from pathlib import Path
from PIL import Image
import csv
from src.main import (
    find_photo_sets,
    find_photo_sets_enhanced,
    convert_to_tiff,
    rename_files,
    package_to_zip,
    extract_iid_from_xml,
    extract_iid_from_xml_enhanced,
    sanitize_name,
    PhotoSet,
    FilePair,
    BatchContext,
    validate_photo_set,
    batch_process_with_safety_nets,
    apply_exif_orientation,
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
    directory, image_files, xml_files, ini_files = result[0]
    assert str(directory) == str(setup_test_directory / "valid_set")

def test_convert_to_tiff(tmp_path):
    """Test Image to TIFF conversion (JPG support)."""
    # Create a small test JPG image
    jpg_path = tmp_path / "test.jpg"
    image = Image.new('RGB', (10, 10), color='red')
    image.save(jpg_path, 'JPEG')
    
    result = convert_to_tiff(jpg_path)
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


# ===== NEW TESTS FOR MULTI-FILE PROCESSING AND PHOTOSET =====

def test_photoset_namedtuple_structure():
    """Test that PhotoSet NamedTuple has correct structure"""
    base_dir = Path("/test/dir")
    image_files = [Path("/test/dir/img1.jpg"), Path("/test/dir/img2.jpg")]
    xml_files = [Path("/test/dir/img1.xml"), Path("/test/dir/img2.xml")]
    manifest = Path("/test/dir/manifest.ini")
    
    photo_set = PhotoSet(
        base_directory=base_dir,
        image_files=image_files,
        xml_files=xml_files,
        manifest_file=manifest,
        structure_type='standard'
    )
    
    # Verify structure
    assert photo_set.base_directory == base_dir
    assert len(photo_set.image_files) == 2
    assert len(photo_set.xml_files) == 2
    assert photo_set.manifest_file == manifest
    assert photo_set.structure_type == 'standard'
    
    # Verify it's a list, not a single file
    assert isinstance(photo_set.image_files, list)
    assert isinstance(photo_set.xml_files, list)
    assert isinstance(photo_set.manifest_file, Path)


def test_filepair_namedtuple_structure():
    """Test that FilePair NamedTuple has correct structure"""
    xml_path = Path("/test/file.xml")
    jpg_path = Path("/test/file.jpg")
    iid = "cetamura:12345"
    
    file_pair = FilePair(xml=xml_path, image=jpg_path, iid=iid)
    
    assert file_pair.xml == xml_path
    assert file_pair.image == jpg_path
    assert file_pair.iid == iid


def test_filepair_with_optional_paths():
    """Test FilePair with None values (orphaned files)"""
    # XML without JPG
    file_pair1 = FilePair(xml=Path("/test/file.xml"), image=None, iid="test:001")
    assert file_pair1.xml is not None
    assert file_pair1.image is None
    
    # JPG without XML (shouldn't happen but test the structure)
    file_pair2 = FilePair(xml=None, image=Path("/test/file.jpg"), iid="test:002")
    assert file_pair2.xml is None
    assert file_pair2.image is not None


@pytest.fixture
def setup_multi_file_directory(tmp_path):
    """Setup directory with MULTIPLE files per photo set"""
    photo_set_dir = tmp_path / "multi_file_set"
    photo_set_dir.mkdir()
    
    # Create 3 JPG/XML pairs with matching stems
    test_files = []
    for i in range(1, 4):
        # Create JPG
        jpg_file = photo_set_dir / f"FSU_Cetamura_photos_20060523_46N3W_00{i}.jpg"
        img = Image.new('RGB', (10, 10), color='red')
        img.save(jpg_file, 'JPEG')
        
        # Create matching XML
        xml_file = photo_set_dir / f"FSU_Cetamura_photos_20060523_46N3W_00{i}.xml"
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
    <mods:identifier type="IID">FSU_Cetamura_photos_20060523_46N3W_00{i}</mods:identifier>
</mods:mods>"""
        xml_file.write_text(xml_content)
        
        test_files.append((jpg_file, xml_file))
    
    # Create manifest
    manifest_file = photo_set_dir / "manifest.ini"
    manifest_file.touch()
    
    return tmp_path, photo_set_dir, test_files


def test_find_photo_sets_enhanced_with_multiple_files(setup_multi_file_directory):
    """Test that find_photo_sets_enhanced finds ALL files in a photo set"""
    tmp_path, photo_set_dir, test_files = setup_multi_file_directory
    
    # Find photo sets
    result = find_photo_sets_enhanced(str(tmp_path))
    
    # Should find exactly 1 photo set
    assert len(result) == 1
    
    photo_set = result[0]
    
    # Verify it's a PhotoSet NamedTuple
    assert isinstance(photo_set, PhotoSet)
    
    # Verify it contains ALL 3 files
    assert len(photo_set.image_files) == 3
    assert len(photo_set.xml_files) == 3
    
    # Verify manifest is a single file (not a list)
    assert isinstance(photo_set.manifest_file, Path)
    assert photo_set.manifest_file.name == "manifest.ini"


def test_validate_photo_set_with_multiple_files(setup_multi_file_directory):
    """Test that validate_photo_set correctly validates multi-file sets"""
    tmp_path, photo_set_dir, test_files = setup_multi_file_directory
    
    photo_sets = find_photo_sets_enhanced(str(tmp_path))
    assert len(photo_sets) == 1
    
    photo_set = photo_sets[0]
    
    # Should validate successfully
    is_valid = validate_photo_set(photo_set)
    assert is_valid is True


def test_extract_iid_from_xml_enhanced(tmp_path):
    """Test the enhanced IID extraction function"""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
    <mods:identifier type="IID">cetamura:test123</mods:identifier>
</mods:mods>"""
    
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content)
    
    result = extract_iid_from_xml_enhanced(xml_file)
    assert result == "cetamura:test123"


def test_extract_iid_handles_invalid_xml(tmp_path):
    """Test that extract_iid_from_xml_enhanced handles invalid XML gracefully"""
    xml_file = tmp_path / "invalid.xml"
    xml_file.write_text("not valid xml content")
    
    result = extract_iid_from_xml_enhanced(xml_file)
    assert result is None


def test_batch_process_multi_file_dry_run(setup_multi_file_directory):
    """Test that batch processing handles ALL files in dry-run mode"""
    tmp_path, photo_set_dir, test_files = setup_multi_file_directory
    
    # Run batch process in dry-run mode
    success_count, error_count, csv_path = batch_process_with_safety_nets(
        folder_path=str(tmp_path),
        dry_run=True,
        staging=False
    )
    
    # Should process all 3 files successfully
    assert success_count == 3
    assert error_count == 0
    
    # Verify CSV report exists
    assert csv_path.exists()
    
    # Read CSV and verify all files are listed
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Header + 3 data rows + 1 summary row = 5 rows
    assert len(rows) >= 4  # At least header + 3 files
    
    # Verify CSV contains entries for all 3 IIDs
    csv_content = csv_path.read_text()
    assert "FSU_Cetamura_photos_20060523_46N3W_001" in csv_content
    assert "FSU_Cetamura_photos_20060523_46N3W_002" in csv_content
    assert "FSU_Cetamura_photos_20060523_46N3W_003" in csv_content
    
    # Verify original files are unchanged (dry-run)
    assert all(jpg.exists() for jpg, xml in test_files)
    assert all(xml.exists() for jpg, xml in test_files)


def test_batch_process_multi_file_staging(setup_multi_file_directory):
    """Test that batch processing handles ALL files in staging mode"""
    tmp_path, photo_set_dir, test_files = setup_multi_file_directory
    
    # Run batch process in staging mode
    success_count, error_count, csv_path = batch_process_with_safety_nets(
        folder_path=str(tmp_path),
        dry_run=False,
        staging=True
    )
    
    # Should process all 3 files successfully
    assert success_count == 3
    assert error_count == 0
    
    # Verify staging_output directory was created
    staging_dir = tmp_path / "staging_output"
    assert staging_dir.exists()
    
    # Verify 3 ZIP files were created
    zip_files = list(staging_dir.glob("*.zip"))
    assert len(zip_files) == 3


def test_file_matching_by_stem(setup_multi_file_directory):
    """Test that JPG and XML files are matched by filename stem"""
    tmp_path, photo_set_dir, test_files = setup_multi_file_directory
    
    photo_sets = find_photo_sets_enhanced(str(tmp_path))
    photo_set = photo_sets[0]
    
    # Verify each XML has a matching JPG with the same stem
    for xml_file in photo_set.xml_files:
        xml_stem = xml_file.stem
        matching_jpgs = [jpg for jpg in photo_set.image_files if jpg.stem == xml_stem]
        assert len(matching_jpgs) == 1, f"Expected exactly 1 matching JPG for {xml_file.name}"


def test_hierarchical_photo_set_structure(tmp_path):
    """Test detection of hierarchical photo set structures"""
    # Create hierarchical structure:
    # parent/
    #   manifest.ini
    #   subdir1/
    #     file1.jpg, file1.xml
    #   subdir2/
    #     file2.jpg, file2.xml
    
    parent_dir = tmp_path / "parent"
    parent_dir.mkdir()
    
    manifest = parent_dir / "manifest.ini"
    manifest.touch()
    
    # Create subdirectories with files
    for i in [1, 2]:
        subdir = parent_dir / f"subdir{i}"
        subdir.mkdir()
        
        jpg = subdir / f"file{i}.jpg"
        img = Image.new('RGB', (10, 10), color='blue')
        img.save(jpg, 'JPEG')
        
        xml = subdir / f"file{i}.xml"
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
    <mods:identifier type="IID">test_hierarchical_00{i}</mods:identifier>
</mods:mods>"""
        xml.write_text(xml_content)
    
    # Find photo sets
    photo_sets = find_photo_sets_enhanced(str(tmp_path), flexible_structure=True)
    
    # Should find 2 photo sets (one for each subdirectory)
    assert len(photo_sets) == 2
    
    # Each should have structure_type='hierarchical'
    for ps in photo_sets:
        assert ps.structure_type == 'hierarchical'
        assert len(ps.image_files) == 1
        assert len(ps.xml_files) == 1


def test_exif_orientation_correction(tmp_path):
    """Test that EXIF orientation is properly detected and corrected"""
    # Create a test image with EXIF orientation
    img = Image.new('RGB', (100, 50), color='red')  # Wide rectangle
    
    jpg_path = tmp_path / "test_orientation.jpg"
    
    # Save with EXIF orientation tag (6 = Rotated 90° CW)
    exif = img.getexif()
    exif[274] = 6  # Orientation tag
    img.save(jpg_path, 'JPEG', exif=exif)
    
    # Apply orientation correction
    with Image.open(jpg_path) as img_to_correct:
        corrected_img = apply_exif_orientation(img_to_correct, jpg_path)
        
        # After 270° rotation, wide rectangle becomes tall
        # Original: 100x50, After rotation: 50x100
        assert corrected_img.size == (50, 100)


def test_backward_compatibility_find_photo_sets(setup_multi_file_directory):
    """Test that find_photo_sets (backward compatible) returns correct format"""
    tmp_path, photo_set_dir, test_files = setup_multi_file_directory
    
    # Use old function signature
    result = find_photo_sets(str(tmp_path))
    
    # Should return list of tuples
    assert isinstance(result, list)
    assert len(result) == 1
    
    directory, image_files, xml_files, manifest_files = result[0]
    
    # Verify tuple format
    assert isinstance(directory, Path)
    assert isinstance(image_files, list)
    assert isinstance(xml_files, list)
    assert isinstance(manifest_files, list)
    
    # Verify it contains ALL files
    assert len(image_files) == 3
    assert len(xml_files) == 3
    assert len(manifest_files) == 1


def test_no_files_skipped_in_multi_file_set(setup_multi_file_directory):
    """
    CRITICAL TEST: Verify that ALL files are processed, not just the first one.
    This test prevents regression of the "only first file processed" bug.
    """
    tmp_path, photo_set_dir, test_files = setup_multi_file_directory
    
    # Get photo sets
    photo_sets = find_photo_sets_enhanced(str(tmp_path))
    assert len(photo_sets) == 1
    
    photo_set = photo_sets[0]
    
    # CRITICAL: Verify we have 3 XML files to process
    assert len(photo_set.xml_files) == 3, "Photo set should contain 3 XML files"
    
    # Run dry-run to check processing logic
    success_count, error_count, csv_path = batch_process_with_safety_nets(
        folder_path=str(tmp_path),
        dry_run=True,
        staging=False
    )
    
    # CRITICAL: All 3 files should be processed
    assert success_count == 3, f"Expected 3 files processed, got {success_count}"
    assert error_count == 0, f"Expected 0 errors, got {error_count}"
    
    # Read CSV to verify all 3 files have entries
    with open(csv_path, 'r', encoding='utf-8') as f:
        csv_content = f.read()
    
    # Count how many times each IID appears in CSV
    iid_001_count = csv_content.count("FSU_Cetamura_photos_20060523_46N3W_001")
    iid_002_count = csv_content.count("FSU_Cetamura_photos_20060523_46N3W_002")
    iid_003_count = csv_content.count("FSU_Cetamura_photos_20060523_46N3W_003")
    
    # Each IID should appear at least once in the CSV
    assert iid_001_count >= 1, "File 001 was not processed"
    assert iid_002_count >= 1, "File 002 was not processed"
    assert iid_003_count >= 1, "File 003 was not processed"

from pathlib import Path
import logging
from PIL import Image
import xml.etree.ElementTree as ET
from datetime import datetime
import zipfile
import re
from typing import Optional
import configparser

NAMESPACES = {
    'mods': 'http://www.loc.gov/mods/v3'
}
DEFAULT_EMAIL = 'mhunter2@fsu.edu'
CONTENT_MODEL = 'islandora:sp_large_image_cmodel'

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def find_photo_sets(parent_folder: str) -> list:
    """
    Finds valid photo sets (JPG/JPEG, XML, and manifest.ini) in a directory structure.

    Args:
        parent_folder (str): Path to the parent folder to search.

    Returns:
        list: A list of tuples containing valid photo sets. Each tuple contains:
              (directory, list of JPG/JPEG files, list of XML files, list of manifest files)
    """
    photo_sets = []
    parent_path = Path(parent_folder).resolve()
    logging.info(f"Searching for photo sets in: {parent_path}")

    for candidate_dir in parent_path.rglob('*'):
        if candidate_dir.is_dir():
            logging.debug(f"Inspecting directory: {candidate_dir}")
            
            # Gather files
            jpg_files = [
                f for f in candidate_dir.glob('*')
                if f.suffix.lower() in ['.jpg', '.jpeg']
            ]
            xml_files = [f for f in candidate_dir.glob('*') if f.suffix.lower() == '.xml']
            ini_file = next(
                (f for f in candidate_dir.glob('*') if f.name.lower() == 'manifest.ini'), 
                None
            )

            # Debugging output for found files
            logging.debug(f"Found JPG/JPEG files: {jpg_files}")
            logging.debug(f"Found XML files: {xml_files}")
            logging.debug(f"Found manifest.ini: {ini_file}")

            # Validate and collect photo sets
            if jpg_files and xml_files and ini_file:
                photo_sets.append((candidate_dir, jpg_files, xml_files, [ini_file]))
                logging.info(f"Valid photo set found in {candidate_dir}")
            else:
                missing = []
                if not jpg_files:
                    missing.append("JPG/JPEG files")
                if not xml_files:
                    missing.append("XML files")
                if not ini_file:
                    missing.append("manifest.ini")
                logging.warning(f"Directory {candidate_dir} missing: {', '.join(missing)}")

    logging.info(f"Total photo sets found: {len(photo_sets)} in {parent_folder}")
    return photo_sets

def convert_jpg_to_tiff(jpg_path: Path) -> Path:
    """
    Converts a .jpg file to .tiff and removes the original JPG.
    """
    try:
        tiff_path = jpg_path.with_suffix('.tiff')
        Image.open(jpg_path).save(tiff_path, "TIFF")
        jpg_path.unlink()
        logging.info(f"Converted {jpg_path} to {tiff_path}")
        return tiff_path
    except Exception as e:
        logging.error(f"Error converting {jpg_path} to TIFF: {e}")
        raise e

def extract_iid_from_xml(xml_file: Path) -> str:
    """
    Extracts the content of the <identifier type="IID"> tag from an XML file.
    Handles both namespaced and non-namespaced XML files.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Define namespaces if applicable
        namespaces = {'mods': "http://www.loc.gov/mods/v3"}

        # Try to find the IID in a namespaced environment
        identifier = root.find(".//mods:identifier[@type='IID']", namespaces)
        if identifier is not None and identifier.text:
            iid = identifier.text.strip()
            logging.info(f"Extracted IID '{iid}' from {xml_file}")
            return iid

        # Fallback to non-namespaced lookup
        identifier = root.find(".//identifier[@type='IID']")
        if identifier is not None and identifier.text:
            iid = identifier.text.strip()
            logging.info(f"Extracted IID '{iid}' from {xml_file}")
            return iid

        # If not found, raise an error
        raise ValueError(f"Missing or invalid <identifier type='IID'> in {xml_file}")

    except Exception as e:
        logging.error(f"Error parsing XML file {xml_file}: {e}")
        raise e

def extract_iid(xml_file: Path) -> str:
    """
    Extract IID from XML file.
    
    Args:
        xml_file: Path to XML file
        
    Returns:
        str: Extracted IID value
        
    Raises:
        ValueError: If IID not found
        Exception: For XML parsing errors
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Define namespaces if applicable
        namespaces = {'mods': "http://www.loc.gov/mods/v3"}

        # Try to find the IID in a namespaced environment
        identifier = root.find(".//mods:identifier[@type='IID']", namespaces)
        if identifier is not None and identifier.text:
            iid = identifier.text.strip()
            logging.info(f"Extracted IID '{iid}' from {xml_file}")
            return iid

        # Fallback to non-namespaced lookup
        identifier = root.find(".//identifier[@type='IID']")
        if identifier is not None and identifier.text:
            iid = identifier.text.strip()
            logging.info(f"Extracted IID '{iid}' from {xml_file}")
            return iid

        # If not found, raise an error
        raise ValueError(f"Missing or invalid <identifier type='IID'> in {xml_file}")

    except Exception as e:
        logging.error(f"Error parsing XML file {xml_file}: {e}")
        raise e

def update_manifest(manifest_path: Path, collection_name: str, trench_name: str) -> None:
    """
    Updates manifest.ini with specified fields.
    
    Args:
        manifest_path: Path to manifest file
        collection_name: Collection identifier
        trench_name: Trench identifier
    """
    config = configparser.ConfigParser()
    config.optionxform = str  # Preserve case
    config.read(manifest_path)
    
    if not config.has_section('package'):
        config.add_section('package')
        
    config['package'].update({
        'submitter_email': 'mhunter2@fsu.edu',
        'content_model': 'islandora:sp_large_image_cmodel',
        'parent_collection': f"fsu:cetamuraExcavations_trenchPhotos_{collection_name}_{trench_name}"
    })
    
    with open(manifest_path, 'w') as f:
        config.write(f)

def rename_files(path: Path, tiff_file: Path, xml_file: Path, iid: str) -> tuple:
    """
    Renames TIFF and XML files based on the extracted IID, ensuring no unnecessary suffixes are added.
    """
    base_name = sanitize_filename(iid)
    new_tiff_path = path / f"{base_name}.tiff"
    new_xml_path = path / f"{base_name}.xml"

    # Check if the new paths are different from the current file paths
    need_to_rename_tiff = new_tiff_path != tiff_file
    need_to_rename_xml = new_xml_path != xml_file

    conflict = False
    if need_to_rename_tiff and new_tiff_path.exists():
        conflict = True
    if need_to_rename_xml and new_xml_path.exists():
        conflict = True

    if conflict:
        logging.warning(f"File conflict detected for base name {base_name}. Adding suffix.")
        suffix = 0
        while True:
            suffix_letter = chr(97 + suffix)  # 'a', 'b', 'c', etc.
            new_tiff_path_candidate = path / f"{base_name}_{suffix_letter}.tiff"
            new_xml_path_candidate = path / f"{base_name}_{suffix_letter}.xml"
            suffix += 1
            if suffix > 25:  # Safety limit
                raise FileExistsError(f"Too many duplicate files for base name: {iid}")
            if (not new_tiff_path_candidate.exists() or new_tiff_path_candidate == tiff_file) and \
               (not new_xml_path_candidate.exists() or new_xml_path_candidate == xml_file):
                new_tiff_path = new_tiff_path_candidate
                new_xml_path = new_xml_path_candidate
                break
    else:
        logging.info(f"No conflicts detected for base name {base_name}.")

    # Rename files if needed
    if need_to_rename_tiff:
        tiff_file.rename(new_tiff_path)
    if need_to_rename_xml:
        xml_file.rename(new_xml_path)
    logging.info(f"Renamed files to {new_tiff_path.name} and {new_xml_path.name}")
    return new_tiff_path, new_xml_path

def sanitize_filename(filename: str) -> str:
    """
    Removes or replaces invalid characters in a filename.
    """
    # Replace spaces with underscores
    sanitized = filename.replace(" ", "_")
    # Remove invalid characters for filenames
    sanitized = re.sub(r'[<>:"/\\|?*\']', '', sanitized)
    return sanitized

def package_to_zip(tiff_path: Path, xml_path: Path, manifest_path: Path, output_folder: Path) -> Path:
    """
    Creates a zip file containing .tiff, .xml, and a properly formatted manifest.ini,
    handling conflicts in zip file names by adding suffixes only when necessary.
    """
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        base_name = tiff_path.stem  # Use the base name from the TIFF file
        sanitized_base_name = sanitize_filename(base_name)
        zip_path = output_folder / f"{sanitized_base_name}.zip"

        # Check if zip file already exists (excluding the one we're about to create)
        if zip_path.exists():
            logging.warning(f"Zip file conflict detected for base name {sanitized_base_name}. Adding suffix.")
            suffix = 0
            while True:
                suffix_letter = chr(97 + suffix)  # 'a', 'b', 'c', etc.
                zip_path_candidate = output_folder / f"{sanitized_base_name}_{suffix_letter}.zip"
                suffix += 1
                if suffix > 25:  # Safety limit
                    raise FileExistsError(f"Too many duplicate zip files for base name: {sanitized_base_name}")
                if not zip_path_candidate.exists():
                    zip_path = zip_path_candidate
                    break
        else:
            logging.info(f"No conflicts detected for zip file name {zip_path.name}.")

        # Ensure no additional modifications to file names inside the zip
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in [tiff_path, xml_path, manifest_path]:
                zipf.write(file, arcname=file.name)  # Preserve original file name
        logging.info(f"Created zip archive: {zip_path}")
        return zip_path
    except Exception as e:
        logging.error(f"Error creating zip archive {zip_path}: {e}")
        raise e
    
def batch_process(root: str, jpg_files: list, xml_files: list, ini_files: list) -> None:
    """
    Processes each photo set by:
    - Converting JPG to TIFF.
    - Extracting the IID from the XML file.
    - Updating and copying the manifest file.
    - Renaming the TIFF and XML files based on the IID.
    - Packaging the files into a ZIP archive.
    """
    try:
        path = Path(root)
        manifest_path = ini_files[0]

        # Extract collection details from directory structure
        collection_year = path.parts[-4]
        collection_date = path.parts[-3]
        trench_name = path.parts[-2]

        # Update the manifest
        update_manifest(manifest_path, collection_year, trench_name)

        # Process each pair of JPG and XML files
        for jpg_file, xml_file in zip(jpg_files, xml_files):
            iid = extract_iid_from_xml(xml_file)  # Extract IID
            logging.debug(f"Processing IID: {iid}")

            tiff_path = convert_jpg_to_tiff(jpg_file)  # Convert JPG to TIFF
            new_tiff_path, new_xml_path = rename_files(path, tiff_path, xml_file, iid)  # Rename files

            output_folder = path.parents[2] / f"{collection_date}_CetamuraUploadBatch"
            package_to_zip(new_tiff_path, new_xml_path, manifest_path, output_folder)  # Package files

        logging.info(f"Batch processing completed for {root}")

    except Exception as e:
        logging.error(f"Error during batch processing for {root}: {e}")
        raise e

def validate_inputs(collection_name: str, trench_name: str) -> None:
    if not collection_name or not trench_name:
        raise ValueError("Collection and trench names cannot be empty")
    if not collection_name.isalnum() or not trench_name.replace('-', '').isalnum():
        raise ValueError("Invalid characters in collection or trench name")
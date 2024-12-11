from pathlib import Path
import logging
from PIL import Image,UnidentifiedImageError
import xml.etree.ElementTree as ET
import zipfile
import re
from typing import Optional

NAMESPACES = {
    'mods': 'http://www.loc.gov/mods/v3'
}

# Set up logging
debug_handler = logging.FileHandler("batch_tool_debug.log", mode="w", encoding="utf-8")
debug_handler.setLevel(logging.DEBUG)

info_handler = logging.FileHandler("batch_tool.log", mode="w", encoding="utf-8")
info_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[info_handler, debug_handler, logging.StreamHandler()]
)

def sanitize_name(name: str) -> str:
    """
    Removes or replaces invalid characters and normalizes whitespace.
    """
    sanitized = re.sub(r'[<>:"/\\|?*\']', '', name.strip().replace(' ', '_'))
    return sanitized


def validate_directory_structure(path: Path) -> None:
    """
    Validates that the directory structure has the required components.
    Raises an error if the structure is invalid.
    """
    parts = path.parts
    if len(parts) < 4:
        raise ValueError(f"Invalid directory structure: {path}. Expected at least 4 levels of directories.")


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

            jpg_files = [
                f for f in candidate_dir.glob('*')
                if f.suffix.lower() in ['.jpg', '.jpeg']
            ]
            xml_files = [f for f in candidate_dir.glob('*') if f.suffix.lower() == '.xml']
            ini_file = next(
                (f for f in candidate_dir.glob('*') if f.name.lower() == 'manifest.ini'),
                None
            )

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

def fix_corrupted_jpg(jpg_path: Path) -> Optional[Path]:
    """
    Attempts to fix a corrupted JPG by re-encoding it. If successful, returns the fixed file path.
    """
    try:
        fixed_path = jpg_path.with_name(f"{jpg_path.stem}_fixed{jpg_path.suffix}")
        with Image.open(jpg_path) as img:
            img = img.convert("RGB")  # Ensure standard RGB encoding
            img.save(fixed_path, "JPEG")
        logging.info(f"Fixed corrupted image: {jpg_path} -> {fixed_path}")
        return fixed_path
    except Exception as e:
        logging.error(f"Failed to fix corrupted image {jpg_path}: {e}")
        return None


def convert_jpg_to_tiff(jpg_path: Path) -> Optional[Path]:
    """
    Converts a .jpg file to .tiff. Detects and attempts to fix corrupted files before skipping them.
    """
    try:
        tiff_path = jpg_path.with_suffix('.tiff')
        with Image.open(jpg_path) as img:
            img.verify()  # Verify if the image is corrupted
            img = Image.open(jpg_path)  # Re-open the image to save as TIFF
            img.save(tiff_path, "TIFF")
        logging.info(f"Converted {jpg_path} to {tiff_path}")
        return tiff_path
    except UnidentifiedImageError as e:
        logging.warning(f"Corrupted file detected: {jpg_path}. Attempting to fix...")
        fixed_path = fix_corrupted_jpg(jpg_path)
        if fixed_path:
            return convert_jpg_to_tiff(fixed_path)  # Retry with the fixed file
        logging.error(f"Unable to process {jpg_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error converting {jpg_path} to TIFF: {e}")
        return None

def extract_iid_from_xml(xml_file: Path) -> str:
    """
    Extracts the content of the <identifier type="IID"> tag from an XML file.
    Handles both namespaced and non-namespaced XML files.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        identifier = root.find(".//mods:identifier[@type='IID']", NAMESPACES)
        if identifier is not None and identifier.text:
            iid = identifier.text.strip()
            logging.info(f"Extracted IID '{iid}' from {xml_file}")
            return iid

        identifier = root.find(".//identifier[@type='IID']")
        if identifier is not None and identifier.text:
            iid = identifier.text.strip()
            logging.info(f"Extracted IID '{iid}' from {xml_file}")
            return iid

        raise ValueError(f"Missing or invalid <identifier type='IID'> in {xml_file}")
    except Exception as e:
        logging.error(f"Error parsing XML file {xml_file}: {e}")
        raise e


def rename_files(path: Path, tiff_file: Path, xml_file: Path, iid: str) -> tuple:
    """
    Renames TIFF and XML files based on the extracted IID, ensuring no unnecessary suffixes are added.
    """
    base_name = sanitize_name(iid)
    new_tiff_path = path / f"{base_name}.tiff"
    new_xml_path = path / f"{base_name}.xml"

    conflict = False
    if new_tiff_path.exists() and new_tiff_path != tiff_file:
        conflict = True
    if new_xml_path.exists() and new_xml_path != xml_file:
        conflict = True

    if conflict:
        suffix = 0
        while True:
            suffix_letter = chr(97 + suffix)
            new_tiff_candidate = path / f"{base_name}_{suffix_letter}.tiff"
            new_xml_candidate = path / f"{base_name}_{suffix_letter}.xml"
            if not new_tiff_candidate.exists() and not new_xml_candidate.exists():
                new_tiff_path = new_tiff_candidate
                new_xml_path = new_xml_candidate
                break
            suffix += 1

    tiff_file.rename(new_tiff_path)
    xml_file.rename(new_xml_path)
    logging.info(f"Renamed files to {new_tiff_path} and {new_xml_path}")
    return new_tiff_path, new_xml_path


def package_to_zip(tiff_path: Path, xml_path: Path, manifest_path: Path, output_folder: Path) -> Path:
    """
    Creates a zip file containing .tiff, .xml, and a properly formatted manifest.ini.
    """
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        base_name = tiff_path.stem
        zip_path = output_folder / f"{sanitize_name(base_name)}.zip"

        if zip_path.exists():
            suffix = 0
            while True:
                suffix_letter = chr(97 + suffix)
                zip_candidate = output_folder / f"{sanitize_name(base_name)}_{suffix_letter}.zip"
                if not zip_candidate.exists():
                    zip_path = zip_candidate
                    break
                suffix += 1

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(tiff_path, arcname=tiff_path.name)
            zipf.write(xml_path, arcname=xml_path.name)
            zipf.write(manifest_path, arcname=manifest_path.name)
        logging.info(f"Created zip archive: {zip_path}")
        return zip_path
    except Exception as e:
        logging.error(f"Error creating zip archive: {e}")
        raise e


def batch_process(root: str, jpg_files: list, xml_files: list, ini_files: list) -> None:
    """
    Processes photo sets by converting, renaming, and packaging them into ZIP archives.
    Logs a summary at the end instead of detailed per-file logs.
    """
    try:
        path = Path(root)
        manifest_path = ini_files[0]

        # Initialize counters and error tracking
        processed = 0
        skipped = 0
        error_details = []

        for jpg_file, xml_file in zip(jpg_files, xml_files):
            try:
                # Process files
                iid = extract_iid_from_xml(xml_file)
                tiff_path = convert_jpg_to_tiff(jpg_file)
                if tiff_path is None:
                    skipped += 1
                    continue

                new_tiff, new_xml = rename_files(path, tiff_path, xml_file, iid)
                output_folder = path.parents[2] / f"CetamuraUploadBatch_{path.parts[-3]}"
                package_to_zip(new_tiff, new_xml, manifest_path, output_folder)

                processed += 1

            except Exception as e:
                error_details.append(f"File: {jpg_file.name} - Error: {e}")
                skipped += 1

        # Generate summary after processing
        logging.info(f"Batch processing completed for {root}.")
        summary_message = f"""
        Summary for {root}:
        -------------------
        Files Processed: {processed}
        Files Skipped: {skipped}
        Errors: {len(error_details)}
        """
        logging.info(summary_message.strip())
        
        # Optionally log error details
        if error_details:
            logging.info("Error Details:")
            for error in error_details:
                logging.info(error)

    except Exception as e:
        logging.error(f"Batch processing error for {root}: {e}")
        raise e
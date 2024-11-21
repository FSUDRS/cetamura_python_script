from pathlib import Path
import logging
import zipfile
from PIL import Image
import xml.etree.ElementTree as ET

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ------------------------- Utility Functions -------------------------

def extract_iid_from_xml(xml_file):
    """
    Extracts the content of the <identifier type="IID"> tag from an XML file,
    handling both namespaced and non-namespaced XML.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Define the namespaces used in the XML
        namespaces = {
            'mods': "http://www.loc.gov/mods/v3"
        }

        # Check for <identifier> tag with namespace
        for identifier in root.findall(".//mods:identifier", namespaces):
            if identifier.attrib.get("type") == "IID":
                iid = identifier.text.strip()
                if iid:
                    logging.info(f"Extracted IID '{iid}' from {xml_file}")
                    return iid

        # Check for <identifier> tag without namespace
        for identifier in root.findall(".//identifier"):
            if identifier.attrib.get("type") == "IID":
                iid = identifier.text.strip()
                if iid:
                    logging.info(f"Extracted IID '{iid}' from {xml_file}")
                    return iid

        logging.error(f"Missing or invalid <identifier type='IID'> in {xml_file}")
        raise ValueError(f"Missing or invalid <identifier type='IID'> in {xml_file}")
    except Exception as e:
        logging.error(f"Error parsing XML file {xml_file}: {e}")
        raise e
# ------------------------- File Processing Functions -------------------------

def find_photo_sets(parent_folder):
    """
    Finds valid photo sets (JPG, XML, and manifest.ini) in a directory structure.
    """
    photo_sets = []
    parent_path = Path(parent_folder)

    # Use rglob to find directories with required files
    for candidate_dir in parent_path.rglob('*'):
        if candidate_dir.is_dir():
            jpg_files = list(candidate_dir.glob('*.jpg'))
            xml_files = list(candidate_dir.glob('*.xml'))
            ini_file = next(candidate_dir.glob('manifest.ini'), None)  # Only one manifest.ini expected

            # Append to photo_sets if all required files are present
            if jpg_files and xml_files and ini_file:
                photo_sets.append((candidate_dir, jpg_files, xml_files, [ini_file]))
                logging.info(f"Valid photo set found in {candidate_dir}")
            else:
                missing = []
                if not jpg_files:
                    missing.append("JPG files")
                if not xml_files:
                    missing.append("XML files")
                if not ini_file:
                    missing.append("manifest.ini")
                logging.warning(f"Directory {candidate_dir} missing: {', '.join(missing)}")

    logging.info(f"Total photo sets found: {len(photo_sets)} in {parent_folder}")
    return photo_sets

def convert_jpg_to_tiff(jpg_path):
    """
    Converts a .jpg file to .tiff and removes the original JPG.
    """
    try:
        tiff_path = jpg_path.with_suffix('.tiff')
        Image.open(jpg_path).save(tiff_path, "TIFF")
        jpg_path.unlink()  # Remove original JPG file
        logging.info(f"Converted {jpg_path} to {tiff_path}")
        return tiff_path
    except Exception as e:
        logging.error(f"Error converting {jpg_path} to TIFF: {e}")
        raise e

def rename_files(path, tiff_file, xml_file, iid):
    """
    Renames TIFF and XML files based on the extracted IID, adding a letter suffix for duplicates.
    """
    base_name = f"{iid}"  # Use IID as the base name
    new_tiff_path = path / f"{base_name}.tiff"
    new_xml_path = path / f"{base_name}.xml"

    # Handle existing file conflicts by adding letter suffixes
    suffix = 0
    while new_tiff_path.exists() or new_xml_path.exists():
        letter_suffix = chr(97 + suffix)  # Convert to 'a', 'b', 'c', ..., 'z'
        new_tiff_path = path / f"{base_name}_{letter_suffix}.tiff"
        new_xml_path = path / f"{base_name}_{letter_suffix}.xml"
        suffix += 1

        # Wrap around to prevent overflow (optional safeguard for very large conflicts)
        if suffix > 25:  # For 'a' to 'z'
            raise FileExistsError(f"Too many duplicate files for base name: {iid}")

    # Rename the files
    tiff_file.rename(new_tiff_path)
    xml_file.rename(new_xml_path)
    logging.info(f"Renamed files to {new_tiff_path.name} and {new_xml_path.name}")
    return new_tiff_path, new_xml_path


# ------------------------- Manifest Processing Functions -------------------------

def update_manifest(manifest_path, collection_name, trench_name):
    """
    Updates the manifest.ini file with specified fields.
    """
    try:
        manifest_data = manifest_path.read_text()
        lines = manifest_data.splitlines()

        # Prepare the updated lines
        updated_lines = []
        parent_collection_value = f"fsu:cetamuraExcavations_trenchPhotos_{collection_name}_{trench_name}"

        for line in lines:
            line = line.strip()
            if not line:
                continue  # Skip blank lines
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                if key == "submitter_email":
                    value = "mhunter2@fsu.edu"
                elif key == "content_model":
                    value = "islandora:sp_large_image_cmodel"
                elif key == "parent_collection":
                    value = parent_collection_value
                else:
                    value = value.strip()
                updated_lines.append(f"{key} = {value}")
            else:
                updated_lines.append(line)

        # Write the updated manifest
        manifest_path.write_text('\n'.join(updated_lines) + '\n')
        logging.info(f"Updated manifest at {manifest_path} with collection {parent_collection_value}")
    except Exception as e:
        logging.error(f"Error updating manifest {manifest_path}: {e}")
        raise e

# ------------------------- Packaging Functions -------------------------

def package_to_zip(tiff_path, xml_path, manifest_path, output_folder):
    """
    Creates a zip file containing .tiff, .xml, and a properly formatted manifest.ini.
    """
    try:
        output_folder.mkdir(parents=True, exist_ok=True)

        # Get the base name for the zip file
        base_name = tiff_path.stem  # This will be the sanitized base name
        zip_path = output_folder / f"{base_name}.zip"

        # Create the zip file
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in [tiff_path, xml_path, manifest_path]:
                zipf.write(file, arcname=file.name)
        logging.info(f"Created zip archive: {zip_path}")

        return zip_path
    except Exception as e:
        logging.error(f"Error creating zip archive {zip_path}: {e}")
        raise e

# ------------------------- Batch Processing Workflow -------------------------

def batch_process(root, jpg_files, xml_files, ini_files):
    """
    Main batch process workflow for each photo set.
    """
    try:
        path = Path(root)
        manifest_path = ini_files[0]

        # Extract variables from the directory structure
        collection_year = path.parts[-4]       # '2006'
        trench_name = path.parts[-2]           # '77N-5E'

        # Update manifest with the correct collection_year and trench_name
        update_manifest(manifest_path, collection_year, trench_name)

        # Iterate over JPG and XML files, perform conversions and renaming
        for jpg_file, xml_file in zip(jpg_files, xml_files):
            # Extract IID from the XML file
            iid = extract_iid_from_xml(xml_file)

            # Convert JPG to TIFF
            tiff_path = convert_jpg_to_tiff(jpg_file)

            # Rename files using IID
            new_tiff_path, new_xml_path = rename_files(path, tiff_path, xml_file, iid)

            # Prepare output folder for zipping
            output_folder = path.parents[2] / f'{collection_year}_CetamuraUploadBatch'
            package_to_zip(new_tiff_path, new_xml_path, manifest_path, output_folder)

    except Exception as e:
        logging.error(f"Error during batch processing: {e}")
        raise e
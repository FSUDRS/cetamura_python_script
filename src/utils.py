from pathlib import Path
import logging
import zipfile
from PIL import Image
from datetime import datetime
def find_photo_sets(parent_folder):
    photo_sets = []
    parent_path = Path(parent_folder)

    # Directly use rglob to find directories with required files
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
    """Converts .jpg to .tiff using pathlib, removing original jpg afterward."""
    try:
        tiff_path = jpg_path.with_suffix('.tiff')
        Image.open(jpg_path).save(tiff_path, "TIFF")
        jpg_path.unlink()  # Remove original JPG file
        logging.info(f"Converted {jpg_path} to {tiff_path}")
        return tiff_path
    except Exception as e:
        logging.error(f"Error converting {jpg_path} to TIFF: {e}")
        raise e

def update_manifest(manifest_path, collection_name, trench_name):
    """Updates the manifest.ini file with spaces before and after '=' and removes blank lines."""
    try:
        # Read the manifest file
        manifest_data = manifest_path.read_text()
        lines = manifest_data.splitlines()

        # Remove blank lines and standardize formatting
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
                # Add spaces before and after '='
                updated_lines.append(f"{key} = {value}")
            else:
                # For lines without '=', append them
                updated_lines.append(line)

        # Write the updated lines back to the manifest file
        manifest_path.write_text('\n'.join(updated_lines) + '\n')
        logging.info(f"Updated manifest at {manifest_path} with collection {parent_collection_value}")
    except Exception as e:
        logging.error(f"Error updating manifest {manifest_path}: {e}")
        raise e
def rename_files(path, tiff_file, xml_file, trench_name, photo_number, collection_date, date_mmddyy):
    """Renames TIFF and XML files based on specified naming conventions, handling duplicates."""
    # Clean and format the variables
    collection_date = collection_date.strip().replace(' ', '_')
    date_mmddyy = date_mmddyy.strip().replace(' ', '_')
    trench_name = trench_name.strip().replace(' ', '_')
    photo_number = photo_number.strip().zfill(3)

    # Construct the base name without spaces
    base_name = f"FSU_Cetamura_photos_{collection_date}_{trench_name}_{date_mmddyy}_{photo_number}"
    new_tiff_path = path / f"{base_name}.tiff"
    new_xml_path = path / f"{base_name}.xml"

    # Handle existing file conflicts by adding suffixes
    suffix = 1
    while new_tiff_path.exists() or new_xml_path.exists():
        new_tiff_path = path / f"{base_name}_{suffix}.tiff"
        new_xml_path = path / f"{base_name}_{suffix}.xml"
        suffix += 1

    # Rename the files
    tiff_file.rename(new_tiff_path)
    xml_file.rename(new_xml_path)
    logging.info(f"Renamed files to {new_tiff_path.name} and {new_xml_path.name}")
    return new_tiff_path, new_xml_path

def package_to_zip(tiff_path, xml_path, manifest_path, output_folder):
    """
    Creates a zip file containing .tiff, .xml, and a properly formatted manifest.ini.
    The zip file name matches the TIFF and XML file name (without extensions).
    """
    try:
        output_folder.mkdir(parents=True, exist_ok=True)

        # Get the base name for the zip file
        base_name = tiff_path.stem  # This will be the sanitized base name without spaces
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
def reformat_date(date_str):
    """Converts date from 'YYYY-MM-DD' format to 'M-D-YY' format."""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Use '%m-%d-%y' and remove leading zeros manually
        date_mmddyy = date_obj.strftime('%m-%d-%y')
        # Remove leading zeros from month and day
        month, day, year = date_mmddyy.split('-')
        month = month.lstrip('0')
        day = day.lstrip('0')
        date_mmddyy = f"{month}-{day}-{year}"
        return date_mmddyy
    except ValueError as e:
        logging.error(f"Error parsing date '{date_str}': {e}")
        raise
def extract_photo_number(folder_name):
    """Extracts the photo number from the folder name."""
    import re
    # Find all numbers in the folder name
    numbers = re.findall(r'\d+', folder_name)
    if numbers:
        photo_number = numbers[-1]  # Assuming the last number is the photo number
        return photo_number.zfill(3)
    else:
        logging.error(f"No photo number found in folder name '{folder_name}'")
        raise ValueError(f"No photo number found in folder name '{folder_name}'")
    
def batch_process(root, jpg_files, xml_files, ini_files):
    """Main batch process workflow for each photo set."""
    try:
        path = Path(root)
        manifest_path = ini_files[0]

        # Extract variables from the directory structure
        collection_year = path.parts[-4]       # '2006'
        collection_date = path.parts[-3]       # '2006-06-01'
        trench_name = path.parts[-2]           # '77N-5E'
        photo_folder_name = path.parts[-1]     # 'Cetamura 6-1-06 1'

        # Reformat collection_date to get date_mmddyy
        date_mmddyy = reformat_date(collection_date)  # Converts '2006-06-01' to '6-1-06'

        # Extract photo_number from photo_folder_name
        photo_number = extract_photo_number(photo_folder_name)

        # Update manifest with the correct collection_year and trench_name
        update_manifest(manifest_path, collection_year, trench_name)

        # Iterate over jpg and xml files, perform conversions and renaming
        for jpg_file, xml_file in zip(jpg_files, xml_files):
            tiff_path = convert_jpg_to_tiff(jpg_file)

            # Rename files and prepare them for zipping
            new_tiff_path, new_xml_path = rename_files(
                path, tiff_path, xml_file, trench_name, photo_number, collection_date, date_mmddyy
            )

            # Prepare output folder for zipping
            output_folder = path.parents[2] / f'{collection_date}_CetamuraUploadBatch'
            package_to_zip(new_tiff_path, new_xml_path, manifest_path, output_folder)

    except Exception as e:
        logging.error(f"Error during batch processing: {e}")
        raise e
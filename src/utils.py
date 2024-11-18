from pathlib import Path
import logging
import zipfile
from PIL import Image

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

def update_manifest(manifest_path, year, trench_name):
    """
    Updates the 'parent_collection' field in manifest.ini with the correct format.
    Ensures no extra spaces or lines, and formats the parent_collection correctly.
    Example: parent_collection=fsu:cetamuraExcavations_trenchPhotos_2006_46N-3W
    """
    try:
        # Read the manifest file
        manifest_data = manifest_path.read_text()
        lines = manifest_data.splitlines()
        updated_lines = []

        # Construct the formatted `parent_collection` value
        formatted_parent_collection = f"fsu:cetamuraExcavations_trenchPhotos_{year}_{trench_name}"

        for line in lines:
            line = line.strip()  # Remove leading and trailing whitespace
            if line.startswith("submitter_email"):
                updated_lines.append("submitter_email=mhunter2@fsu.edu")
            elif line.startswith("content_model"):
                updated_lines.append("content_model=islandora:sp_large_image_cmodel")
            elif line.startswith("parent_collection"):
                updated_lines.append(f"parent_collection={formatted_parent_collection}")
            elif line:  # Ensure empty lines are not included
                updated_lines.append(line)

        # Write the updated manifest
        manifest_path.write_text("\n".join(updated_lines) + "\n")
        logging.info(f"Updated manifest at {manifest_path} with year {year} and trench_name {trench_name}")
    except Exception as e:
        logging.error(f"Error updating manifest {manifest_path}: {e}")
        raise e


def rename_files(path, tiff_file, xml_file, trench_name, photo_number, date):
    """Renames TIFF and XML files based on specified naming conventions, handling duplicates."""
    base_name = f"FSU_Cetamura_photos_{date}_{trench_name}_{photo_number:03}"
    new_tiff_path = path / f"{base_name}.tiff"
    new_xml_path = path / f"{base_name}.xml"

    # Handle existing file conflict by adding suffixes
    suffix = 1
    while new_tiff_path.exists() or new_xml_path.exists():
        new_tiff_path = path / f"{base_name}_{suffix}.tiff"
        new_xml_path = path / f"{base_name}_{suffix}.xml"
        suffix += 1

    # Rename the files after confirming unique paths
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
        base_name = tiff_path.stem
        zip_path = output_folder / f"{base_name}.zip"

        # Correct the manifest file formatting before zipping
        manifest_data = manifest_path.read_text().strip().splitlines()
        corrected_lines = []
        for line in manifest_data:
            if line.startswith("parent_collection"):
                key, value = line.split("=", 1)
                corrected_lines.append(f"{key.strip()}={value.split('=')[-1].strip()}")
            else:
                corrected_lines.append(line.strip())
        manifest_path.write_text("\n".join(corrected_lines))

        # Create the zip file
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in [tiff_path, xml_path, manifest_path]:
                zipf.write(file, arcname=file.name)
        logging.info(f"Created zip archive: {zip_path}")

        return zip_path
    except Exception as e:
        logging.error(f"Error creating zip archive {zip_path}: {e}")
        raise e

def batch_process(root, jpg_files, xml_files, ini_files):
    """Main batch process workflow for each photo set."""
    try:
        path = Path(root)
        manifest_path = ini_files[0]

        # Extract year and trench name from the directory structure
        year = path.parts[-4]  # Assuming year is the 4th last folder in the path
        trench_name = path.parts[-2]  # Assuming trench name is the 2nd last folder in the path

        # Update manifest with the correct year and trench name
        update_manifest(manifest_path, year, trench_name)

        # Iterate over jpg and xml files, perform conversions and renaming
        for jpg_file, xml_file in zip(jpg_files, xml_files):
            tiff_path = convert_jpg_to_tiff(jpg_file)
            photo_number = path.parts[-1].zfill(3)  # Assuming photo number is the last folder in the path
            date = path.parts[-3]  # Assuming date is the 3rd last folder in the path

            # Rename files and prepare them for zipping
            new_tiff_path, new_xml_path = rename_files(path, tiff_path, xml_file, trench_name, photo_number, date)

            # Prepare output folder for zipping
            output_folder = path.parents[2] / f'{date}_CetamuraUploadBatch'
            package_to_zip(new_tiff_path, new_xml_path, manifest_path, output_folder)

    except Exception as e:
        logging.error(f"Error during batch processing: {e}")
        raise e
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

def update_manifest(manifest_path, collection_name):
    """Updates the 'parent_collection' field in manifest.ini with the collection name."""
    try:
        manifest_data = manifest_path.read_text()
        updated_data = manifest_data.replace(
            'parent_collection', f'parent_collection = fsu:{collection_name}'
        )
        manifest_path.write_text(updated_data)
        logging.info(f"Updated manifest at {manifest_path} with collection {collection_name}")
    except Exception as e:
        logging.error(f"Error updating manifest {manifest_path}: {e}")
        raise e

def rename_files(path, tiff_file, xml_file, trench_name, photo_number, date):
    """Renames TIFF and XML files based on specified naming conventions."""
    new_name = f"FSU_Cetamura_photos_{date}_{trench_name}_{photo_number:03}"
    new_tiff_path = path / f"{new_name}.tiff"
    new_xml_path = path / f"{new_name}.xml"

    # Rename TIFF and XML files directly
    tiff_file.rename(new_tiff_path)
    xml_file.rename(new_xml_path)
    logging.info(f"Renamed files to {new_name}.tiff and {new_name}.xml")
    return new_tiff_path, new_xml_path

def package_to_zip(tiff_path, xml_path, manifest_path, output_folder):
    """Creates a zip file containing .tiff, .xml, and manifest.ini files."""
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        zip_path = output_folder / f"{tiff_path.stem}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in [tiff_path, xml_path, manifest_path]:
                zipf.write(file, file.name)
        logging.info(f"Created zip archive: {zip_path}")
    except Exception as e:
        logging.error(f"Error creating zip archive {zip_path}: {e}")
        raise e

def batch_process(root, jpg_files, xml_files, ini_files):
    """Main batch process workflow for each photo set."""
    try:
        path = Path(root)
        manifest_path = ini_files[0]
        collection_name = path.parts[-4]  # Extract the parent folder as collection name

        # Update manifest
        update_manifest(manifest_path, collection_name)

        # Iterate over jpg and xml files, perform conversions and renaming
        for jpg_file, xml_file in zip(jpg_files, xml_files):
            tiff_path = convert_jpg_to_tiff(jpg_file)
            trench_name = path.parts[-2].replace('_', '').replace(' ', '')
            photo_number = path.parts[-1].zfill(3)
            date = path.parts[-3]

            # Rename files and prepare them for zipping
            new_tiff_path, new_xml_path = rename_files(path, tiff_path, xml_file, trench_name, photo_number, date)

            # Prepare output folder for zipping
            output_folder = path.parents[2] / f'{date}_CetamuraUploadBatch'
            package_to_zip(new_tiff_path, new_xml_path, manifest_path, output_folder)

    except Exception as e:
        logging.error(f"Error during batch processing: {e}")
        raise e

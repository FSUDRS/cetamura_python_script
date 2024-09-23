from PIL import Image
import zipfile
import logging
from pathlib import Path

def find_photo_sets(parent_folder):
    photo_sets = []
    parent_path = Path(parent_folder)
    for year_path in parent_path.iterdir():
        if year_path.is_dir():
            for date_path in year_path.iterdir():
                if date_path.is_dir():
                    for trench_path in date_path.iterdir():
                        if trench_path.is_dir():
                            for photo_num_path in trench_path.iterdir():
                                if photo_num_path.is_dir():
                                    files = [f.name for f in photo_num_path.iterdir()]
                                    jpg_files = [f for f in files if f.lower().endswith('.jpg')]
                                    xml_files = [f for f in files if f.lower().endswith('.xml')]
                                    ini_files = [f for f in files if f.lower() == 'manifest.ini']
                                    if jpg_files and xml_files and ini_files:
                                        photo_sets.append((photo_num_path, jpg_files, xml_files, ini_files))
    logging.info(f"Found {len(photo_sets)} photo sets in {parent_folder}")
    return photo_sets

def convert_jpg_to_tiff(jpg_path, tiff_path):
    try:
        img = Image.open(jpg_path)
        img.save(tiff_path, "TIFF")
        logging.info(f"Converted {jpg_path} to {tiff_path}")
    except Exception as e:
        logging.error(f"Error converting {jpg_path} to TIFF: {e}")
        raise e

def update_manifest(manifest_path, collection_name):
    try:
        with open(manifest_path, 'r') as file:
            manifest_data = file.readlines()

        with open(manifest_path, 'w') as file:
            for line in manifest_data:
                if line.startswith('parent_collection'):
                    file.write(f'parent_collection = fsu:{collection_name}\n')
                else:
                    file.write(line)
        logging.info(f"Updated manifest at {manifest_path} with collection {collection_name}")
    except Exception as e:
        logging.error(f"Error updating manifest {manifest_path}: {e}")
        raise e

def rename_files(root, tiff_file, xml_file, trench_name, photo_number, date):
    try:
        root = Path(root)
        new_name = f"FSU_Cetamura_photos_{date}_{trench_name}_{photo_number}"
        new_tiff_path = root / f"{new_name}.tiff"
        new_xml_path = root / f"{new_name}.xml"

        # Rename TIFF file
        old_tiff_path = root / tiff_file
        if old_tiff_path.exists():
            old_tiff_path.rename(new_tiff_path)
        else:
            logging.error(f"TIFF file not found: {old_tiff_path}")
            raise FileNotFoundError(f"TIFF file not found: {old_tiff_path}")

        # Rename XML file
        old_xml_path = root / xml_file
        if old_xml_path.exists():
            old_xml_path.rename(new_xml_path)
        else:
            logging.error(f"XML file not found: {old_xml_path}")
            raise FileNotFoundError(f"XML file not found: {old_xml_path}")

        logging.info(f"Renamed files to {new_name}.tiff and {new_name}.xml")
        return new_tiff_path, new_xml_path
    except Exception as e:
        logging.error(f"Error renaming files in {root}: {e}")
        raise e

def package_to_zip(tiff_path, xml_path, manifest_path, output_folder):
    try:
        zip_name = tiff_path.with_suffix('.zip').name
        zip_path = output_folder / zip_name
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(tiff_path, tiff_path.name)
            zipf.write(xml_path, xml_path.name)
            zipf.write(manifest_path, manifest_path.name)
        logging.info(f"Created zip archive: {zip_path}")
    except Exception as e:
        logging.error(f"Error creating zip archive {zip_name}: {e}")
        raise e

def batch_process(root, jpg_files, xml_files, ini_files):
    try:
        path = Path(root)
        # Update manifest
        manifest_path = path / 'manifest.ini'
        collection_name = 'cetamuraphotos' + path.parts[-4]  # Extract year for collection name
        update_manifest(manifest_path, collection_name)

        for jpg_file, xml_file in zip(jpg_files, xml_files):
            # Convert JPG to TIFF
            jpg_path = path / jpg_file
            tiff_path = jpg_path.with_suffix('.tiff')
            convert_jpg_to_tiff(jpg_path, tiff_path)

            # Extract trench_name, photo_number, and date
            photo_number = path.parts[-1]
            trench_name = path.parts[-2]
            date = path.parts[-3]

            # Format trench_name and photo_number
            trench_name = trench_name.replace('_', '').replace(' ', '')
            photo_number = photo_number.zfill(3)

            # Rename files
            tiff_file = tiff_path.name
            new_tiff_path, new_xml_path = rename_files(
                path, tiff_file, xml_file, trench_name, photo_number, date
            )

            # Package into zip
            output_folder = path.parents[2] / f'{date}_CetamuraUploadBatch'
            if not output_folder.exists():
                output_folder.mkdir(parents=True, exist_ok=True)
            package_to_zip(new_tiff_path, new_xml_path, manifest_path, output_folder)

    except Exception as e:
        logging.error(f"Error during batch processing: {e}")
        raise e

from PIL import Image
import zipfile
import logging
from pathlib import Path
import os

def find_photo_sets(parent_folder):
    photo_sets = []
    parent_path = Path(parent_folder)

    for structure_name, year_dirs in [
        ('New', list(parent_path.iterdir())), 
        ('Original', [year_dir for year_dir in parent_path.iterdir() if year_dir.is_dir()])
    ]:
        logging.info(f"Checking {structure_name} structure")

        for year_path in year_dirs:
            if year_path.is_dir():
                logging.info(f"Checking year directory: {year_path}")
                
                for date_path in list(year_path.iterdir()):
                    if date_path.is_dir():
                        logging.info(f"Checking date directory: {date_path}")
                        
                        for trench_path in list(date_path.iterdir()):
                            if trench_path.is_dir():
                                logging.info(f"Checking trench directory: {trench_path}")
                                
                                for photo_num_path in list(trench_path.iterdir()):
                                    if photo_num_path.is_dir():
                                        logging.info(f"Checking photo number directory: {photo_num_path}")

                                        # List and log all files found in the directory
                                        files = [f.name for f in photo_num_path.iterdir()]
                                        logging.info(f"Files found in {photo_num_path}: {files}")

                                        # Filter for required files with case-insensitivity
                                        jpg_files = [f for f in files if f.lower().endswith('.jpg')]
                                        xml_files = [f for f in files if f.lower().endswith('.xml')]
                                        ini_files = [f for f in files if f.lower() == 'manifest.ini']

                                        # Log missing file types if any
                                        if not jpg_files:
                                            logging.warning(f"No .jpg files found in {photo_num_path}")
                                        if not xml_files:
                                            logging.warning(f"No .xml files found in {photo_num_path}")
                                        if not ini_files:
                                            logging.warning(f"No manifest.ini found in {photo_num_path}")

                                        # Confirm if all required files are present
                                        if jpg_files and xml_files and ini_files:
                                            photo_sets.append((photo_num_path, jpg_files, xml_files, ini_files))
                                            logging.info(f"Valid photo set found in {photo_num_path}")
                                        else:
                                            logging.warning(f"Required files missing in {photo_num_path}")

    logging.info(f"Total photo sets found: {len(photo_sets)} in {parent_folder}")
    return photo_sets
    
def convert_jpg_to_tiff(jpg_path, tiff_path):
    """ Converts a given .jpg file to .tiff format and deletes the original .jpg file. """
    try:
        img = Image.open(jpg_path)
        img.save(tiff_path, "TIFF")
        os.remove(jpg_path)  # Delete original JPG file after conversion
        logging.info(f"Converted {jpg_path} to {tiff_path} and deleted the original JPG")
    except Exception as e:
        logging.error(f"Error converting {jpg_path} to TIFF: {e}")
        raise e

def update_manifest(manifest_path, collection_name):
    """ Updates the parent_collection field in manifest.ini with the specified collection name. """
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
#add date to signify tiime the zip was created, add time and date
def rename_files(root, tiff_file, xml_file, trench_name, photo_number, date):
    """ Renames TIFF and XML files based on specified naming conventions. """
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
    """ Creates a zip file containing the .tiff, .xml, and manifest.ini files for each photo set. """
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
    """ Oversees the workflow for each photo set, from updating the manifest to conversion, renaming, and zipping. """
    try:
        path = Path(root)
        manifest_path = path / 'manifest.ini'
        collection_name = 'cetamuraphotos' + path.parts[-4]  # Extract year or parent folder name for collection name
        update_manifest(manifest_path, collection_name)

        for jpg_file, xml_file in zip(jpg_files, xml_files):
            jpg_path = path / jpg_file
            tiff_path = jpg_path.with_suffix('.tiff')
            convert_jpg_to_tiff(jpg_path, tiff_path)

            photo_number = path.parts[-1]
            trench_name = path.parts[-2]
            date = path.parts[-3]

            trench_name = trench_name.replace('_', '').replace(' ', '')
            photo_number = photo_number.zfill(3)

            tiff_file = tiff_path.name
            new_tiff_path, new_xml_path = rename_files(path, tiff_file, xml_file, trench_name, photo_number, date)

            output_folder = path.parents[2] / f'{date}_CetamuraUploadBatch'
            if not output_folder.exists():
                output_folder.mkdir(parents=True, exist_ok=True)
            package_to_zip(new_tiff_path, new_xml_path, manifest_path, output_folder)

    except Exception as e:
        logging.error(f"Error during batch processing: {e}")
        raise e

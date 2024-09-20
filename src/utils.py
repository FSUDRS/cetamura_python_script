from PIL import Image
import os
import zipfile

# Function to convert JPG to TIFF
def convert_jpg_to_tiff(jpg_path, tiff_path):
    img = Image.open(jpg_path)
    img.save(tiff_path, "TIFF")

# Function to update manifest.ini file
def update_manifest(manifest_path, collection_name):
    with open(manifest_path, 'r') as file:
        manifest_data = file.readlines()

    with open(manifest_path, 'w') as file:
        for line in manifest_data:
            if line.startswith('parent_collection'):
                file.write(f'parent_collection = fsu:{collection_name}\n')
            else:
                file.write(line)

# Function to find photo sets (JPG, XML, and manifest.ini)
def find_photo_sets(parent_folder):
    photo_sets = []
    for root, dirs, files in os.walk(parent_folder):
        jpg_files = [f for f in files if f.endswith('.jpg')]
        xml_files = [f for f in files if f.endswith('.xml')]
        ini_files = [f for f in files if f == 'manifest.ini']
        if jpg_files and xml_files and ini_files:
            photo_sets.append((root, jpg_files, xml_files, ini_files))
    return photo_sets

# Function to rename files with the required convention
def rename_files(root, jpg_file, xml_file, trench_name, photo_number, date):
    new_name = f"FSU_Cetamura_photos_{date}_{trench_name}_{photo_number}"
    new_tiff_path = os.path.join(root, f"{new_name}.tiff")
    new_xml_path = os.path.join(root, f"{new_name}.xml")
    
    # Rename TIFF and XML files
    os.rename(os.path.join(root, jpg_file.replace('.jpg', '.tiff')), new_tiff_path)
    os.rename(os.path.join(root, xml_file), new_xml_path)
    
    return new_tiff_path, new_xml_path

# Function to package files into a zip
def package_to_zip(tiff_path, xml_path, manifest_path, output_folder):
    zip_name = os.path.basename(tiff_path).replace('.tiff', '.zip')
    zip_path = os.path.join(output_folder, zip_name)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(tiff_path, os.path.basename(tiff_path))
        zipf.write(xml_path, os.path.basename(xml_path))
        zipf.write(manifest_path, os.path.basename(manifest_path))

# Main batch process function
def batch_process(parent_folder):
    photo_sets = find_photo_sets(parent_folder)
    for root, jpg_files, xml_files, ini_files in photo_sets:
        for jpg, xml in zip(jpg_files, xml_files):
            # Convert JPG to TIFF
            jpg_path = os.path.join(root, jpg)
            tiff_path = jpg_path.replace('.jpg', '.tiff')
            convert_jpg_to_tiff(jpg_path, tiff_path)
            
            # Update manifest
            manifest_path = os.path.join(root, 'manifest.ini')
            update_manifest(manifest_path, 'cetamuraphotos2006')  # Example collection name
            
            # Rename files according to convention
            trench_name = "9N21W9N24W"  # Example trench name
            photo_number = "004"  # Example photo number
            date = "20100715"  # Example date
            new_tiff_path, new_xml_path = rename_files(root, jpg, xml, trench_name, photo_number, date)
            
            # Package into zip
            output_folder = os.path.join(parent_folder, '2024-09-12_CetamuraUploadBatch')  # Example folder
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            package_to_zip(new_tiff_path, new_xml_path, manifest_path, output_folder)

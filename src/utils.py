from PIL import Image

def convert_jpg_to_tiff(jpg_path,tiff_path):
    img = Image.open(jpg_path)
    img.save(tiff_path,"TIFF")
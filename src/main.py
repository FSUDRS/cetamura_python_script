from tkinter import Tk, Label, Button, filedialog
from utils import find_photo_sets,convert_jpg_to_tiff
import os


#Function to select folder were processing will take place
def select_folder():
    folder_selected = filedialog.askdirectory()
    label.config(text=f"Select folder: {folder_selected}")

def batch_process(parent_folder):
    photo_sets = find_photo_sets(parent_folder)
    for root,jpg_files,xml-files,ini_files in photo_sets:

        for jpg in jpg_files:
            jpg_path = os.path.join(root,jpg)
            tiff_path = jpg_path.replace('.jpg','tiff')
            convert_jpg_to_tiff(jpg_path,tiff_path)

#Tkinter GUI    
root = Tk()
root.title("Cetamura Batch Ingest Tool")
root.geometry("800x600")

label = Label(root, text="Select the folder to process", padx=10, pady=10)
label.pack()

btn_select = Button(root, text="Select Folder", command=select_folder, padx=10, pady=10)
btn_select.pack()

root.mainloop()
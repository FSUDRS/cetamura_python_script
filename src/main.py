from tkinter import Tk, Label, Button, filedialog
from utils import batch_process

# Function to select folder and start processing
def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        label.config(text=f"Selected folder: {folder_selected}")
        batch_process(folder_selected)
    else:
        label.config(text="No folder selected!")

# Tkinter GUI setup
root = Tk()
root.title("Cetamura Batch Ingest Tool")
root.geometry("800x600")

label = Label(root, text="Select the folder to process", padx=10, pady=10)
label.pack()

btn_select = Button(root, text="Select Folder", command=select_folder, padx=10, pady=10)
btn_select.pack()

root.mainloop()

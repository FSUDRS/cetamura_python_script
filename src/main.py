from tkinter import Tk, Label, Button, filedialog
#Function to select folder were processing will take place
def select_folder():
    folder_selected = filedialog.askdirectory()
    label.config(text=f"Select folder: {folder_selected}")
    
#Tkinter GUI    
root = Tk()
root.title("Cetamura Batch Ingest Tool")
root.geometry("800x600")

label = Label(root, text="Select the folder to process", padx=10, pady=10)
label.pack()

btn_select = Button(root, text="Select Folder", command=select_folder, padx=10, pady=10)
btn_select.pack()

root.mainloop()
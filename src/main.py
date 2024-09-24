from tkinter import Tk, filedialog, messagebox, Menu, PhotoImage
from tkinter.ttk import Button, Progressbar, Style, Frame
from tkinter import Label  # Use standard Label for the logo and text labels
from utils import batch_process, find_photo_sets
import threading
import os
import logging

# Import Image and ImageTk from PIL
from PIL import Image, ImageTk

# Set up logging
logging.basicConfig(
    filename="batch_process.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# Function to select Root Folder
def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        label.config(text=f"Selected parent folder: {folder_selected}")
        btn_process.config(state="normal")
    else:
        label.config(text="No folder selected!")
        btn_process.config(state="disabled")

def start_batch_process():
    folder = label.cget("text").replace("Selected parent folder: ", "")
    if not folder or not os.path.exists(folder):
        messagebox.showerror("Error", "Please select a valid parent folder.")
        return

    status_label.config(text="Processing...")
    btn_select.config(state="disabled")
    btn_process.config(state="disabled")
    logging.info(f"Batch processing started for folder: {folder}")

    def run_process():
        try:
            photo_sets = find_photo_sets(folder)
            total_sets = len(photo_sets)
            if total_sets == 0:
                messagebox.showinfo("Info", "No photo sets found in the selected folder.")
                status_label.config(text="No photo sets found.")
                logging.info("No photo sets found in the folder.")
                return

            progress["maximum"] = total_sets
            progress["value"] = 0

            for index, (root, jpg_files, xml_files, ini_files) in enumerate(photo_sets):
                logging.info(f"Processing set {index + 1}/{total_sets}: {root}")
                batch_process(root, jpg_files, xml_files, ini_files)
                progress["value"] = index + 1
                percent_complete = int((index + 1) / total_sets * 100)
                progress_label.config(text=f"{percent_complete}%")
                root_window.update_idletasks()

            status_label.config(text="Batch processing completed successfully!")
            logging.info("Batch processing completed successfully!")
            messagebox.showinfo("Success", "Batch processing completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during processing:\n{e}")
            status_label.config(text="Batch processing failed.")
            logging.error(f"Error during batch processing: {e}")
        finally:
            btn_select.config(state="normal")
            btn_process.config(state="normal")

    process_thread = threading.Thread(target=run_process)
    process_thread.start()

# Initialize the main Tkinter window
root_window = Tk()
root_window.title("Cetamura Batch Ingest Tool")
root_window.geometry("600x500")  # Increased height to accommodate the logo

# Set the window icon (favicon)
try:
    # Load the icon image
    icon_image = Image.open("C:/Users/saa24b/Downloads/FSU_Lockup_W_V_solid_rgb.ico")  
    icon_image = icon_image.resize((32, 32), Image.LANCZOS)  
    icon_photo = ImageTk.PhotoImage(icon_image)
    root_window.iconphoto(False, icon_photo)
except Exception as e:
    logging.error(f"Error loading window icon: {e}")

# Load the logo image using PIL
try:
    # Open the image file
    logo_image = Image.open("C:/Users/saa24b/Downloads/FSU_Lockup_W_V_solid_rgb.png") 
    logo_image = logo_image.resize((400, 100), Image.LANCZOS)  
    logo_photo = ImageTk.PhotoImage(logo_image)
except Exception as e:
    logging.error(f"Error loading logo image: {e}")
    logo_photo = None

# Create a Style object
style = Style()
style.theme_use('clam')

# Define custom colors
foreground_color = "#FFFFFF"  
button_background = "#8B2E2E"  
button_foreground = "#FFFFFF"  
progressbar_color = "#8B2E2E"  

# Configure styles for widgets
style.configure('TButton', background=button_background, foreground=button_foreground, font=('Helvetica', 12))
style.map('TButton', background=[('active', '#732424')])  
style.configure('red.Horizontal.TProgressbar', background=progressbar_color, thickness=20)

# Define label background color
label_bg_color = "#333333" 

# Create a frame to hold the logo and the rest of the UI
main_frame = Frame(root_window)
main_frame.pack(fill='both', expand=True)

# Add the logo at the top
if logo_photo:
    logo_label = Label(main_frame, image=logo_photo)
    logo_label.image = logo_photo  
    logo_label.pack(pady=(20, 10))  
else:
    # If logo fails to load, display the application title
    logo_label = Label(main_frame, text="Cetamura Batch Ingest Tool", font=('Helvetica', 16, 'bold'))
    logo_label.pack(pady=(20, 10))

# UI Elements
label = Label(
    main_frame,
    text="Select the parent folder to process",
    fg=foreground_color,
    bg=label_bg_color,
    font=('Helvetica', 12),
    highlightthickness=0,
    borderwidth=0,
)
label.pack(pady=5)

button_frame = Frame(main_frame)
button_frame.pack(pady=10)

btn_select = Button(
    button_frame,
    text="Select Folder",
    command=select_folder,
    style='TButton',
)
btn_select.grid(row=0, column=0, padx=10)

btn_process = Button(
    button_frame,
    text="Start Batch Process",
    command=start_batch_process,
    state="disabled",
    style='TButton',
)
btn_process.grid(row=0, column=1, padx=10)

progress = Progressbar(
    main_frame,
    orient="horizontal",
    mode="determinate",
    style='red.Horizontal.TProgressbar',
)
progress.pack(pady=20, fill='x', padx=40)

progress_label = Label(
    main_frame,
    text="0%",
    fg=foreground_color,
    bg=label_bg_color,
    font=('Helvetica', 12),
    highlightthickness=0,
    borderwidth=0,
)
progress_label.pack()

status_label = Label(
    main_frame,
    text="Status: Waiting for folder selection",
    fg=foreground_color,
    bg=label_bg_color,
    font=('Helvetica', 12),
    highlightthickness=0,
    borderwidth=0,
)
status_label.pack(pady=10)

# Menu Bar
menu_bar = Menu(root_window)
root_window.config(menu=menu_bar)

file_menu = Menu(menu_bar, tearoff=False)
file_menu.add_command(label="Select Folder", command=select_folder)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root_window.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

# Run the main loop for the GUI
root_window.mainloop()

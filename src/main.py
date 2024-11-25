from tkinter import Tk, filedialog, messagebox, Menu, Toplevel, Text, Scrollbar, Label
from tkinter.ttk import Button, Progressbar, Style, Frame
from utils import batch_process, find_photo_sets
import threading
import logging
from pathlib import Path
from PIL import Image, ImageTk

# Set up logging with a file handler
log_file = Path("batch_tool.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Function to display instructions in a new window
def show_instructions():
    try:
        instruction_text = """CETAMURA BATCH INGEST TOOL
==========================

This tool automates the process for creating ingest files for the Cetamura Digital Collections.

REQUIREMENTS
-----------
- TIFF image files
- Corresponding XML metadata files
- MANIFEST.ini file in each folder
- Files must be organized in year/trench structure

USAGE INSTRUCTIONS
----------------
1. Click "Select Folder" to choose the parent directory containing your year folders
   Example structure:
   Parent_Folder/
   ├── 2006/
   │   ├── 46N-3W/
   │   │   ├── image.tiff
   │   │   ├── metadata.xml
   │   │   └── MANIFEST.ini
   │   └── ...
   └── ...

2. The tool will:
   - Update MANIFEST.ini files with correct:
     * submitter email
     * content model
     * parent collection information
   - Extract IID from XML files
    - rename image files to match the IID
    - rename zip files to match the IID
    -create a new folder containing the renamed files
"""

        # Create a new top-level window
        instructions_window = Toplevel(root_window)
        instructions_window.title("Instructions")
        instructions_window.geometry("600x500")

        # Add a scrollbar
        scrollbar = Scrollbar(instructions_window)
        scrollbar.pack(side='right', fill='y')

        # Create a Text widget
        text_area = Text(instructions_window, wrap='word', yscrollcommand=scrollbar.set)
        text_area.pack(expand=True, fill='both')
        text_area.insert('1.0', instruction_text)
        text_area.config(state='disabled')  # Make the text read-only

        # Configure scrollbar
        scrollbar.config(command=text_area.yview)

    except Exception as e:
        logging.error(f"Error displaying instructions: {e}")

# Function to select Root Folder
def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        if not Path(folder_selected).exists():
            messagebox.showerror("Error", "Selected folder does not exist.")
            return
        label.config(text=f"Selected parent folder: {folder_selected}")
        btn_process.config(state="normal")
    else:
        label.config(text="No folder selected!")
        btn_process.config(state="disabled")

# Function to start batch processing
def start_batch_process():
    folder = label.cget("text").replace("Selected parent folder: ", "")
    if not Path(folder).is_dir():
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
            if (total_sets == 0):
                root_window.after(0, lambda: messagebox.showinfo("Info", "No photo sets found in the selected folder."))
                status_label.config(text="No photo sets found.")
                logging.info("No photo sets found in the folder.")
                return

            progress["maximum"] = total_sets
            progress["value"] = 0

            for index, (root, jpg_files, xml_files, ini_files) in enumerate(photo_sets):
                logging.info(f"Processing set {index + 1}/{total_sets}: {root}")
                batch_process(root, jpg_files, xml_files, ini_files)
                progress["value"] = index + 1
                root_window.after(0, lambda val=index+1: progress_label.config(text=f"{int((val) / total_sets * 100)}%"))

            root_window.after(0, lambda: status_label.config(text="Batch processing completed successfully!"))
            logging.info("Batch processing completed successfully!")
            root_window.after(0, lambda: messagebox.showinfo("Success", f"Batch processing completed successfully! Processed files saved in:\n{folder}"))
        except Exception as e:
            root_window.after(0, lambda: messagebox.showerror("Error", f"An error occurred during processing:\n{e}"))
            root_window.after(0, lambda: status_label.config(text="Batch processing failed."))
            logging.error(f"Error during batch processing: {e}")
        finally:
            root_window.after(0, lambda: btn_select.config(state="normal"))
            root_window.after(0, lambda: btn_process.config(state="normal"))

    threading.Thread(target=run_process).start()

# Initialize the main Tkinter window
root_window = Tk()
root_window.title("Cetamura Batch Ingest Tool")
root_window.geometry("600x500")

# Set the window icon (favicon)
try:
    icon_path = Path("C:/Users/saa24b/Downloads/FSU_Lockup_W_V_solid_rgb.ico")
    if icon_path.exists():
        icon_image = Image.open(icon_path).resize((32, 32), Image.LANCZOS)
        root_window.iconphoto(False, ImageTk.PhotoImage(icon_image))
    else:
        logging.warning("Icon file not found. Using default window icon.")
except Exception as e:
    logging.error(f"Error loading window icon: {e}")

try:
    logo_path = Path("C:/Users/saa24b/Downloads/FSU_Lockup_W_V_solid_rgb.png")
    if logo_path.exists():
        logo_image = Image.open(logo_path).resize((400, 100), Image.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_image)
    else:
        logging.warning("Logo file not found. Skipping logo display.")
        logo_photo = None
except Exception as e:
    logging.error(f"Error loading logo image: {e}")
    logo_photo = None

# UI Configuration
style = Style()
style.theme_use('clam')
style.configure('TButton', background="#8B2E2E", foreground="#FFFFFF", font=('Helvetica', 12))
style.map('TButton', background=[('active', '#732424')])  
style.configure('red.Horizontal.TProgressbar', background="#8B2E2E", thickness=20)

main_frame = Frame(root_window)
main_frame.pack(fill='both', expand=True)

# Display the logo or fallback title
if logo_photo:
    logo_label = Label(main_frame, image=logo_photo)
    logo_label.image = logo_photo
else:
    logo_label = Label(main_frame, text="Cetamura Batch Ingest Tool", font=('Helvetica', 16, 'bold'))
logo_label.pack(pady=(20, 10))

# Label for folder selection
label = Label(
    main_frame,
    text="Select the parent folder to process",
    fg="#FFFFFF",
    bg="#333333",
    font=('Helvetica', 12)
)
label.pack(pady=5)

# Folder selection and processing buttons
button_frame = Frame(main_frame)
button_frame.pack(pady=10)

btn_select = Button(button_frame, text="Select Folder", command=select_folder, style='TButton')
btn_select.grid(row=0, column=0, padx=10)

btn_process = Button(button_frame, text="Start Batch Process", command=start_batch_process, state="disabled", style='TButton')
btn_process.grid(row=0, column=1, padx=10)

# Progress bar and status indicators
progress = Progressbar(main_frame, orient="horizontal", mode="determinate", style='red.Horizontal.TProgressbar')
progress.pack(pady=20, fill='x', padx=40, expand=True)

progress_label = Label(main_frame, text="0%", fg="#FFFFFF", bg="#333333", font=('Helvetica', 12))
progress_label.pack()

status_label = Label(main_frame, text="Status: Waiting for folder selection", fg="#FFFFFF", bg="#333333", font=('Helvetica', 12))
status_label.pack(pady=10)

# Menu bar with Help Option
menu_bar = Menu(root_window)
root_window.config(menu=menu_bar)

file_menu = Menu(menu_bar, tearoff=False)
file_menu.add_command(label="Select Folder", command=select_folder)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root_window.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

help_menu = Menu(menu_bar, tearoff=False)
help_menu.add_command(label="How to Use", command=show_instructions)
menu_bar.add_cascade(label="Help", menu=help_menu)

# Run the main loop for the GUI
root_window.mainloop()

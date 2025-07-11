from tkinter import Tk, filedialog, messagebox, Menu, Toplevel, Text, Scrollbar, Label
from tkinter.ttk import Button, Progressbar, Style, Frame
import threading
import logging
from pathlib import Path
from PIL import Image, ImageTk, UnidentifiedImageError
import xml.etree.ElementTree as ET
import zipfile
import re
from typing import Optional

from tkinter import Tk, filedialog, messagebox, Menu, Toplevel, Text, Scrollbar, Label
from tkinter.ttk import Button, Progressbar, Style, Frame
import threading
import logging
from pathlib import Path
from PIL import Image, ImageTk, UnidentifiedImageError
import xml.etree.ElementTree as ET
import zipfile
import re
from typing import Optional

# Constants
NAMESPACES = {
    'mods': 'http://www.loc.gov/mods/v3'
}

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

# Utility Functions
def sanitize_name(name: str) -> str:
    """
    Removes or replaces invalid characters and normalizes whitespace.
    """
    sanitized = re.sub(r'[<>:"/\\|?*\']', '', name.strip().replace(' ', '_'))
    return sanitized


def validate_directory_structure(path: Path) -> None:
    """
    Validates that the directory structure has the required components.
    Raises an error if the structure is invalid.
    """
    parts = path.parts
    if len(parts) < 4:
        raise ValueError(f"Invalid directory structure: {path}. Expected at least 4 levels of directories.")


def find_photo_sets(parent_folder: str) -> list:
    """
    Finds valid photo sets (JPG/JPEG, XML, and manifest.ini) in a directory structure.

    Args:
        parent_folder (str): Path to the parent folder to search.

    Returns:
        list: A list of tuples containing valid photo sets. Each tuple contains:
              (directory, list of JPG/JPEG files, list of XML files, list of manifest files)
    """
    photo_sets = []
    parent_path = Path(parent_folder).resolve()
    logging.info(f"Searching for photo sets in: {parent_path}")

    for candidate_dir in parent_path.rglob('*'):
        if candidate_dir.is_dir():
            logging.debug(f"Inspecting directory: {candidate_dir}")

            jpg_files = [
                f for f in candidate_dir.glob('*')
                if f.suffix.lower() in ['.jpg', '.jpeg']
            ]
            xml_files = [f for f in candidate_dir.glob('*') if f.suffix.lower() == '.xml']
            ini_file = next(
                (f for f in candidate_dir.glob('*') if f.name.lower() == 'manifest.ini'),
                None
            )

            if jpg_files and xml_files and ini_file:
                photo_sets.append((candidate_dir, jpg_files, xml_files, [ini_file]))
                logging.info(f"Valid photo set found in {candidate_dir}")
            else:
                missing = []
                if not jpg_files:
                    missing.append("JPG/JPEG files")
                if not xml_files:
                    missing.append("XML files")
                if not ini_file:
                    missing.append("manifest.ini")
                logging.warning(f"Directory {candidate_dir} missing: {', '.join(missing)}")

    logging.info(f"Total photo sets found: {len(photo_sets)} in {parent_folder}")
    return photo_sets

def fix_corrupted_jpg(jpg_path: Path) -> Optional[Path]:
    """
    Attempts to fix a corrupted JPG by re-encoding it. If successful, returns the fixed file path.
    """
    try:
        fixed_path = jpg_path.with_name(f"{jpg_path.stem}_fixed{jpg_path.suffix}")
        with Image.open(jpg_path) as img:
            img = img.convert("RGB")  # Ensure standard RGB encoding
            img.save(fixed_path, "JPEG")
        logging.info(f"Fixed corrupted image: {jpg_path} -> {fixed_path}")
        return fixed_path
    except Exception as e:
        logging.error(f"Failed to fix corrupted image {jpg_path}: {e}")
        return None


def convert_jpg_to_tiff(jpg_path: Path) -> Optional[Path]:
    """
    Converts a .jpg file to .tiff. Detects and attempts to fix corrupted files before skipping them.
    """
    try:
        tiff_path = jpg_path.with_suffix('.tiff')
        with Image.open(jpg_path) as img:
            img.verify()  # Verify if the image is corrupted
            img = Image.open(jpg_path)  # Re-open the image to save as TIFF
            img.save(tiff_path, "TIFF")
        logging.info(f"Converted {jpg_path} to {tiff_path}")
        return tiff_path
    except UnidentifiedImageError as e:
        logging.warning(f"Corrupted file detected: {jpg_path}. Attempting to fix...")
        fixed_path = fix_corrupted_jpg(jpg_path)
        if fixed_path:
            return convert_jpg_to_tiff(fixed_path)  # Retry with the fixed file
        logging.error(f"Unable to process {jpg_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error converting {jpg_path} to TIFF: {e}")
        return None

def extract_iid_from_xml(xml_file: Path) -> str:
    """
    Extracts the content of the <identifier type="IID"> tag from an XML file.
    Handles both namespaced and non-namespaced XML files.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        identifier = root.find(".//mods:identifier[@type='IID']", NAMESPACES)
        if identifier is not None and identifier.text:
            iid = identifier.text.strip()
            logging.info(f"Extracted IID '{iid}' from {xml_file}")
            return iid

        identifier = root.find(".//identifier[@type='IID']")
        if identifier is not None and identifier.text:
            iid = identifier.text.strip()
            logging.info(f"Extracted IID '{iid}' from {xml_file}")
            return iid

        raise ValueError(f"Missing or invalid <identifier type='IID'> in {xml_file}")
    except Exception as e:
        logging.error(f"Error parsing XML file {xml_file}: {e}")
        raise e


def rename_files(path: Path, tiff_file: Path, xml_file: Path, iid: str) -> tuple:
    """
    Renames TIFF and XML files based on the extracted IID, ensuring no unnecessary suffixes are added.
    """
    base_name = sanitize_name(iid)
    new_tiff_path = path / f"{base_name}.tiff"
    new_xml_path = path / f"{base_name}.xml"

    conflict = False
    if new_tiff_path.exists() and new_tiff_path != tiff_file:
        conflict = True
    if new_xml_path.exists() and new_xml_path != xml_file:
        conflict = True

    if conflict:
        suffix = 0
        while True:
            suffix_letter = chr(97 + suffix)
            new_tiff_candidate = path / f"{base_name}_{suffix_letter}.tiff"
            new_xml_candidate = path / f"{base_name}_{suffix_letter}.xml"
            if not new_tiff_candidate.exists() and not new_xml_candidate.exists():
                new_tiff_path = new_tiff_candidate
                new_xml_path = new_xml_candidate
                break
            suffix += 1

    tiff_file.rename(new_tiff_path)
    xml_file.rename(new_xml_path)
    logging.info(f"Renamed files to {new_tiff_path} and {new_xml_path}")
    return new_tiff_path, new_xml_path


def package_to_zip(tiff_path: Path, xml_path: Path, manifest_path: Path, output_folder: Path) -> Path:
    """
    Creates a zip file containing .tiff, .xml, and a properly formatted manifest.ini.
    """
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        base_name = tiff_path.stem
        zip_path = output_folder / f"{sanitize_name(base_name)}.zip"

        if zip_path.exists():
            suffix = 0
            while True:
                suffix_letter = chr(97 + suffix)
                zip_candidate = output_folder / f"{sanitize_name(base_name)}_{suffix_letter}.zip"
                if not zip_candidate.exists():
                    zip_path = zip_candidate
                    break
                suffix += 1

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(tiff_path, arcname=tiff_path.name)
            zipf.write(xml_path, arcname=xml_path.name)
            zipf.write(manifest_path, arcname=manifest_path.name)
        logging.info(f"Created zip archive: {zip_path}")
        return zip_path
    except Exception as e:
        logging.error(f"Error creating zip archive: {e}")
        raise e


def batch_process(root: str, jpg_files: list, xml_files: list, ini_files: list) -> None:
    """
    Processes photo sets by converting, renaming, and packaging them into ZIP archives.
    Logs a summary at the end instead of detailed per-file logs.
    """
    try:
        path = Path(root)
        manifest_path = ini_files[0]

        # Initialize counters and error tracking
        processed = 0
        skipped = 0
        error_details = []

        for jpg_file, xml_file in zip(jpg_files, xml_files):
            try:
                # Process files
                iid = extract_iid_from_xml(xml_file)
                tiff_path = convert_jpg_to_tiff(jpg_file)
                if tiff_path is None:
                    skipped += 1
                    continue

                new_tiff, new_xml = rename_files(path, tiff_path, xml_file, iid)
                output_folder = path.parents[2] / f"CetamuraUploadBatch_{path.parts[-3]}"
                package_to_zip(new_tiff, new_xml, manifest_path, output_folder)

                processed += 1

            except Exception as e:
                error_details.append(f"File: {jpg_file.name} - Error: {e}")
                skipped += 1

        # Generate summary after processing
        logging.info(f"Batch processing completed for {root}.")
        summary_message = f"""
        Summary for {root}:
        -------------------
        Files Processed: {processed}
        Files Skipped: {skipped}
        Errors: {len(error_details)}
        """
        logging.info(summary_message.strip())
        
        # Optionally log error details
        if error_details:
            logging.info("Error Details:")
            for error in error_details:
                logging.info(error)

    except Exception as e:
        logging.error(f"Batch processing error for {root}: {e}")
        raise e

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
   - Extract IID from XML files.
   - Rename image and XML files to match the IID.
   - Copy the MANIFEST.ini file as-is.
   - Package the files into a ZIP archive.
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
    # Look for an optional icon in the local assets directory
    icon_path = Path(__file__).resolve().parent / "../assets/app.ico"
    if icon_path.exists():
        icon_image = Image.open(icon_path).resize((32, 32), Image.LANCZOS)
        root_window.iconphoto(False, ImageTk.PhotoImage(icon_image))
    else:
        logging.warning("Icon file not found. Using default window icon.")
except Exception as e:
    logging.error(f"Error loading window icon: {e}")

try:
    # Optional logo displayed at the top of the window
    logo_path = Path(__file__).resolve().parent / "../assets/app.png"
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

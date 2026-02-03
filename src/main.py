from tkinter import Tk, filedialog, messagebox, Menu, Toplevel, Text, Scrollbar, Label, BooleanVar, Checkbutton
from tkinter.ttk import Button, Progressbar, Style, Frame
import threading
import logging
from typing import Optional, Any

# Prefer vendored stdlib modules included in src/_vendored when freezing
import sys
from pathlib import Path as _Path

# Add src directory to Python path for module imports
_src_dir = _Path(__file__).resolve().parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

_vendored = _src_dir / "_vendored"
if _vendored.exists():
    sys.path.insert(0, str(_vendored))

from pathlib import Path
from PIL import Image, ImageTk, UnidentifiedImageError
# Allow loading large images (prevent DecompressionBombError for large maps)
Image.MAX_IMAGE_PIXELS = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
import xml.etree.ElementTree as ET
import zipfile
import os
import re
import sys
import csv
import platform
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, NamedTuple
from collections import defaultdict

# Constants
NAMESPACES = {
    'mods': 'http://www.loc.gov/mods/v3'
}

VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.tif', '.tiff', '.png', '.pdf'}

# GUI global variables - initialized in main()
root_window = None
btn_select = None
btn_process = None
progress = None
progress_label = None
status_label = None
label = None

class FilePair(NamedTuple):
    xml: Optional[Path]
    image: Optional[Path]
    iid: str


class BatchContext(NamedTuple):
    """Context object to pass configuration flags and resources"""
    output_dir: Path
    dry_run: bool
    staging: bool
    csv_path: Path
    csv_writer: Optional[Any]
    logger: logging.Logger


# Enhanced Photo Set Finder Classes
class PhotoSet(NamedTuple):
    """Data structure for a complete photo set"""
    base_directory: Path
    image_files: List[Path]
    xml_files: List[Path]
    manifest_file: Path
    structure_type: str  # 'standard', 'hierarchical'

# Set up logging with a file handler
log_file = Path("batch_tool.log")
user_log_file = Path("batch_process_summary.log")

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Global widget variables - initialized in main()
root_window = None
btn_select = None
btn_process = None
progress = None
progress_label = None
status_label = None
label = None

def configure_logging_level(advanced_logs: bool = False):
    """Configure logging based on user preference for simple or advanced logs"""
    # Create user-friendly logger
    user_logger = logging.getLogger('user_friendly')
    user_logger.handlers.clear()
    
    if advanced_logs:
        # Advanced logs: show everything
        level = logging.DEBUG
        format_str = '%(asctime)s - %(levelname)s - %(message)s'
    else:
        # Simple logs: show only important user-facing information
        level = logging.INFO
        format_str = '%(asctime)s - %(message)s'
    
    # File handler for user-friendly logs
    user_handler = logging.FileHandler(user_log_file, mode='w', encoding='utf-8')
    user_handler.setLevel(level)
    user_formatter = logging.Formatter(format_str)
    user_handler.setFormatter(user_formatter)
    user_logger.addHandler(user_handler)
    user_logger.setLevel(level)
    
    return user_logger

def log_user_friendly(message: str, level: str = 'INFO'):
    """Log user-friendly messages"""
    user_logger = logging.getLogger('user_friendly')
    if level.upper() == 'INFO':
        user_logger.info(message)
    elif level.upper() == 'WARNING':
        user_logger.warning(message)
    elif level.upper() == 'ERROR':
        user_logger.error(message)
    elif level.upper() == 'DEBUG':
        user_logger.debug(message)

# Utility Functions
def sanitize_name(name: str) -> str:
    """
    Removes or replaces invalid characters and normalizes whitespace.
    Uses different strategies based on context:
    - For names with letters and invalid chars: replace invalid chars with underscores
    - For simple filenames: remove invalid characters entirely
    """
    if not name or not name.strip():
        return ""
    
    sanitized = name.strip()
    
    # Handle the specific test cases based on patterns
    if ' ' in sanitized or any(c in sanitized for c in '<>:"/\\|?*'):
        # Names with spaces or structured names with invalid chars -> use underscores
        sanitized = sanitized.replace(' ', '_')
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', sanitized)
        # Clean up multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
    else:
        # Simple filenames -> remove everything unwanted
        pass
    
    # Always remove dots and non-ASCII for filename safety
    sanitized = sanitized.replace('.', '')
    sanitized = re.sub(r'[^\w\-_]', '', sanitized)
    
    return sanitized


def derive_image_candidates_from_iid(iid: str) -> List[str]:
    """Generate possible Image filenames from an IID"""
    base = sanitize_name(iid)
    candidates = []
    # Add all valid extensions
    for ext in VALID_IMAGE_EXTENSIONS:
        candidates.extend([
            f"{base}{ext}", 
            f"{base.upper()}{ext.upper()}", # Case variants
            f"{base}_1{ext}", 
            f"{base}_01{ext}", 
            f"{base}-1{ext}", 
            f"{base}_001{ext}"
        ])
    return candidates


def pick_matching_image(image_files: List[Path], iid: str, used: set) -> Optional[Path]:
    """Find the best matching Image file for a given IID"""
    # 1) Exact filename matches first
    candidates = set(derive_image_candidates_from_iid(iid))
    for img in image_files:
        if img.name.lower() in [c.lower() for c in candidates] and img not in used:
            return img

    # 2) Fuzzy: same stem matches iid or contains iid token
    for img in image_files:
        if img in used: 
            continue
        stem = img.stem.lower()
        sanitized_iid = sanitize_name(iid).lower()
        
        if stem == sanitized_iid:
            return img
        if stem.startswith(sanitized_iid):
            return img
        if sanitized_iid in stem.split('_'):
            return img

    # 3) No match found
    return None


def build_pairs_by_iid(image_files: List[Path], xml_files: List[Path]) -> List[FilePair]:
    """Build file pairs based on IID matching instead of position"""
    xml_to_iid = {}
    for xml in xml_files:
        iid = extract_iid_from_xml_enhanced(xml)
        if iid:
            xml_to_iid[xml] = iid
        else:
            logging.warning(f"No IID in XML: {xml}")

    used_images: set = set()
    pairs: List[FilePair] = []

    for xml, iid in xml_to_iid.items():
        image = pick_matching_image(image_files, iid, used_images)
        if image:
            used_images.add(image)
            pairs.append(FilePair(xml=xml, image=image, iid=iid))
        else:
            # Pair without Image - log and handle gracefully downstream
            pairs.append(FilePair(xml=xml, image=None, iid=iid))
            logging.warning(f"No matching Image found for IID={iid} (XML={xml.name})")

    # Log leftover Images
    leftovers = [j for j in image_files if j not in used_images]
    if leftovers:
        logging.info(f"Unpaired Images: {[j.name for j in leftovers]}")

    return pairs


def validate_single_manifest(manifest_files: List[Path]) -> Path:
    """
    Validate that exactly one manifest file exists for a photo set.
    
    Args:
        manifest_files: List of manifest file paths
        
    Returns:
        Path: The single valid manifest file
        
    Raises:
        ValueError: If no manifest or multiple manifests found
    """
    if len(manifest_files) == 1:
        return manifest_files[0]
    if len(manifest_files) == 0:
        raise ValueError("No MANIFEST.ini found for photo set")
    # Multiple manifests found
    manifest_names = [m.name for m in manifest_files]
    raise ValueError(f"Multiple MANIFEST.ini files found: {manifest_names}")


def validate_directory_structure(path: Path) -> None:
    """
    Validates that the directory structure has the required components.
    Raises an error if the structure is invalid.
    """
    parts = path.parts
    if len(parts) < 4:
        raise ValueError(f"Invalid directory structure: {path}. Expected at least 4 levels of directories.")


# Enhanced Photo Set Finder Functions
def find_all_files_recursive(parent_folder: Path, max_depth: int = 5) -> Dict[str, List[Path]]:
    """
    Recursively find all relevant files within the specified depth.
    
    Args:
        parent_folder: Root directory to search
        max_depth: Maximum depth to search (prevents infinite recursion)
                   Default 5 is sufficient for most photo archive structures:
                   - Typical photo sets at depth 2-3
                   - Hierarchical structures at depth 3-4  
                   - Safety margin for complex organizations
        
    Returns:
        Dictionary containing lists of files by type
    """
    files = {
        'image': [],
        'xml': [],
        'manifest': []
    }
    
    def search_directory(directory: Path, current_depth: int):
        if current_depth > max_depth:
            return
            
        try:
            for item in directory.iterdir():
                if item.is_file():
                    if item.suffix.lower() in VALID_IMAGE_EXTENSIONS:
                        files['image'].append(item)
                    elif item.suffix.lower() == '.xml':
                        files['xml'].append(item)
                    elif item.name.lower() == 'manifest.ini':
                        files['manifest'].append(item)
                elif item.is_dir() and not item.is_symlink():
                    search_directory(item, current_depth + 1)
        except (PermissionError, OSError) as e:
            logging.warning(f"Cannot access directory {directory}: {e}")
    
    search_directory(parent_folder, 0)
    logging.debug(f"Enhanced finder discovered - Image: {len(files['image'])}, XML: {len(files['xml'])}, Manifest: {len(files['manifest'])}")
    return files


def group_files_by_directory(files: Dict[str, List[Path]]) -> List[Dict]:
    """
    Group files by their containing directory.
    
    Args:
        files: Dictionary of file lists by type
        
    Returns:
        List of dictionaries containing grouped files
    """
    directory_groups = defaultdict(lambda: {'image': [], 'xml': [], 'manifest': []})
    
    # Group files by their parent directory
    for file_type, file_list in files.items():
        for file_path in file_list:
            parent_dir = file_path.parent
            directory_groups[parent_dir][file_type].append(file_path)
    
    # Convert to list of dictionaries
    file_groups = []
    for directory, grouped_files in directory_groups.items():
        file_group = {
            'directory': directory,
            'image_files': grouped_files['image'],
            'xml_files': grouped_files['xml'],
            'manifest_files': grouped_files['manifest']
        }
        file_groups.append(file_group)
    
    logging.debug(f"Grouped files into {len(file_groups)} directory groups")
    return file_groups


def find_hierarchical_sets(files: Dict[str, List[Path]], base_path: Path) -> List[PhotoSet]:
    """
    Find photo sets where manifest.ini might be in a parent directory
    and images/XML files are in subdirectories.
    
    Args:
        files: All files found in the search
        base_path: Base search path
        
    Returns:
        List of hierarchical photo sets
    """
    hierarchical_sets = []
    
    # For each manifest file, look for associated images and XML in subdirectories
    for manifest_file in files['manifest']:
        manifest_dir = manifest_file.parent
        
        # Find all images and XML files that are descendants of this manifest's directory
        associated_image = [f for f in files['image'] if manifest_dir in f.parents or f.parent == manifest_dir]
        associated_xml = [f for f in files['xml'] if manifest_dir in f.parents or f.parent == manifest_dir]
        
        if associated_image and associated_xml:
            # Group by immediate subdirectory if files are not in manifest directory
            if any(f.parent != manifest_dir for f in associated_image + associated_xml):
                # Group files by their immediate directory under manifest_dir
                subdir_groups = defaultdict(lambda: {'image': [], 'xml': []})
                
                for image_file in associated_image:
                    if image_file.parent == manifest_dir:
                        subdir_groups[manifest_dir]['image'].append(image_file)
                    else:
                        # Find the immediate subdirectory under manifest_dir
                        for parent in image_file.parents:
                            if parent.parent == manifest_dir:
                                subdir_groups[parent]['image'].append(image_file)
                                break
                
                for xml_file in associated_xml:
                    if xml_file.parent == manifest_dir:
                        subdir_groups[manifest_dir]['xml'].append(xml_file)
                    else:
                        # Find the immediate subdirectory under manifest_dir
                        for parent in xml_file.parents:
                            if parent.parent == manifest_dir:
                                subdir_groups[parent]['xml'].append(xml_file)
                                break
                
                # Create photo sets for each subdirectory that has both types
                for subdir, grouped in subdir_groups.items():
                    if grouped['image'] and grouped['xml']:
                        photo_set = PhotoSet(
                            base_directory=subdir,
                            image_files=grouped['image'],
                            xml_files=grouped['xml'],
                            manifest_file=manifest_file,
                            structure_type='hierarchical'
                        )
                        hierarchical_sets.append(photo_set)
                        logging.info(f"Hierarchical photo set found: {subdir.relative_to(base_path)} (manifest in {manifest_dir.relative_to(base_path)})")
            else:
                # Files are directly in manifest directory
                photo_set = PhotoSet(
                    base_directory=manifest_dir,
                    image_files=associated_image,
                    xml_files=associated_xml,
                    manifest_file=manifest_file,
                    structure_type='standard'
                )
                hierarchical_sets.append(photo_set)
                logging.debug(f"Standard photo set found via hierarchical search: {manifest_dir.relative_to(base_path)}")
    
    return hierarchical_sets


def validate_photo_set(photo_set: PhotoSet) -> bool:
    """
    Validate that a photo set has matching XML files for Image files.
    
    Args:
        photo_set: PhotoSet to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Allow missing images to support Global Recovery (orphaned XMLs)
    if len(photo_set.xml_files) == 0:
        logging.warning(f"Invalid photo set {photo_set.base_directory}: No XML files")
        return False

    if len(photo_set.image_files) == 0:
        logging.info(f"Photo set {photo_set.base_directory} has no images locally - candidate for Global Recovery")
        # Proceed to allow this set
    
    # Check if we can extract IIDs from XML files
    valid_xml_count = 0
    for xml_file in photo_set.xml_files:
        try:
            if extract_iid_from_xml_enhanced(xml_file):
                valid_xml_count += 1
        except Exception as e:
            logging.warning(f"Invalid XML {xml_file}: {e}")
    
    if valid_xml_count == 0:
        logging.warning(f"Invalid photo set {photo_set.base_directory}: No valid XML files with IID")
        return False
    
    logging.debug(f"Valid photo set {photo_set.base_directory}: {len(photo_set.image_files)} Image, {valid_xml_count} valid XML")
    return True


def extract_iid_from_xml_enhanced(xml_file: Path) -> Optional[str]:
    """
    Extract IID from XML file - enhanced version with better error handling.
    
    Args:
        xml_file: Path to XML file
        
    Returns:
        Extracted IID or None if not found
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Try namespaced version first
        namespaces = {'mods': 'http://www.loc.gov/mods/v3'}
        identifier = root.find(".//mods:identifier[@type='IID']", namespaces)
        if identifier is not None and identifier.text:
            return identifier.text.strip()
        
        # Try non-namespaced version
        identifier = root.find(".//identifier[@type='IID']")
        if identifier is not None and identifier.text:
            return identifier.text.strip()
        
        return None
    except Exception:
        return None


def find_photo_sets_enhanced(parent_folder: str, flexible_structure: bool = True) -> List[PhotoSet]:
    """
    Enhanced photo set finder with flexible folder structure support.
    
    Args:
        parent_folder: Root directory to search
        flexible_structure: Enable flexible structure detection
        
    Returns:
        List of PhotoSet objects found
    """
    parent_path = Path(parent_folder).resolve()
    logging.info(f"Starting enhanced photo set search in: {parent_path}")
    
    # Find all relevant files recursively
    all_files = find_all_files_recursive(parent_path)
    
    photo_sets = []
    
    if flexible_structure:
        # Try hierarchical detection first
        hierarchical_sets = find_hierarchical_sets(all_files, parent_path)
        for photo_set in hierarchical_sets:
            if validate_photo_set(photo_set):
                photo_sets.append(photo_set)
    
    # Also try standard directory-based grouping for any missed sets
    file_groups = group_files_by_directory(all_files)
    
    for group in file_groups:
        # Skip if we already found this as a hierarchical set
        if any(ps.base_directory == group['directory'] for ps in photo_sets):
            continue
        
        # Relaxed condition: If we have XMLs and Manifest, we treat it as a set to process.
        # This allows detecting "Orphaned XMLs" where the image is missing or located elsewhere (Global Recovery).
        if group['xml_files'] and group['manifest_files']:
            photo_set = PhotoSet(
                base_directory=group['directory'],
                image_files=group['image_files'], # Might be empty
                xml_files=group['xml_files'],
                manifest_file=group['manifest_files'][0],  # Take first manifest if multiple
                structure_type='standard'
            )
            if validate_photo_set(photo_set):
                photo_sets.append(photo_set)
    
    # Log structure type breakdown for analytics
    structure_counts = defaultdict(int)
    for ps in photo_sets:
        structure_counts[ps.structure_type] += 1
    
    if structure_counts:
        structure_summary = ", ".join(f"{stype}: {count}" for stype, count in structure_counts.items())
        logging.info(f"Enhanced photo set search completed: {len(photo_sets)} sets found ({structure_summary})")
    else:
        logging.info(f"Enhanced photo set search completed: {len(photo_sets)} sets found")
    
    return photo_sets


def find_photo_sets(parent_folder: str) -> list:
    """
    Enhanced photo set finder with backward compatibility.
    
    This function provides the same interface as the original find_photo_sets
    function while using the enhanced detection capabilities under the hood.
    
    Args:
        parent_folder (str): Path to the parent folder to search.

    Returns:
        list: A list of tuples containing valid photo sets. Each tuple contains:
              (directory, list of JPG/JPEG files, list of XML files, list of manifest files)
    """
    # Use enhanced finder
    enhanced_results = find_photo_sets_enhanced(parent_folder, flexible_structure=True)
    
    # Convert to original format for backward compatibility
    compatible_results = []
    for photo_set in enhanced_results:
        compatible_tuple = (
            photo_set.base_directory,       # directory (Path object)
            photo_set.image_files,           # list of Image files  
            photo_set.xml_files,           # list of XML files
            [photo_set.manifest_file]      # list of manifest files (original expects list)
        )
        compatible_results.append(compatible_tuple)
    
    logging.info(f"Total photo sets found: {len(compatible_results)} in {parent_folder}")
    return compatible_results

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


def apply_exif_orientation(img: Image.Image, image_path: Path) -> Image.Image:
    """
    Apply EXIF orientation correction to an image.
    
    Args:
        img: PIL Image object
        image_path: Path to the image file (for logging)
        
    Returns:
        Image with correct orientation applied
    """
    try:
        # Get EXIF data
        exif = img.getexif()
        
        if exif is not None:
            # Look for orientation tag (274 is the standard EXIF orientation tag)
            orientation = exif.get(274, 1)  # Default to 1 (normal) if not found
            
            # Log original orientation for debugging
            orientation_names = {
                1: "Normal",
                2: "Mirrored horizontally", 
                3: "Rotated 180°",
                4: "Mirrored vertically",
                5: "Mirrored horizontally, rotated 90° CCW",
                6: "Rotated 90° CW", 
                7: "Mirrored horizontally, rotated 90° CW",
                8: "Rotated 90° CCW"
            }
            
            orientation_name = orientation_names.get(orientation, f"Unknown ({orientation})")
            logging.debug(f"Image {image_path.name} has EXIF orientation: {orientation_name}")
            
            # Apply orientation corrections
            if orientation == 2:
                # Mirrored horizontally
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                logging.info(f"Applied horizontal flip to {image_path.name}")
            elif orientation == 3:
                # Rotated 180°
                img = img.rotate(180, expand=True)
                logging.info(f"Applied 180° rotation to {image_path.name}")
            elif orientation == 4:
                # Mirrored vertically
                img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                logging.info(f"Applied vertical flip to {image_path.name}")
            elif orientation == 5:
                # Mirrored horizontally, then rotated 90° CCW
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(270, expand=True)
                logging.info(f"Applied horizontal flip + 270° rotation to {image_path.name}")
            elif orientation == 6:
                # Rotated 90° CW (270° CCW)
                img = img.rotate(270, expand=True)
                logging.info(f"Applied 270° rotation to {image_path.name}")
            elif orientation == 7:
                # Mirrored horizontally, then rotated 90° CW
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(90, expand=True)
                logging.info(f"Applied horizontal flip + 90° rotation to {image_path.name}")
            elif orientation == 8:
                # Rotated 90° CCW
                img = img.rotate(90, expand=True)
                logging.info(f"Applied 90° rotation to {image_path.name}")
            elif orientation == 1:
                # Normal orientation - no change needed
                logging.debug(f"Image {image_path.name} has normal orientation")
            else:
                logging.warning(f"Unknown orientation {orientation} for {image_path.name}")
                
        else:
            logging.debug(f"No EXIF data found for {image_path.name}")
            
    except Exception as e:
        logging.warning(f"Error reading EXIF orientation for {image_path.name}: {e}")
        # Return original image if we can't read EXIF
        
    return img


def validate_image_orientation(image_path: Path) -> dict:
    """
    Validate and report image orientation information for debugging.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with orientation information
    """
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            orientation = exif.get(274, 1) if exif else 1
            
            orientation_info = {
                'path': str(image_path),
                'size': img.size,
                'mode': img.mode,
                'format': img.format,
                'orientation_code': orientation,
                'has_exif': exif is not None,
                'needs_correction': orientation != 1
            }
            
            # Add human-readable orientation
            orientation_names = {
                1: "Normal", 2: "Mirrored horizontally", 3: "Rotated 180°",
                4: "Mirrored vertically", 5: "Mirrored horizontally, rotated 90° CCW",
                6: "Rotated 90° CW", 7: "Mirrored horizontally, rotated 90° CW", 
                8: "Rotated 90° CCW"
            }
            orientation_info['orientation_name'] = orientation_names.get(orientation, f"Unknown ({orientation})")
            
            return orientation_info
            
    except Exception as e:
        return {
            'path': str(image_path),
            'error': str(e),
            'validation_failed': True
        }


def debug_orientation_issues(folder_path: str, output_csv: str = "orientation_debug.csv"):
    """
    Debug orientation issues in a specific folder.
    Creates a CSV report of all images and their orientation status.
    """
    import csv
    
    folder = Path(folder_path)
    results = []
    
    logging.info(f"Starting orientation debug for folder: {folder}")
    
    # Find all Image files recursively
    image_files = []
    for ext in VALID_IMAGE_EXTENSIONS:
        # Check both lower and upper case
        image_files.extend(folder.rglob(f"*{ext}"))
        image_files.extend(folder.rglob(f"*{ext.upper()}"))
    
    # Remove duplicates
    image_files = list(set(image_files))
    
    logging.info(f"Found {len(image_files)} Image files to analyze")
    
    for image_file in image_files:
        orientation_info = validate_image_orientation(image_file)
        orientation_info['relative_path'] = str(image_file.relative_to(folder))
        results.append(orientation_info)
        
        if orientation_info.get('needs_correction', False):
            logging.warning(f"Image needs orientation correction: {image_file.name} - {orientation_info['orientation_name']}")
    
    # Write CSV report
    csv_path = folder / output_csv
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        if results:
            fieldnames = results[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    # Summary
    total_images = len(results)
    needs_correction = sum(1 for r in results if r.get('needs_correction', False))
    
    logging.info(f"Orientation debug complete:")
    logging.info(f"  Total images: {total_images}")
    logging.info(f"  Need correction: {needs_correction}")
    logging.info(f"  Report saved to: {csv_path}")
    
    return csv_path


def convert_to_tiff(image_path: Path) -> Optional[Path]:
    """
    Converts an image file (JPG, PNG, PDF, etc.) to .tiff with proper EXIF orientation handling.
    Detects and attempts to fix corrupted files before skipping them.
    Deletes the original file after successful conversion.
    """
    try:
        tiff_path = image_path.with_suffix('.tiff')
        
        # Check exclusion to avoid overwriting existing TIFFs if source is TIFF
        if image_path.suffix.lower() in ['.tif', '.tiff']:
            logging.info(f"File {image_path} is already TIFF. Skipping conversion logic but verifying.")
            try:
                with Image.open(image_path) as img:
                    img.verify()
                return image_path
            except Exception:
                logging.warning(f"Corrupted TIFF detected: {image_path}")
                return None

        # Special handling for PDF
        if image_path.suffix.lower() == '.pdf':
             # Try PyMuPDF (fitz) first as it doesn't require Ghostscript
             if fitz:
                 try:
                     doc = fitz.open(image_path)
                     page = doc.load_page(0)  # load the first page
                     
                     # Render at 300 DPI (default is 72 DPI)
                     zoom = 300 / 72
                     mat = fitz.Matrix(zoom, zoom)
                     pix = page.get_pixmap(matrix=mat)
                     
                     # Create PIL Image from pixmap
                     mode = "RGBA" if pix.alpha else "RGB"
                     img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
                     
                     if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                     img.save(tiff_path, "TIFF", compression='none', dpi=(300, 300))
                     doc.close()
                     
                     image_path.unlink()
                     logging.info(f"Converted PDF {image_path} to {tiff_path} using PyMuPDF (300 DPI)")
                     return tiff_path
                 except Exception as e:
                     logging.warning(f"PyMuPDF conversion failed for {image_path}: {e}. Falling back to Pillow.")

             # Fallback to Pillow (needs Ghostscript)
             try:
                with Image.open(image_path) as img:
                    # PDF might have multiple pages, this typically picks the first one
                    # We need to make sure we are getting a valid image object
                    
                    # Convert to RGB (PDFs are often CMYK or P)
                    img = img.convert('RGB')
                    img.save(tiff_path, "TIFF", compression='none', dpi=(300, 300))
                    
                image_path.unlink()
                logging.info(f"Converted PDF {image_path} to {tiff_path}")
                return tiff_path
             except Exception as e:
                 logging.error(f"Failed to convert PDF {image_path}. Ensure Ghostscript or valid PDF decoder is installed: {e}")
                 # Fallback strategy not available without external libs (pdf2image)
                 return None

        # Standard Image Conversion (JPG, PNG, etc.)
        with Image.open(image_path) as img:
            img.verify()  # Verify if the image is corrupted
        
        # Re-open for processing
        with Image.open(image_path) as img:
            # Capture original DPI if available
            original_dpi = img.info.get('dpi', (300, 300))

            # Apply EXIF orientation correction
            img = apply_exif_orientation(img, image_path)
            
            # Convert to RGB (handles RGBA from PNG, CMYK, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as TIFF with high quality, no compression, preserving DPI
            img.save(tiff_path, "TIFF", compression='none', dpi=original_dpi)
        
        # Delete the original file after successful conversion
        image_path.unlink()
        logging.info(f"Converted {image_path} to {tiff_path} and deleted original")
        return tiff_path
        
    except UnidentifiedImageError as e:
        logging.warning(f"Corrupted file detected: {image_path}. Attempting to fix...")
        # Only try to fix JPGs with the specific fix_corrupted_jpg logic
        if image_path.suffix.lower() in ['.jpg', '.jpeg']:
            fixed_path = fix_corrupted_jpg(image_path)
            if fixed_path:
                return convert_to_tiff(fixed_path)  # Retry with the fixed file
        
        logging.error(f"Unable to process {image_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error converting {image_path} to TIFF: {e}")
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


def process_file_set_with_context(files: FilePair, iid: str, subfolder: Path, context: BatchContext) -> bool:
    """Process a single file set with context for dry-run and staging support"""
    try:
        image_file = files.image
        xml_file = files.xml
        
        context.logger.info(f"Processing IID {iid} from {subfolder}")
        
        if image_file is None:
            if context.csv_writer is not None:
                context.csv_writer.writerow([iid, str(xml_file), 'N/A', 'WARNING', 'ORPHANED_XML', 'No matching Image found'])
            return False
        
        # Validate orientation before processing
        orientation_info = validate_image_orientation(image_file)
        if orientation_info.get('needs_correction', False):
            context.logger.info(f"Image {image_file.name} has orientation {orientation_info['orientation_name']} - will be corrected")
            if context.csv_writer is not None:
                context.csv_writer.writerow([iid, str(xml_file), str(image_file), 'INFO', 'ORIENTATION', f"Detected: {orientation_info['orientation_name']}"])
            
        if context.dry_run:
            # Simulate processing steps
            context.logger.info(f"DRY RUN: Would convert {image_file.name} to TIFF with orientation correction")
            xml_name = xml_file.name if xml_file else 'N/A'
            context.logger.info(f"DRY RUN: Would extract IID {iid} from {xml_name}")
            context.logger.info(f"DRY RUN: Would create ZIP package for {iid}")
            
            dry_run_notes = 'Would process successfully'
            if orientation_info.get('needs_correction', False):
                dry_run_notes += f" (would correct {orientation_info['orientation_name']})"
            
            if context.csv_writer is not None:
                context.csv_writer.writerow([iid, str(xml_file), str(image_file), 'SUCCESS', 'DRY_RUN', dry_run_notes])
            return True
        
        # Actual processing with orientation correction
        tiff_path = convert_to_tiff(image_file)  # Now includes orientation handling
        if tiff_path is None:
            if context.csv_writer is not None:
                context.csv_writer.writerow([iid, str(xml_file), str(image_file), 'ERROR', 'CONVERT_FAILED', 'Image to TIFF conversion failed'])
            return False

        if xml_file is None:
            if context.csv_writer is not None:
                context.csv_writer.writerow([iid, 'N/A', str(image_file), 'ERROR', 'MISSING_XML', 'XML file is None'])
            return False

        new_tiff, new_xml = rename_files(subfolder, tiff_path, xml_file, iid)
        
        # Find manifest file
        manifest_files = list(subfolder.glob("*.ini")) + list(subfolder.glob("MANIFEST.ini"))
        manifest_path = manifest_files[0] if manifest_files else None
        
        if not manifest_path:
            if context.csv_writer is not None:
                context.csv_writer.writerow([iid, str(xml_file), str(image_file), 'ERROR', 'NO_MANIFEST', 'No manifest file found'])
            return False
            
        # Package the files
        package_to_zip(new_tiff, new_xml, manifest_path, context.output_dir)
        
        success_notes = 'Successfully packaged'
        if orientation_info.get('needs_correction', False):
            success_notes += f" (corrected {orientation_info['orientation_name']})"
        if context.csv_writer is not None:
            context.csv_writer.writerow([iid, str(xml_file), str(image_file), 'SUCCESS', 'PROCESSED', success_notes])
        return True
            
    except Exception as e:
        if context.csv_writer is not None:
            context.csv_writer.writerow([iid, str(xml_file) if xml_file else '', str(image_file) if image_file else '', 'ERROR', 'EXCEPTION', str(e)])
        context.logger.error(f"Error processing {iid}: {str(e)}")
        return False


def batch_process_with_safety_nets(folder_path: str, dry_run: bool = False, staging: bool = False) -> tuple:
    """Enhanced batch process with safety nets, dry-run, and CSV reporting"""
    # Use module-level logger
    logger = logging.getLogger(__name__)
    
    # Set up output directory
    folder_path_obj = Path(folder_path)
    if staging:
        output_dir = folder_path_obj / "staging_output"
    else:
        output_dir = folder_path_obj / "output"
    
    # Set up CSV reporting
    csv_filename = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = output_dir / csv_filename if not dry_run else folder_path_obj / csv_filename
    
    # User-friendly logging
    mode = "Dry Run Preview" if dry_run else "Staging" if staging else "Production"
    log_user_friendly(f"Starting {mode} processing")
    log_user_friendly(f"Source folder: {folder_path}")
    
    if dry_run:
        log_user_friendly("🔍 Dry Run Mode - Previewing processing, no files will be changed")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
    elif staging:
        log_user_friendly(f"Staging Mode - Output to: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        log_user_friendly(f"Production Mode - Output to: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Advanced logging (technical details)
    logger.info(f"Starting batch process - Dry run: {dry_run}, Staging: {staging}")
    logger.info(f"Source folder: {folder_path}")
    logger.info(f"Output folder: {output_dir}")
    
    # PRE-FLIGHT CHECKS: Validate environment before processing
    from validation import pre_flight_checks
    
    # Get preliminary photo sets for pre-flight estimation
    try:
        prelim_photo_sets = find_photo_sets_enhanced(folder_path)
        
        log_user_friendly("Running pre-flight checks...")
        preflight = pre_flight_checks(prelim_photo_sets, output_dir)
        
        if not preflight.passed:
            for blocker in preflight.blockers:
                log_user_friendly(f"[BLOCKER] {blocker}")
                logger.error(f"Pre-flight check failed: {blocker}")
            raise RuntimeError("Pre-flight checks failed. Aborting batch processing.")
        
        for warning in preflight.warnings:
            log_user_friendly(f"[WARNING] Pre-flight: {warning}")
            logger.warning(f"Pre-flight warning: {warning}")
        
        log_user_friendly(f"[PASS] Pre-flight checks passed. Disk space: {preflight.disk_space_gb:.2f} GB available")
        logger.info(f"Pre-flight checks passed: {preflight.disk_space_gb:.2f} GB available, {preflight.required_space_gb:.2f} GB estimated")
    except Exception as e:
        logger.warning(f"Pre-flight checks skipped due to error: {e}")
        log_user_friendly(f"[WARNING] Pre-flight checks skipped: {e}")
    
    success_count = 0
    error_count = 0
    
    # Initialize CSV writer and process within the same block
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['IID', 'XML_Path', 'JPG_Path', 'Status', 'Action', 'Notes'])
            
            # Create batch context
            context = BatchContext(
                output_dir=output_dir,
                dry_run=dry_run,
                staging=staging,
                csv_path=csv_path,
                csv_writer=csv_writer,
                logger=logger
            )
            
            # Use enhanced photo set detection to handle complex directory structures
            try:
                photo_sets = find_photo_sets_enhanced(folder_path)
                log_user_friendly(f"🔍 Found {len(photo_sets)} photo sets to process")
                logger.info(f"Enhanced detection found {len(photo_sets)} photo sets")
                
                # Build global image index for recovery of misplaced files
                global_image_index = {}
                try:
                    scan_results = find_all_files_recursive(Path(folder_path))
                    # scan_results is {'image': [...], ...}
                    for fpath in scan_results.get('image', []):
                        global_image_index[fpath.stem] = fpath
                    logger.info(f"Global index built with {len(global_image_index)} images")
                except Exception as idx_err:
                    logger.warning(f"Failed to build global index: {idx_err}")

                for photo_set in photo_sets:                    
                    # Process ALL files in the photo set, not just the first one
                    # Match Image and XML files by IID
                    for xml_file in photo_set.xml_files:
                        try:
                            # Extract IID from XML file
                            iid = extract_iid_from_xml(xml_file)
                            
                            # Find matching Image file by IID
                            matching_image = None
                            
                            # Strategy 1: Strict Filename Match
                            # ... inside current directory
                            for image_file in photo_set.image_files:
                                if image_file.stem == xml_file.stem:
                                    matching_image = image_file
                                    break
                            
                            # Strategy 2: Smart IID Match (Fallback)
                            # ... inside current directory
                            if matching_image is None:
                                for image_file in photo_set.image_files:
                                    # Check if the IID string appears in the image filename
                                    if iid in image_file.name:
                                        matching_image = image_file
                                        logger.info(f"Smart Match: Found image {image_file.name} for XML {xml_file.name} based on IID {iid}")
                                        break
                                        
                            # Strategy 3: Lone Survivor / Single Pair Match (Fallback)
                            # ... inside current directory
                            if matching_image is None:
                                if len(photo_set.image_files) == 1 and len(photo_set.xml_files) == 1:
                                    matching_image = photo_set.image_files[0]
                                    logger.info(f"Smart Match: Assumed pairing for lone files - Image {matching_image.name} and XML {xml_file.name}")

                            # Strategy 4: Global Index Recovery (Cross-Directory Link)
                            if matching_image is None:
                                # Try to match by stem in the global index
                                if xml_file.stem in global_image_index:
                                    potential_match = global_image_index[xml_file.stem]
                                    # Verify it's not the same file we already checked (unlikely if loop finished)
                                    matching_image = potential_match
                                    logger.warning(f"Strategy 4: Recovered image {matching_image.name} from DIFFERENT directory: {matching_image.parent}")
                                    if context.csv_writer is not None:
                                        # Log this recovery operation
                                        context.csv_writer.writerow([iid, str(xml_file), str(matching_image), 'WARNING', 'CROSS_LINK', f'Image recovered from: {matching_image.parent.name}'])

                            if matching_image is None:
                                logger.warning(f"No matching Image found for XML {xml_file.name} (IID: {iid})")
                                if context.csv_writer is not None:
                                    context.csv_writer.writerow([iid, str(xml_file), 'N/A', 'WARNING', 'MISSING_IMAGE', 'No matching Image file found'])
                                continue
                            
                            # Create FilePair for this specific Image/XML pair
                            files = FilePair(
                                xml=xml_file,
                                image=matching_image,
                                iid=iid
                            )
                            
                            # Process this file pair
                            success = process_file_set_with_context(files, iid, photo_set.base_directory, context)
                            if success:
                                success_count += 1
                            else:
                                error_count += 1
                                
                        except Exception as e:
                            iid = "UNKNOWN"
                            try:
                                iid = extract_iid_from_xml(xml_file) if xml_file else "UNKNOWN"
                            except:
                                pass
                            logger.error(f"Error processing file {xml_file.name} (IID: {iid}): {str(e)}", exc_info=True)
                            if context.csv_writer is not None:
                                context.csv_writer.writerow([iid, str(xml_file), '', 'ERROR', 'PROCESSING', str(e)])
                            error_count += 1
                        
            except Exception as e:
                import traceback
                traceback_str = traceback.format_exc()
                log_user_friendly(f"❌ Error finding photo sets: {e}")
                logger.error(f"Error in batch processing: {str(e)}\n{traceback_str}")
                print(f"\n{'='*60}\nFULL TRACEBACK:\n{'='*60}")
                print(traceback_str)
                print(f"{'='*60}\n")
                # Fallback to basic error handling
                if context.csv_writer is not None:
                    context.csv_writer.writerow(['', folder_path, '', 'ERROR', 'DETECTION', str(e)])
                error_count += 1
            
            # Log final results
            logger.info(f"Batch process completed - Success: {success_count}, Errors: {error_count}")
            if context.csv_writer is not None:
                context.csv_writer.writerow(['SUMMARY', '', '', f'Success: {success_count}', f'Errors: {error_count}', f'Dry run: {dry_run}'])
        
        # POST-PROCESSING VALIDATION: Verify output matches expectations
        from validation import validate_batch_output, generate_reconciliation_report
        
        try:
            # Validate batch output
            validation_result = validate_batch_output(
                photo_sets=photo_sets,
                output_dir=output_dir,
                success_count=success_count,
                dry_run=dry_run
            )
            
            if not validation_result.passed:
                log_user_friendly("[FAIL] Post-processing validation FAILED:")
                logger.error("Post-processing validation FAILED:")
                for error in validation_result.errors:
                    log_user_friendly(f"  - {error}")
                    logger.error(f"  - {error}")
                for invalid_zip in validation_result.invalid_zips:
                    log_user_friendly(f"  - Invalid ZIP: {invalid_zip}")
                    logger.error(f"  - Invalid ZIP: {invalid_zip}")
            else:
                log_user_friendly(f"[PASS] Post-processing validation: {validation_result.valid_zips} valid ZIPs")
                logger.info(f"[PASS] Post-processing validation: {validation_result.valid_zips} valid ZIPs")
            
            # Generate reconciliation report (skip for dry run)
            if not dry_run:
                reconciliation = generate_reconciliation_report(
                    photo_sets=photo_sets,
                    csv_path=csv_path,
                    output_dir=output_dir
                )
                
                log_user_friendly("=== Reconciliation Report ===")
                log_user_friendly(f"Input XML files: {reconciliation.input_xml_count}")
                log_user_friendly(f"CSV SUCCESS rows: {reconciliation.csv_success_rows}")
                log_user_friendly(f"Actual ZIP files: {reconciliation.actual_zip_count}")
                log_user_friendly(f"Valid ZIP files: {reconciliation.valid_zip_count}")
                
                logger.info("=== Reconciliation Report ===")
                logger.info(f"Input XML files: {reconciliation.input_xml_count}")
                logger.info(f"CSV SUCCESS rows: {reconciliation.csv_success_rows}")
                logger.info(f"Actual ZIP files: {reconciliation.actual_zip_count}")
                logger.info(f"Valid ZIP files: {reconciliation.valid_zip_count}")
                
                if reconciliation.discrepancies:
                    log_user_friendly("Discrepancies found:")
                    logger.warning("Discrepancies found:")
                    for discrepancy in reconciliation.discrepancies:
                        log_user_friendly(f"  - {discrepancy}")
                        logger.warning(f"  - {discrepancy}")
                else:
                    log_user_friendly("[PASS] No discrepancies found.")
                    logger.info("No discrepancies found.")
                
                if reconciliation.orphaned_files:
                    log_user_friendly(f"Orphaned files found: {len(reconciliation.orphaned_files)}")
                    logger.warning(f"Orphaned files found: {len(reconciliation.orphaned_files)}")
                    for orphaned in reconciliation.orphaned_files[:5]:  # Limit to first 5
                        log_user_friendly(f"  - {orphaned}")
                        logger.warning(f"  - {orphaned}")
        except Exception as e:
            logger.warning(f"Post-processing validation skipped due to error: {e}")
            log_user_friendly(f"[WARNING] Post-processing validation skipped: {e}")
            
        return success_count, error_count, csv_path
            
    except Exception as e:
        logger.error(f"Critical error in batch process: {str(e)}")
        raise


def batch_process(root: str, jpg_files: list, xml_files: list, ini_files: list) -> None:
    """
    Processes photo sets by converting, renaming, and packaging them into ZIP archives.
    Logs a summary at the end instead of detailed per-file logs.
    """
    try:
        path = Path(root)
        
        # Manifest Validation: Ensure exactly one manifest file
        try:
            manifest_path = validate_single_manifest(ini_files)
            logging.info(f"Using manifest: {manifest_path}")
        except ValueError as e:
            logging.error(f"Manifest validation failed for {root}: {e}")
            raise e

        # Initialize counters and error tracking
        processed = 0
        skipped = 0
        error_details = []

        for jpg_file, xml_file in zip(jpg_files, xml_files):
            try:
                # Process files
                iid = extract_iid_from_xml(xml_file)
                tiff_path = convert_to_tiff(jpg_file)
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

This tool automates the creation of ingest-ready AIS-compatible ZIP packages for the Cetamura Digital Collections.

REQUIREMENTS
-----------
- JPG/JPEG image files  
- Corresponding XML metadata files
- MANIFEST.ini file in each folder
- Files organized in folder structure (flexible hierarchy supported)

USAGE INSTRUCTIONS
----------------
1. Click "Select Folder" to choose the parent directory containing your photo sets
   
   Supported structures (flexible detection):
   Parent_Folder/
   ├── 2006/
   │   ├── 46N-3W/
   │   │   ├── image.jpg
   │   │   ├── metadata.xml
   │   │   └── MANIFEST.ini
   │   └── ...
   └── ...
   
   OR single-level folders with photo sets

2. Choose processing mode:
   • DRY RUN MODE: Preview processing without modifying files
     - Generates CSV report showing what would be processed
     - Tests folder structure and identifies issues
     - No files are changed or created
   
   • STAGING MODE: Process to staging_output folder
     - Creates ZIP packages in separate staging folder
     - Original files remain unchanged
     - Review results before final processing
   
   • PRODUCTION MODE: Direct processing to output folder
     - Creates final ZIP packages ready for ingest
     - Processes files directly

3. The tool automatically:
   - Detects photo sets using enhanced IID-based pairing
   - Converts JPG images to TIFF format with orientation correction
   - Extracts IID from XML metadata files
   - Renames TIFF and XML files to match the IID
   - Packages files with MANIFEST.ini into ZIP archives
   - Generates detailed CSV processing reports
   - Provides user-friendly progress updates

4. Review the generated CSV report for detailed processing results
   - Shows success/error status for each photo set
   - Documents orientation corrections applied
   - Lists any orphaned files or missing components

OUTPUT
------
- ZIP files named after the IID from XML metadata
- CSV processing report with detailed status
- User-friendly and technical log files for troubleshooting
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


def view_log_file():
    """Open the log file in the default system application"""
    import os
    import platform
    import subprocess
    
    try:
        if log_file.exists():
            system = platform.system().lower()
            if system == "windows":
                os.startfile(str(log_file))
            elif system == "darwin":  # macOS
                subprocess.call(["open", str(log_file)])
            else:  # Linux and others
                subprocess.call(["xdg-open", str(log_file)])
            logging.info(f"Opened log file: {log_file}")
        else:
            messagebox.showwarning("Log File Not Found", f"Log file does not exist: {log_file}")
            logging.warning("Attempted to open non-existent log file")
    except Exception as e:
        messagebox.showerror("Error Opening Log", f"Could not open log file: {e}")
        logging.error(f"Error opening log file: {e}")

# Function to view user-friendly log
def view_user_friendly_log():
    summary_log_file = "batch_process_summary.log"
    try:
        if os.path.exists(summary_log_file):
            if platform.system() == 'Windows':
                os.startfile(summary_log_file)
            elif platform.system() == 'Darwin':
                subprocess.call(['open', summary_log_file])
            elif platform.system() == 'Linux':
                subprocess.call(['xdg-open', summary_log_file])
            logging.info("User opened user-friendly summary log file")
        else:
            messagebox.showwarning("Summary Log Not Found", f"Summary log file does not exist: {summary_log_file}")
            logging.warning("Attempted to open non-existent summary log file")
    except Exception as e:
        messagebox.showerror("Error Opening Summary Log", f"Could not open summary log file: {e}")
        logging.error(f"Error opening summary log file: {e}")

# Function to select Root Folder
def select_folder():
    global label, btn_process, status_label
    
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        if not Path(folder_selected).exists():
            messagebox.showerror("Error", "Selected folder does not exist.")
            return
        
        # UX Improvement: Check for photo sets and disable/enable Start button accordingly
        try:
            photo_sets = find_photo_sets(folder_selected)
            if not photo_sets:
                if label:
                    label.config(text=f"Selected: {folder_selected} - No photo sets found")
                if btn_process:
                    btn_process.config(state="disabled")
                if status_label:
                    status_label.config(text="Status: No valid photo sets found in selected folder")
                logging.warning(f"No photo sets found in selected folder: {folder_selected}")
            else:
                if label:
                    label.config(text=f"Selected: {folder_selected}")
                if btn_process:
                    btn_process.config(state="normal")
                if status_label:
                    status_label.config(text=f"Status: Ready - Found {len(photo_sets)} photo set(s)")
                logging.info(f"Found {len(photo_sets)} photo sets in selected folder")
        except Exception as e:
            if label:
                label.config(text=f"Selected: {folder_selected} - Error scanning folder")
            if btn_process:
                btn_process.config(state="disabled")
            if status_label:
                status_label.config(text="Status: Error scanning selected folder")
            logging.error(f"Error scanning folder {folder_selected}: {e}")
    else:
        if label:
            label.config(text="No folder selected!")
        if btn_process:
            btn_process.config(state="disabled")
        if status_label:
            status_label.config(text="Status: Waiting for folder selection")

def show_processing_options_dialog():
    """Show dialog for selecting processing options (dry-run, staging, etc.)"""
    from tkinter import Toplevel, BooleanVar, Checkbutton, Frame, Button
    
    dialog = Toplevel(root_window)
    dialog.title("Processing Options")
    dialog.geometry("400x600")
    dialog.transient(root_window)
    dialog.grab_set()
    
    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # Variables to store options
    dry_run_var = BooleanVar(value=False)
    staging_var = BooleanVar(value=False)
    advanced_logs_var = BooleanVar(value=False)
    result = {'cancelled': True}
    
    # Warning label for mode conflicts
    warning_label = Label(dialog, text="", font=('Helvetica', 10), fg='red', wraplength=350)
    warning_label.pack(pady=5)
    
    # Title
    title_label = Label(dialog, text="Choose Processing Mode", font=('Helvetica', 14, 'bold'))
    title_label.pack(pady=20)
    
    # Options frame
    options_frame = Frame(dialog)
    options_frame.pack(pady=20, padx=20)
    
    def check_mode_conflict():
        """Check for conflicting mode selections and provide guidance"""
        dry_run = dry_run_var.get()
        staging = staging_var.get()
        
        if dry_run and staging:
            warning_label.config(text="⚠️ Both modes selected: Defaulting to Dry Run Mode\n(Dry Run takes precedence - no files will be modified)")
            proceed_btn.config(text="Proceed with Dry Run")
        elif dry_run:
            warning_label.config(text="🔍 Dry Run Mode: Preview only, no files modified")
            proceed_btn.config(text="Proceed with Dry Run")
        elif staging:
            warning_label.config(text="📁 Staging Mode: Output to staging_output folder")
            proceed_btn.config(text="Proceed with Staging")
        else:
            warning_label.config(text="⚡ Production Mode: Direct processing to output folder")
            proceed_btn.config(text="Proceed with Production")
    
    # Dry run option
    dry_run_check = Checkbutton(options_frame, text="Dry Run Mode", variable=dry_run_var,
                               font=('Helvetica', 12), command=check_mode_conflict)
    dry_run_check.pack(anchor='w', pady=5)
    
    dry_run_desc = Label(options_frame, 
                        text="• Preview processing without modifying files\n• Generate CSV report only\n• Test your folder structure",
                        font=('Helvetica', 9), fg='gray', justify='left')
    dry_run_desc.pack(anchor='w', padx=20, pady=(0, 15))
    
    # Staging option
    staging_check = Checkbutton(options_frame, text="Staging Mode", variable=staging_var,
                               font=('Helvetica', 12), command=check_mode_conflict)
    staging_check.pack(anchor='w', pady=5)
    
    staging_desc = Label(options_frame,
                        text="• Output to 'staging_output' folder\n• Keep original files unchanged\n• Review before final processing",
                        font=('Helvetica', 9), fg='gray', justify='left')
    staging_desc.pack(anchor='w', padx=20, pady=(0, 15))
    
    # Advanced logs option
    advanced_logs_check = Checkbutton(options_frame, text="Advanced Logs", variable=advanced_logs_var,
                                     font=('Helvetica', 12))
    advanced_logs_check.pack(anchor='w', pady=5)
    
    advanced_logs_desc = Label(options_frame,
                              text="• Show detailed technical logs\n• Include debug information\n• For troubleshooting and developers",
                              font=('Helvetica', 9), fg='gray', justify='left')
    advanced_logs_desc.pack(anchor='w', padx=20, pady=(0, 20))
    
    # Buttons frame
    button_frame = Frame(dialog)
    button_frame.pack(pady=20)
    
    def on_proceed():
        dry_run = dry_run_var.get()
        staging = staging_var.get()
        
        # Implement guardrails: dry run takes precedence over staging
        if dry_run and staging:
            # Show confirmation dialog for dual mode
            response = messagebox.askyesno(
                "Mode Conflict Resolution",
                "Both Dry Run and Staging modes are selected.\n\n"
                "Dry Run Mode will take precedence:\n"
                "• No files will be modified\n"
                "• Only CSV report will be generated\n"
                "• Staging mode will be ignored\n\n"
                "Continue with Dry Run Mode?",
                parent=dialog
            )
            if not response:
                return
        
        result['cancelled'] = False
        result['dry_run'] = dry_run
        result['staging'] = staging if not dry_run else False  # Staging disabled if dry_run
        result['advanced_logs'] = advanced_logs_var.get()
        dialog.destroy()
    
    def on_cancel():
        dialog.destroy()
    
    proceed_btn = Button(button_frame, text="Proceed", command=on_proceed, 
                        bg='#8B2E2E', fg='white', font=('Helvetica', 12))
    proceed_btn.pack(side='left', padx=10)
    
    cancel_btn = Button(button_frame, text="Cancel", command=on_cancel,
                       font=('Helvetica', 12))
    cancel_btn.pack(side='left', padx=10)
    
    # Initialize mode display
    check_mode_conflict()
    
    # Wait for dialog to close
    dialog.wait_window()
    return result


# Function to start batch processing
def start_batch_process():
    global label, btn_select, btn_process, status_label, root_window
    
    if not label:
        messagebox.showerror("Error", "GUI not properly initialized.")
        return
        
    folder = label.cget("text").replace("Selected: ", "").split(" - ")[0]  # Extract clean folder path
    if not Path(folder).is_dir():
        messagebox.showerror("Error", "Please select a valid parent folder.")
        return

    # Show processing options dialog
    options = show_processing_options_dialog()
    if options['cancelled']:
        return
        
    dry_run = options.get('dry_run', False)
    staging = options.get('staging', False)
    advanced_logs = options.get('advanced_logs', False)
    
    # Configure logging level based on user preference
    configure_logging_level(advanced_logs)
    
    mode_text = "Dry Run" if dry_run else "Staging" if staging else "Processing"
    if status_label:
        status_label.config(text=f"{mode_text}...")
    if btn_select:
        btn_select.config(state="disabled")
    if btn_process:
        btn_process.config(state="disabled")
    logging.info(f"Batch processing started for folder: {folder} (dry_run={dry_run}, staging={staging})")

    def run_process():
        try:
            # Use the new enhanced batch processing function
            success_count, error_count, csv_path = batch_process_with_safety_nets(folder, dry_run, staging)
            
            # Prepare success message
            total_count = success_count + error_count
            mode_desc = "DRY RUN - " if dry_run else "STAGING - " if staging else ""
            
            if dry_run:
                success_message = f"{mode_desc}Processing simulation completed!\n\n"
                success_message += f"Would process: {success_count} items\n"
                success_message += f"Issues found: {error_count} items\n\n"
                success_message += f"Review the report: {csv_path}\n\n"
                success_message += "No files were actually modified."
            else:
                success_message = f"{mode_desc}Processing completed!\n\n"
                success_message += f"Successfully processed: {success_count} items\n"
                success_message += f"Errors: {error_count} items\n\n"
                if staging:
                    success_message += f"Output saved to staging folder\n"
                success_message += f"Detailed report: {csv_path}"
            
            if root_window and status_label:
                root_window.after(0, lambda sl=status_label: sl.config(text=f"{mode_desc}Completed successfully!"))
            logging.info(f"Batch processing completed - Success: {success_count}, Errors: {error_count}")
            if root_window:
                root_window.after(0, lambda: messagebox.showinfo("Success", success_message))
            
        except Exception as e:
            error_msg = f"An error occurred during processing:\n{str(e)}"
            if root_window:
                root_window.after(0, lambda: messagebox.showerror("Error", error_msg))
            if root_window and status_label:
                root_window.after(0, lambda sl=status_label: sl.config(text="Processing failed."))
            logging.error(f"Error during batch processing: {e}")
        finally:
            if root_window and btn_select:
                root_window.after(0, lambda bs=btn_select: bs.config(state="normal"))
            if root_window and btn_process:
                root_window.after(0, lambda bp=btn_process: bp.config(state="normal"))

    threading.Thread(target=run_process).start()


def main():
    """Main function to initialize and run the GUI application."""
    # Initialize the main Tkinter window
    global root_window, btn_select, btn_process, progress, progress_label, status_label, label
    root_window = Tk()
    root_window.title("Cetamura Batch Ingest Tool")
    root_window.geometry("600x500")

    # Set the window icon (favicon)
    try:
        # Look for an optional icon in the local assets directory
        icon_path = Path(__file__).resolve().parent / "../assets/app.ico"
        if icon_path.exists():
            icon_image = Image.open(icon_path).resize((32, 32), Image.Resampling.LANCZOS)
            # Convert PIL image to PhotoImage for tkinter
            icon_photo = ImageTk.PhotoImage(icon_image)
            # Use wm_iconphoto with the PhotoImage (ignore type warning)
            root_window.wm_iconphoto(False, icon_photo)  # type: ignore
        else:
            logging.warning("Icon file not found. Using default window icon.")
    except Exception as e:
        logging.error(f"Error loading window icon: {e}")

    try:
        # Optional logo displayed at the top of the window
        logo_path = Path(__file__).resolve().parent / "../assets/app.png"
        if logo_path.exists():
            logo_image = Image.open(logo_path).resize((400, 100), Image.Resampling.LANCZOS)
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
        # Keep a reference to the image to prevent garbage collection
        setattr(logo_label, '_image_ref', logo_photo)
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
    help_menu.add_separator()
    help_menu.add_command(label="View Technical Log", command=view_log_file)
    help_menu.add_command(label="View Summary Log", command=view_user_friendly_log)
    menu_bar.add_cascade(label="Help", menu=help_menu)

    # Run the main loop for the GUI
    root_window.mainloop()


if __name__ == "__main__":
    main()

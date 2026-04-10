from tkinter import (
    Tk,
    filedialog,
    messagebox,
    Menu,
    Toplevel,
    Text,
    Scrollbar,
    Label,
    StringVar,
)
from tkinter.ttk import Button, Progressbar, Style, Frame, Radiobutton
import threading
import logging

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

MAX_SAFE_IMAGE_PIXELS = 500_000_000
Image.MAX_IMAGE_PIXELS = MAX_SAFE_IMAGE_PIXELS

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
import defusedxml.ElementTree as ET
import zipfile
import os
import re
import sys
import csv
import platform
import subprocess
import shutil
import configparser
from datetime import datetime
from typing import Any, Dict, List, NamedTuple, Optional
from collections import defaultdict
from validation import (
    generate_reconciliation_report,
    pre_flight_checks,
    validate_batch_output,
)

# Constants
NAMESPACES = {"mods": "http://www.loc.gov/mods/v3"}

VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".pdf"}
SKIP_DIRECTORY_NAMES = {"output", "staging_output", ".work", "__pycache__", ".git"}
WORKFLOW_PHOTO = "photo"
WORKFLOW_PATENT = "patent"
APP_BG = "#F8F4EA"
SURFACE_BG = "#FFFDF9"
CARD_BG = "#F4E7C8"
ACCENT_BG = "#782F40"
ACCENT_BG_DARK = "#5C2331"
ACCENT_ALT = "#CEB888"
ACCENT_ALT_SOFT = "#E6D8B3"
TEXT_PRIMARY = "#4A1F2B"
TEXT_MUTED = "#6C5A38"
SUCCESS_COLOR = "#782F40"
WARNING_COLOR = "#8C6B1F"
DISABLED_BG = "#D9C79B"
PATENT_SEARCH_ROOTS = [
    Path(path_str)
    for path_str in os.environ.get("CETAMURA_PATENT_SEARCH_ROOTS", "").split(os.pathsep)
    if path_str.strip()
]
PATENT_MANIFEST_REQUIRED_KEYS = (
    "submitter_email",
    "content_model",
    "parent_collection",
)


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
    workflow: str
    run_work_dir: Path
    patent_search_roots: List[Path]


# Enhanced Photo Set Finder Classes
class PhotoSet(NamedTuple):
    """Data structure for a complete photo set"""

    base_directory: Path
    image_files: List[Path]
    xml_files: List[Path]
    manifest_file: Path
    structure_type: str  # 'standard', 'hierarchical'


class PatentBatch(NamedTuple):
    """Data structure for a patent batch directory"""

    base_directory: Path
    pdf_files: List[Path]
    xml_files: List[Path]
    manifest_file: Path


class FolderScanSummary(NamedTuple):
    """UI-friendly summary of folder readiness for a workflow."""

    workflow: str
    ready: bool
    unit_count: int
    metadata_count: int
    asset_count: int
    issue_count: int
    status_text: str
    detail_text: str


# Set up logging with a file handler
log_file = Path("batch_tool.log")
user_log_file = Path("batch_process_summary.log")

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# Global widget variables - initialized in main()
root_window = None
btn_select = None
btn_process = None
progress = None
progress_label = None
status_label = None
label = None
folder_summary_label = None
workflow_description_label = None
selected_folder_path: Optional[Path] = None
workflow_selector_var = None


def configure_logging_level(advanced_logs: bool = False):
    """Configure logging based on user preference for simple or advanced logs"""
    # Create user-friendly logger
    user_logger = logging.getLogger("user_friendly")
    user_logger.handlers.clear()

    if advanced_logs:
        # Advanced logs: show everything
        level = logging.DEBUG
        format_str = "%(asctime)s - %(levelname)s - %(message)s"
    else:
        # Simple logs: show only important user-facing information
        level = logging.INFO
        format_str = "%(asctime)s - %(message)s"

    # File handler for user-friendly logs
    user_handler = logging.FileHandler(user_log_file, mode="w", encoding="utf-8")
    user_handler.setLevel(level)
    user_formatter = logging.Formatter(format_str)
    user_handler.setFormatter(user_formatter)
    user_logger.addHandler(user_handler)
    user_logger.setLevel(level)
    user_logger.propagate = False

    return user_logger


def log_user_friendly(message: str, level: str = "INFO"):
    """Log user-friendly messages"""
    user_logger = logging.getLogger("user_friendly")
    if level.upper() == "INFO":
        user_logger.info(message)
    elif level.upper() == "WARNING":
        user_logger.warning(message)
    elif level.upper() == "ERROR":
        user_logger.error(message)
    elif level.upper() == "DEBUG":
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
    if " " in sanitized or any(c in sanitized for c in '<>:"/\\|?*'):
        # Names with spaces or structured names with invalid chars -> use underscores
        sanitized = sanitized.replace(" ", "_")
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", sanitized)
        # Clean up multiple consecutive underscores
        sanitized = re.sub(r"_+", "_", sanitized)
    else:
        # Simple filenames -> remove everything unwanted
        pass

    # Always remove dots and non-ASCII for filename safety
    sanitized = sanitized.replace(".", "")
    sanitized = re.sub(r"[^\w\-_]", "", sanitized)

    return sanitized


def should_skip_directory(path: Path) -> bool:
    """Return True when a directory should be ignored during recursive scans."""
    return path.name.lower() in SKIP_DIRECTORY_NAMES


def copy_file_to_path(source_path: Path, destination_path: Path) -> Path:
    """Copy a file into the working directory while preserving metadata."""
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path)
    return destination_path


def cleanup_path(path: Path) -> None:
    """Best-effort cleanup for per-item workspace files."""
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink()
    except Exception as exc:
        logging.warning(f"Could not clean up temporary path {path}: {exc}")


def remove_empty_directory(path: Path) -> None:
    """Remove a directory only when it exists and is empty."""
    try:
        if path.exists() and path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    except Exception as exc:
        logging.warning(f"Could not remove empty directory {path}: {exc}")


def create_run_work_dir(output_dir: Path) -> Path:
    """Create a scratch workspace rooted inside the output directory."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    work_dir = output_dir / ".work" / run_id
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


def create_package_work_dir(context: BatchContext, package_id: str) -> Path:
    """Create a per-package scratch workspace."""
    package_work_dir = context.run_work_dir / sanitize_name(package_id)
    package_work_dir.mkdir(parents=True, exist_ok=True)
    return package_work_dir


def create_zip_archive(
    entries: List[tuple[Path, str]], output_folder: Path, base_name: str
) -> Path:
    """Create a ZIP archive from explicit file-to-archive-name entries."""
    output_folder.mkdir(parents=True, exist_ok=True)
    sanitized_base_name = sanitize_name(base_name)
    zip_path = output_folder / f"{sanitized_base_name}.zip"

    if zip_path.exists():
        suffix = 0
        while True:
            suffix_letter = chr(97 + suffix)
            zip_candidate = output_folder / f"{sanitized_base_name}_{suffix_letter}.zip"
            if not zip_candidate.exists():
                zip_path = zip_candidate
                break
            suffix += 1

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for source_path, archive_name in entries:
            zipf.write(source_path, arcname=archive_name)

    logging.info(f"Created zip archive: {zip_path}")
    return zip_path


def normalize_patent_document_id(value: str) -> str:
    """Normalize patent identifiers like 'US 123 B2' to 'US-123-B2'."""
    tokens = re.findall(r"[A-Za-z0-9]+", value.upper())
    return "-".join(tokens)


def normalize_patent_lookup_key(value: str) -> str:
    """Normalize patent identifiers for matching across filename variants."""
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def extract_identifier_from_xml_by_type(
    xml_file: Path, identifier_type: str
) -> Optional[str]:
    """Extract a specific identifier value from a MODS XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        identifier = root.find(
            f".//mods:identifier[@type='{identifier_type}']", NAMESPACES
        )
        if identifier is not None and identifier.text:
            return identifier.text.strip()

        identifier = root.find(f".//identifier[@type='{identifier_type}']")
        if identifier is not None and identifier.text:
            return identifier.text.strip()

        return None
    except Exception:
        return None


def validate_patent_manifest(manifest_path: Path) -> List[str]:
    """Validate that the shared patent manifest has the required structure."""
    errors: List[str] = []
    parser = configparser.ConfigParser()

    try:
        with manifest_path.open("r", encoding="utf-8") as manifest_file:
            parser.read_file(manifest_file)
    except Exception as exc:
        return [f"Could not read manifest.ini: {exc}"]

    if not parser.has_section("package"):
        return ["manifest.ini missing [package] section"]

    for key in PATENT_MANIFEST_REQUIRED_KEYS:
        actual_value = parser.get("package", key, fallback="").strip()
        if not actual_value:
            errors.append(f"manifest.ini missing required package value: {key}")

    return errors


def discover_patent_batches(parent_folder: str) -> tuple[List[PatentBatch], List[str]]:
    """Recursively discover patent batch directories."""
    root_path = Path(parent_folder).resolve()
    batches: List[PatentBatch] = []
    issues: List[str] = []

    for current_root, dirnames, _ in os.walk(root_path):
        current_dir = Path(current_root)
        dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIRECTORY_NAMES]

        xml_files = sorted(current_dir.glob("*.xml"))
        if not xml_files:
            continue

        manifest_files = sorted(
            path
            for path in current_dir.iterdir()
            if path.is_file() and path.name.lower() == "manifest.ini"
        )
        pdf_files = sorted(current_dir.glob("*.pdf"))

        if len(manifest_files) != 1:
            if len(manifest_files) == 0:
                issues.append(
                    f"Patent batch directory missing manifest.ini: {current_dir}"
                )
            else:
                issues.append(
                    f"Patent batch directory has multiple manifest.ini files: {current_dir}"
                )
            continue

        batches.append(
            PatentBatch(
                base_directory=current_dir,
                pdf_files=pdf_files,
                xml_files=xml_files,
                manifest_file=manifest_files[0],
            )
        )

    return batches, issues


def get_workflow_display_name(workflow: str) -> str:
    """Return a user-facing workflow label."""
    return "Patent" if workflow == WORKFLOW_PATENT else "Photo"


def get_workflow_description(workflow: str) -> str:
    """Return a concise description for the selected workflow."""
    if workflow == WORKFLOW_PATENT:
        return (
            "Package matching PDF + XML patent records with the shared manifest.ini. "
            "Fallback patent search roots are used only when the batch folder lacks a PDF."
        )
    return (
        "Convert source images to TIFF in an output-side scratch workspace, then package the "
        "TIFF, XML, and manifest.ini without changing the source folders."
    )


def scan_folder_for_workflow(folder_path: str, workflow: str) -> FolderScanSummary:
    """Summarize the selected folder for the active workflow."""
    if workflow == WORKFLOW_PATENT:
        patent_batches, discovery_issues = discover_patent_batches(folder_path)
        metadata_count = sum(len(batch.xml_files) for batch in patent_batches)
        asset_count = sum(len(batch.pdf_files) for batch in patent_batches)

        if patent_batches:
            status_text = (
                f"Ready for patent packaging: {len(patent_batches)} batch director"
                f"{'y' if len(patent_batches) == 1 else 'ies'} detected"
            )
            detail_text = (
                f"{metadata_count} XML file(s), {asset_count} local PDF file(s), "
                f"{len(discovery_issues)} discovery warning(s). Output stays in output or staging_output."
            )
            ready = True
        else:
            ready = False
            status_text = "No valid patent batch directories detected"
            detail_text = (
                "Expected at least one folder containing patent XML files "
                "and exactly one shared manifest.ini."
            )
            if discovery_issues:
                detail_text += f" Discovery warnings: {len(discovery_issues)}."

        return FolderScanSummary(
            workflow=workflow,
            ready=ready,
            unit_count=len(patent_batches),
            metadata_count=metadata_count,
            asset_count=asset_count,
            issue_count=len(discovery_issues),
            status_text=status_text,
            detail_text=detail_text,
        )

    photo_sets = find_photo_sets_enhanced(folder_path)
    metadata_count = sum(len(photo_set.xml_files) for photo_set in photo_sets)
    asset_count = sum(len(photo_set.image_files) for photo_set in photo_sets)

    if photo_sets:
        status_text = (
            f"Ready for photo packaging: {len(photo_sets)} photo set"
            f"{'' if len(photo_sets) == 1 else 's'} detected"
        )
        detail_text = (
            f"{metadata_count} XML file(s) and {asset_count} image file(s) available. "
            "Image conversion and renamed package copies stay inside the output workspace."
        )
        ready = True
    else:
        ready = False
        status_text = "No valid photo sets detected"
        detail_text = (
            "Expected image files, XML metadata, and a manifest.ini within "
            "a standard or hierarchical photo set."
        )

    return FolderScanSummary(
        workflow=workflow,
        ready=ready,
        unit_count=len(photo_sets),
        metadata_count=metadata_count,
        asset_count=asset_count,
        issue_count=0,
        status_text=status_text,
        detail_text=detail_text,
    )


def build_patent_pdf_index(search_roots: List[Path]) -> Dict[str, List[Path]]:
    """Index patent PDFs across configured fallback search roots."""
    pdf_index: Dict[str, List[Path]] = defaultdict(list)

    for search_root in search_roots:
        if not search_root.exists() or not search_root.is_dir():
            continue

        for current_root, dirnames, filenames in os.walk(search_root):
            dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIRECTORY_NAMES]

            for filename in filenames:
                file_path = Path(current_root) / filename
                if file_path.suffix.lower() != ".pdf":
                    continue
                pdf_index[normalize_patent_lookup_key(file_path.stem)].append(file_path)

    return dict(pdf_index)


def find_matching_patent_pdf(
    patent_batch: PatentBatch,
    package_id: str,
    fallback_index: Dict[str, List[Path]],
) -> tuple[Optional[Path], Optional[str]]:
    """Find the matching patent PDF, preferring the selected batch folder."""
    lookup_key = normalize_patent_lookup_key(package_id)
    local_matches = [
        pdf_path
        for pdf_path in patent_batch.pdf_files
        if normalize_patent_lookup_key(pdf_path.stem) == lookup_key
    ]

    if len(local_matches) == 1:
        return local_matches[0], None
    if len(local_matches) > 1:
        return None, f"Multiple PDFs found in batch directory for {package_id}"

    fallback_matches = fallback_index.get(lookup_key, [])
    if len(fallback_matches) == 1:
        return fallback_matches[0], None
    if len(fallback_matches) > 1:
        return None, f"Multiple fallback PDFs found for {package_id}"

    return None, f"No PDF found for {package_id}"


def derive_image_candidates_from_iid(iid: str) -> List[str]:
    """Generate possible Image filenames from an IID"""
    base = sanitize_name(iid)
    candidates = []
    # Add all valid extensions
    for ext in VALID_IMAGE_EXTENSIONS:
        candidates.extend(
            [
                f"{base}{ext}",
                f"{base.upper()}{ext.upper()}",  # Case variants
                f"{base}_1{ext}",
                f"{base}_01{ext}",
                f"{base}-1{ext}",
                f"{base}_001{ext}",
            ]
        )
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
        if sanitized_iid in stem.split("_"):
            return img

    # 3) No match found
    return None


def build_pairs_by_iid(
    image_files: List[Path], xml_files: List[Path]
) -> List[FilePair]:
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
        raise ValueError(
            f"Invalid directory structure: {path}. Expected at least 4 levels of directories."
        )


# Enhanced Photo Set Finder Functions
def find_all_files_recursive(
    parent_folder: Path, max_depth: int = 5
) -> Dict[str, List[Path]]:
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
    files = {"image": [], "xml": [], "manifest": []}

    def search_directory(directory: Path, current_depth: int):
        if current_depth > max_depth:
            return

        try:
            for item in directory.iterdir():
                if item.is_file():
                    if item.suffix.lower() in VALID_IMAGE_EXTENSIONS:
                        files["image"].append(item)
                    elif item.suffix.lower() == ".xml":
                        files["xml"].append(item)
                    elif item.name.lower() == "manifest.ini":
                        files["manifest"].append(item)
                elif item.is_dir() and not item.is_symlink():
                    if should_skip_directory(item):
                        continue
                    search_directory(item, current_depth + 1)
        except (PermissionError, OSError) as e:
            logging.warning(f"Cannot access directory {directory}: {e}")

    search_directory(parent_folder, 0)
    logging.debug(
        "Enhanced finder discovered - "
        f"Image: {len(files['image'])}, "
        f"XML: {len(files['xml'])}, "
        f"Manifest: {len(files['manifest'])}"
    )
    return files


def group_files_by_directory(files: Dict[str, List[Path]]) -> List[Dict]:
    """
    Group files by their containing directory.

    Args:
        files: Dictionary of file lists by type

    Returns:
        List of dictionaries containing grouped files
    """
    directory_groups = defaultdict(lambda: {"image": [], "xml": [], "manifest": []})

    # Group files by their parent directory
    for file_type, file_list in files.items():
        for file_path in file_list:
            parent_dir = file_path.parent
            directory_groups[parent_dir][file_type].append(file_path)

    # Convert to list of dictionaries
    file_groups = []
    for directory, grouped_files in directory_groups.items():
        file_group = {
            "directory": directory,
            "image_files": grouped_files["image"],
            "xml_files": grouped_files["xml"],
            "manifest_files": grouped_files["manifest"],
        }
        file_groups.append(file_group)

    logging.debug(f"Grouped files into {len(file_groups)} directory groups")
    return file_groups


def find_hierarchical_sets(
    files: Dict[str, List[Path]], base_path: Path
) -> List[PhotoSet]:
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
    for manifest_file in files["manifest"]:
        manifest_dir = manifest_file.parent

        # Find all images and XML files that are descendants of this manifest's directory
        associated_image = [
            f
            for f in files["image"]
            if manifest_dir in f.parents or f.parent == manifest_dir
        ]
        associated_xml = [
            f
            for f in files["xml"]
            if manifest_dir in f.parents or f.parent == manifest_dir
        ]

        if associated_image and associated_xml:
            # Group by immediate subdirectory if files are not in manifest directory
            if any(f.parent != manifest_dir for f in associated_image + associated_xml):
                # Group files by their immediate directory under manifest_dir
                subdir_groups = defaultdict(lambda: {"image": [], "xml": []})

                for image_file in associated_image:
                    if image_file.parent == manifest_dir:
                        subdir_groups[manifest_dir]["image"].append(image_file)
                    else:
                        # Find the immediate subdirectory under manifest_dir
                        for parent in image_file.parents:
                            if parent.parent == manifest_dir:
                                subdir_groups[parent]["image"].append(image_file)
                                break

                for xml_file in associated_xml:
                    if xml_file.parent == manifest_dir:
                        subdir_groups[manifest_dir]["xml"].append(xml_file)
                    else:
                        # Find the immediate subdirectory under manifest_dir
                        for parent in xml_file.parents:
                            if parent.parent == manifest_dir:
                                subdir_groups[parent]["xml"].append(xml_file)
                                break

                # Create photo sets for each subdirectory that has both types
                for subdir, grouped in subdir_groups.items():
                    if grouped["image"] and grouped["xml"]:
                        photo_set = PhotoSet(
                            base_directory=subdir,
                            image_files=grouped["image"],
                            xml_files=grouped["xml"],
                            manifest_file=manifest_file,
                            structure_type="hierarchical",
                        )
                        hierarchical_sets.append(photo_set)
                        logging.info(
                            "Hierarchical photo set found: "
                            f"{subdir.relative_to(base_path)} "
                            f"(manifest in {manifest_dir.relative_to(base_path)})"
                        )
            else:
                # Files are directly in manifest directory
                photo_set = PhotoSet(
                    base_directory=manifest_dir,
                    image_files=associated_image,
                    xml_files=associated_xml,
                    manifest_file=manifest_file,
                    structure_type="standard",
                )
                hierarchical_sets.append(photo_set)
                logging.debug(
                    f"Standard photo set found via hierarchical search: {manifest_dir.relative_to(base_path)}"
                )

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
        logging.info(
            f"Photo set {photo_set.base_directory} has no images locally - candidate for Global Recovery"
        )
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
        logging.warning(
            f"Invalid photo set {photo_set.base_directory}: No valid XML files with IID"
        )
        return False

    logging.debug(
        f"Valid photo set {photo_set.base_directory}: {len(photo_set.image_files)} Image, {valid_xml_count} valid XML"
    )
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
        namespaces = {"mods": "http://www.loc.gov/mods/v3"}
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


def find_photo_sets_enhanced(
    parent_folder: str, flexible_structure: bool = True
) -> List[PhotoSet]:
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
        if any(ps.base_directory == group["directory"] for ps in photo_sets):
            continue

        # Relaxed condition: If we have XMLs and Manifest, we treat it as a set to process.
        # This allows detecting "Orphaned XMLs" where the image is missing or located elsewhere (Global Recovery).
        if group["xml_files"] and group["manifest_files"]:
            photo_set = PhotoSet(
                base_directory=group["directory"],
                image_files=group["image_files"],  # Might be empty
                xml_files=group["xml_files"],
                manifest_file=group["manifest_files"][
                    0
                ],  # Take first manifest if multiple
                structure_type="standard",
            )
            if validate_photo_set(photo_set):
                photo_sets.append(photo_set)

    # Log structure type breakdown for analytics
    structure_counts = defaultdict(int)
    for ps in photo_sets:
        structure_counts[ps.structure_type] += 1

    if structure_counts:
        structure_summary = ", ".join(
            f"{stype}: {count}" for stype, count in structure_counts.items()
        )
        logging.info(
            f"Enhanced photo set search completed: {len(photo_sets)} sets found ({structure_summary})"
        )
    else:
        logging.info(
            f"Enhanced photo set search completed: {len(photo_sets)} sets found"
        )

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
            photo_set.base_directory,  # directory (Path object)
            photo_set.image_files,  # list of Image files
            photo_set.xml_files,  # list of XML files
            [photo_set.manifest_file],  # list of manifest files (original expects list)
        )
        compatible_results.append(compatible_tuple)

    logging.info(
        f"Total photo sets found: {len(compatible_results)} in {parent_folder}"
    )
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
                3: "Rotated 180Ã‚Â°",
                4: "Mirrored vertically",
                5: "Mirrored horizontally, rotated 90Ã‚Â° CCW",
                6: "Rotated 90Ã‚Â° CW",
                7: "Mirrored horizontally, rotated 90Ã‚Â° CW",
                8: "Rotated 90Ã‚Â° CCW",
            }

            orientation_name = orientation_names.get(
                orientation, f"Unknown ({orientation})"
            )
            logging.debug(
                f"Image {image_path.name} has EXIF orientation: {orientation_name}"
            )

            # Apply orientation corrections
            if orientation == 2:
                # Mirrored horizontally
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                logging.info(f"Applied horizontal flip to {image_path.name}")
            elif orientation == 3:
                # Rotated 180Ã‚Â°
                img = img.rotate(180, expand=True)
                logging.info(f"Applied 180Ã‚Â° rotation to {image_path.name}")
            elif orientation == 4:
                # Mirrored vertically
                img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                logging.info(f"Applied vertical flip to {image_path.name}")
            elif orientation == 5:
                # Mirrored horizontally, then rotated 90Ã‚Â° CCW
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(
                    270, expand=True
                )
                logging.info(
                    f"Applied horizontal flip + 270Ã‚Â° rotation to {image_path.name}"
                )
            elif orientation == 6:
                # Rotated 90Ã‚Â° CW (270Ã‚Â° CCW)
                img = img.rotate(270, expand=True)
                logging.info(f"Applied 270Ã‚Â° rotation to {image_path.name}")
            elif orientation == 7:
                # Mirrored horizontally, then rotated 90Ã‚Â° CW
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(
                    90, expand=True
                )
                logging.info(
                    f"Applied horizontal flip + 90Ã‚Â° rotation to {image_path.name}"
                )
            elif orientation == 8:
                # Rotated 90Ã‚Â° CCW
                img = img.rotate(90, expand=True)
                logging.info(f"Applied 90Ã‚Â° rotation to {image_path.name}")
            elif orientation == 1:
                # Normal orientation - no change needed
                logging.debug(f"Image {image_path.name} has normal orientation")
            else:
                logging.warning(
                    f"Unknown orientation {orientation} for {image_path.name}"
                )

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
                "path": str(image_path),
                "size": img.size,
                "mode": img.mode,
                "format": img.format,
                "orientation_code": orientation,
                "has_exif": exif is not None,
                "needs_correction": orientation != 1,
            }

            # Add human-readable orientation
            orientation_names = {
                1: "Normal",
                2: "Mirrored horizontally",
                3: "Rotated 180Ã‚Â°",
                4: "Mirrored vertically",
                5: "Mirrored horizontally, rotated 90Ã‚Â° CCW",
                6: "Rotated 90Ã‚Â° CW",
                7: "Mirrored horizontally, rotated 90Ã‚Â° CW",
                8: "Rotated 90Ã‚Â° CCW",
            }
            orientation_info["orientation_name"] = orientation_names.get(
                orientation, f"Unknown ({orientation})"
            )

            return orientation_info

    except Exception as e:
        return {"path": str(image_path), "error": str(e), "validation_failed": True}


def debug_orientation_issues(
    folder_path: str, output_csv: str = "orientation_debug.csv"
):
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
        orientation_info["relative_path"] = str(image_file.relative_to(folder))
        results.append(orientation_info)

        if orientation_info.get("needs_correction", False):
            logging.warning(
                f"Image needs orientation correction: {image_file.name} - {orientation_info['orientation_name']}"
            )

    # Write CSV report
    csv_path = folder / output_csv
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        if results:
            fieldnames = results[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    # Summary
    total_images = len(results)
    needs_correction = sum(1 for r in results if r.get("needs_correction", False))

    logging.info("Orientation debug complete:")
    logging.info(f"  Total images: {total_images}")
    logging.info(f"  Need correction: {needs_correction}")
    logging.info(f"  Report saved to: {csv_path}")

    return csv_path


def convert_to_tiff(
    image_path: Path, output_path: Optional[Path] = None, delete_original: bool = True
) -> Optional[Path]:
    """
    Converts an image file (JPG, PNG, PDF, etc.) to .tiff with proper EXIF orientation handling.
    Detects and attempts to fix corrupted files before skipping them.
    Deletes the original file after successful conversion.
    """
    try:
        tiff_path = (
            output_path if output_path is not None else image_path.with_suffix(".tiff")
        )
        tiff_path.parent.mkdir(parents=True, exist_ok=True)

        # Check exclusion to avoid overwriting existing TIFFs if source is TIFF
        if image_path.suffix.lower() in [".tif", ".tiff"]:
            logging.info(
                f"File {image_path} is already TIFF. Skipping conversion logic but verifying."
            )
            try:
                with Image.open(image_path) as img:
                    img.verify()
                if (
                    output_path is not None
                    and image_path.resolve() != output_path.resolve()
                ):
                    copy_file_to_path(image_path, tiff_path)
                    return tiff_path
                return image_path
            except Exception:
                logging.warning(f"Corrupted TIFF detected: {image_path}")
                return None

        # Special handling for PDF
        if image_path.suffix.lower() == ".pdf":
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

                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    img.save(tiff_path, "TIFF", compression="none", dpi=(300, 300))
                    doc.close()

                    if delete_original:
                        image_path.unlink()
                    logging.info(
                        f"Converted PDF {image_path} to {tiff_path} using PyMuPDF (300 DPI)"
                    )
                    return tiff_path
                except Exception as e:
                    logging.warning(
                        f"PyMuPDF conversion failed for {image_path}: {e}. Falling back to Pillow."
                    )

            # Fallback to Pillow (needs Ghostscript)
            try:
                with Image.open(image_path) as img:
                    # PDF might have multiple pages, this typically picks the first one
                    # We need to make sure we are getting a valid image object

                    # Convert to RGB (PDFs are often CMYK or P)
                    img = img.convert("RGB")
                    img.save(tiff_path, "TIFF", compression="none", dpi=(300, 300))

                if delete_original:
                    image_path.unlink()
                logging.info(f"Converted PDF {image_path} to {tiff_path}")
                return tiff_path
            except Exception as e:
                logging.error(
                    f"Failed to convert PDF {image_path}. Ensure Ghostscript or valid PDF decoder is installed: {e}"
                )
                # Fallback strategy not available without external libs (pdf2image)
                return None

        # Standard Image Conversion (JPG, PNG, etc.)
        with Image.open(image_path) as img:
            img.verify()  # Verify if the image is corrupted

        # Re-open for processing
        with Image.open(image_path) as img:
            # Capture original DPI if available
            original_dpi = img.info.get("dpi", (300, 300))

            # Apply EXIF orientation correction
            img = apply_exif_orientation(img, image_path)

            # Convert to RGB (handles RGBA from PNG, CMYK, etc.)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Save as TIFF with high quality, no compression, preserving DPI
            img.save(tiff_path, "TIFF", compression="none", dpi=original_dpi)

        # Delete the original file after successful conversion
        if delete_original:
            image_path.unlink()
            logging.info(f"Converted {image_path} to {tiff_path} and deleted original")
        else:
            logging.info(f"Converted {image_path} to {tiff_path}")
        return tiff_path

    except UnidentifiedImageError as e:
        logging.warning(f"Corrupted file detected: {image_path}. Attempting to fix...")
        # Only try to fix JPGs with the specific fix_corrupted_jpg logic
        if image_path.suffix.lower() in [".jpg", ".jpeg"]:
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
        raise


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


def package_to_zip(
    tiff_path: Path, xml_path: Path, manifest_path: Path, output_folder: Path
) -> Path:
    """
    Creates a zip file containing .tiff, .xml, and a properly formatted manifest.ini.
    """
    try:
        return create_zip_archive(
            [
                (tiff_path, tiff_path.name),
                (xml_path, xml_path.name),
                (manifest_path, manifest_path.name),
            ],
            output_folder,
            tiff_path.stem,
        )
    except Exception as e:
        logging.error(f"Error creating zip archive: {e}")
        raise


def write_csv_row(
    context: BatchContext,
    package_id: str,
    metadata_path: Optional[Path],
    asset_path: Optional[Path],
    status: str,
    action: str,
    notes: str,
) -> None:
    """Write a standardized CSV row when reporting is enabled."""
    if context.csv_writer is not None:
        context.csv_writer.writerow(
            [
                package_id,
                str(metadata_path) if metadata_path else "",
                str(asset_path) if asset_path else "",
                status,
                action,
                notes,
            ]
        )


def process_file_set_with_context(
    files: FilePair, iid: str, manifest_path: Path, context: BatchContext
) -> bool:
    """Process a single photo file set without mutating the source directory."""
    try:
        image_file = files.image
        xml_file = files.xml

        context.logger.info(f"Processing IID {iid} from {manifest_path.parent}")

        if image_file is None:
            write_csv_row(
                context,
                iid,
                xml_file,
                None,
                "WARNING",
                "ORPHANED_XML",
                "No matching Image found",
            )
            return False

        # Validate orientation before processing
        orientation_info = validate_image_orientation(image_file)
        if orientation_info.get("needs_correction", False):
            context.logger.info(
                f"Image {image_file.name} has orientation {orientation_info['orientation_name']} - will be corrected"
            )
            write_csv_row(
                context,
                iid,
                xml_file,
                image_file,
                "INFO",
                "ORIENTATION",
                f"Detected: {orientation_info['orientation_name']}",
            )

        if context.dry_run:
            # Simulate processing steps
            context.logger.info(
                f"DRY RUN: Would convert {image_file.name} to TIFF with orientation correction"
            )
            xml_name = xml_file.name if xml_file else "N/A"
            context.logger.info(f"DRY RUN: Would extract IID {iid} from {xml_name}")
            context.logger.info(f"DRY RUN: Would create ZIP package for {iid}")

            dry_run_notes = "Would process successfully"
            if orientation_info.get("needs_correction", False):
                dry_run_notes += (
                    f" (would correct {orientation_info['orientation_name']})"
                )

            write_csv_row(
                context, iid, xml_file, image_file, "SUCCESS", "DRY_RUN", dry_run_notes
            )
            return True

        if xml_file is None:
            write_csv_row(
                context,
                iid,
                None,
                image_file,
                "ERROR",
                "MISSING_XML",
                "XML file is None",
            )
            return False

        if not manifest_path:
            write_csv_row(
                context,
                iid,
                xml_file,
                image_file,
                "ERROR",
                "NO_MANIFEST",
                "No manifest file found",
            )
            return False

        package_name = sanitize_name(iid)
        package_work_dir = create_package_work_dir(context, package_name)

        try:
            tiff_path = convert_to_tiff(
                image_file,
                output_path=package_work_dir / f"{package_name}.tiff",
                delete_original=False,
            )
            if tiff_path is None:
                write_csv_row(
                    context,
                    iid,
                    xml_file,
                    image_file,
                    "ERROR",
                    "CONVERT_FAILED",
                    "Image to TIFF conversion failed",
                )
                return False

            copied_xml_path = copy_file_to_path(
                xml_file, package_work_dir / f"{package_name}.xml"
            )

            create_zip_archive(
                [
                    (tiff_path, f"{package_name}.tiff"),
                    (copied_xml_path, f"{package_name}.xml"),
                    (manifest_path, manifest_path.name),
                ],
                context.output_dir,
                package_name,
            )

            success_notes = "Successfully packaged"
            if orientation_info.get("needs_correction", False):
                success_notes += f" (corrected {orientation_info['orientation_name']})"
            write_csv_row(
                context,
                iid,
                xml_file,
                image_file,
                "SUCCESS",
                "PROCESSED",
                success_notes,
            )
            return True
        finally:
            cleanup_path(package_work_dir)

    except Exception as e:
        write_csv_row(context, iid, xml_file, image_file, "ERROR", "EXCEPTION", str(e))
        context.logger.error(f"Error processing {iid}: {str(e)}")
        return False


def process_patent_batch_with_context(
    patent_batch: PatentBatch,
    context: BatchContext,
    fallback_pdf_index: Dict[str, List[Path]],
) -> tuple[int, int]:
    """Process a patent batch directory into one ZIP per XML record."""
    success_count = 0
    error_count = 0

    manifest_errors = validate_patent_manifest(patent_batch.manifest_file)
    if manifest_errors:
        for xml_file in patent_batch.xml_files:
            write_csv_row(
                context,
                xml_file.stem,
                xml_file,
                None,
                "ERROR",
                "INVALID_MANIFEST",
                "; ".join(manifest_errors),
            )
        return 0, len(patent_batch.xml_files)

    for xml_file in patent_batch.xml_files:
        iid = extract_identifier_from_xml_by_type(xml_file, "IID")
        if not iid:
            write_csv_row(
                context,
                xml_file.stem,
                xml_file,
                None,
                "ERROR",
                "MISSING_IID",
                "XML is missing identifier type=IID",
            )
            error_count += 1
            continue

        document_id = extract_identifier_from_xml_by_type(xml_file, "document ID")
        if xml_file.stem != iid:
            write_csv_row(
                context,
                iid,
                xml_file,
                None,
                "ERROR",
                "FILENAME_MISMATCH",
                f"XML filename stem '{xml_file.stem}' does not match IID '{iid}'",
            )
            error_count += 1
            continue

        if document_id:
            normalized_document_id = normalize_patent_document_id(document_id)
            if normalized_document_id != iid:
                write_csv_row(
                    context,
                    iid,
                    xml_file,
                    None,
                    "ERROR",
                    "DOCUMENT_ID_MISMATCH",
                    f"Normalized document ID '{normalized_document_id}' does not match IID '{iid}'",
                )
                error_count += 1
                continue

        pdf_path, pdf_error = find_matching_patent_pdf(
            patent_batch, iid, fallback_pdf_index
        )
        if pdf_error or pdf_path is None:
            write_csv_row(
                context,
                iid,
                xml_file,
                None,
                "ERROR",
                "PDF_LOOKUP",
                pdf_error or "No PDF found",
            )
            error_count += 1
            continue

        if context.dry_run:
            write_csv_row(
                context,
                iid,
                xml_file,
                pdf_path,
                "SUCCESS",
                "DRY_RUN",
                "Would create patent ZIP package",
            )
            success_count += 1
            continue

        package_name = sanitize_name(iid)
        try:
            create_zip_archive(
                [
                    (pdf_path, f"{package_name}.pdf"),
                    (xml_file, f"{package_name}.xml"),
                    (patent_batch.manifest_file, "manifest.ini"),
                ],
                context.output_dir,
                package_name,
            )
            write_csv_row(
                context,
                iid,
                xml_file,
                pdf_path,
                "SUCCESS",
                "PROCESSED",
                "Successfully packaged patent ZIP",
            )
            success_count += 1
        except Exception as exc:
            write_csv_row(
                context, iid, xml_file, pdf_path, "ERROR", "EXCEPTION", str(exc)
            )
            context.logger.error(f"Error processing patent {iid}: {exc}")
            error_count += 1

    return success_count, error_count


def batch_process_with_safety_nets(
    folder_path: str,
    dry_run: bool = False,
    staging: bool = False,
    workflow: str = WORKFLOW_PHOTO,
) -> tuple:
    """Enhanced batch process with safety nets, dry-run, and CSV reporting"""
    return _batch_process_core(
        folder_path=folder_path,
        dry_run=dry_run,
        staging=staging,
        workflow=workflow,
    )


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
            raise

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
                output_folder = (
                    path.parents[2] / f"CetamuraUploadBatch_{path.parts[-3]}"
                )
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
        raise


def _batch_process_core(
    folder_path: str,
    dry_run: bool = False,
    staging: bool = False,
    workflow: str = WORKFLOW_PHOTO,
) -> tuple:
    """Current workflow-aware batch processing implementation."""
    logger = logging.getLogger(__name__)

    folder_path_obj = Path(folder_path)
    output_dir = folder_path_obj / ("staging_output" if staging else "output")
    csv_filename = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = (
        output_dir / csv_filename if not dry_run else folder_path_obj / csv_filename
    )

    workflow_name = get_workflow_display_name(workflow)
    mode = "Dry Run Preview" if dry_run else "Staging" if staging else "Production"
    log_user_friendly(f"Starting {workflow_name} {mode} processing")
    log_user_friendly(f"Source folder: {folder_path}")

    if dry_run:
        log_user_friendly(
            "Dry Run Mode - Previewing processing, no files will be changed"
        )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        log_user_friendly(f"{mode} Mode - Output to: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        f"Starting batch process - workflow: {workflow}, dry_run: {dry_run}, staging: {staging}"
    )
    logger.info(f"Source folder: {folder_path}")
    logger.info(f"Output folder: {output_dir}")

    success_count = 0
    error_count = 0
    photo_sets: List[PhotoSet] = []
    patent_batches: List[PatentBatch] = []
    discovery_issues: List[str] = []
    processing_units: List = []
    expected_asset_type = "pdf" if workflow == WORKFLOW_PATENT else "tiff"
    work_root = output_dir / ".work"

    if workflow == WORKFLOW_PATENT:
        patent_batches, discovery_issues = discover_patent_batches(folder_path)
        processing_units = patent_batches
    else:
        photo_sets = find_photo_sets_enhanced(folder_path)
        processing_units = photo_sets

    try:
        log_user_friendly("Running pre-flight checks...")
        preflight = pre_flight_checks(
            processing_units,
            output_dir,
            work_root=work_root,
            required_paths=PATENT_SEARCH_ROOTS if workflow == WORKFLOW_PATENT else None,
        )

        if not processing_units and not discovery_issues:
            preflight.blockers.append(f"No {workflow_name.lower()} batch content found")

        if not preflight.passed:
            for blocker in preflight.blockers:
                log_user_friendly(f"[BLOCKER] {blocker}")
                logger.error(f"Pre-flight check failed: {blocker}")
            raise RuntimeError("Pre-flight checks failed. Aborting batch processing.")

        for warning in preflight.warnings:
            log_user_friendly(f"[WARNING] Pre-flight: {warning}")
            logger.warning(f"Pre-flight warning: {warning}")

        for issue in discovery_issues:
            log_user_friendly(f"[WARNING] Discovery: {issue}")
            logger.warning(issue)

        log_user_friendly(
            f"[PASS] Pre-flight checks passed. Disk space: {preflight.disk_space_gb:.2f} GB available"
        )
        logger.info(
            f"Pre-flight checks passed: {preflight.disk_space_gb:.2f} GB available, "
            f"{preflight.required_space_gb:.2f} GB estimated"
        )
    except Exception as e:
        logger.warning(f"Pre-flight checks skipped due to error: {e}")
        log_user_friendly(f"[WARNING] Pre-flight checks skipped: {e}")

    run_work_dir = (
        create_run_work_dir(output_dir) if not dry_run else work_root / "dry_run"
    )

    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(
                [
                    "Package_ID",
                    "Metadata_Path",
                    "Asset_Path",
                    "Status",
                    "Action",
                    "Notes",
                ]
            )

            context = BatchContext(
                output_dir=output_dir,
                dry_run=dry_run,
                staging=staging,
                csv_path=csv_path,
                csv_writer=csv_writer,
                logger=logger,
                workflow=workflow,
                run_work_dir=run_work_dir,
                patent_search_roots=PATENT_SEARCH_ROOTS,
            )

            try:
                if workflow == WORKFLOW_PATENT:
                    logger.info(
                        f"Patent detection found {len(patent_batches)} batch unit(s)"
                    )
                    log_user_friendly(
                        f"Found {len(patent_batches)} patent batch directorie(s) to process"
                    )

                    fallback_pdf_index = build_patent_pdf_index(
                        context.patent_search_roots
                    )
                    if fallback_pdf_index:
                        logger.info(
                            f"Patent fallback index built with {len(fallback_pdf_index)} keys"
                        )

                    for issue in discovery_issues:
                        write_csv_row(
                            context, "", None, None, "WARNING", "DISCOVERY", issue
                        )

                    for patent_batch in patent_batches:
                        batch_success, batch_error = process_patent_batch_with_context(
                            patent_batch,
                            context,
                            fallback_pdf_index,
                        )
                        success_count += batch_success
                        error_count += batch_error
                else:
                    log_user_friendly(f"Found {len(photo_sets)} photo sets to process")
                    logger.info(
                        f"Photo detection found {len(photo_sets)} batch unit(s)"
                    )

                    global_image_index = {}
                    try:
                        scan_results = find_all_files_recursive(Path(folder_path))
                        for fpath in scan_results.get("image", []):
                            global_image_index[fpath.stem] = fpath
                        logger.info(
                            f"Global index built with {len(global_image_index)} images"
                        )
                    except Exception as idx_err:
                        logger.warning(f"Failed to build global index: {idx_err}")

                    for photo_set in photo_sets:
                        for xml_file in photo_set.xml_files:
                            try:
                                iid = extract_iid_from_xml(xml_file)
                                matching_image = None

                                for image_file in photo_set.image_files:
                                    if image_file.stem == xml_file.stem:
                                        matching_image = image_file
                                        break

                                if matching_image is None:
                                    for image_file in photo_set.image_files:
                                        if iid in image_file.name:
                                            matching_image = image_file
                                            logger.info(
                                                "Smart Match: Found image "
                                                f"{image_file.name} for XML "
                                                f"{xml_file.name} based on IID {iid}"
                                            )
                                            break

                                if (
                                    matching_image is None
                                    and len(photo_set.image_files) == 1
                                    and len(photo_set.xml_files) == 1
                                ):
                                    matching_image = photo_set.image_files[0]
                                    logger.info(
                                        "Smart Match: Assumed pairing for lone files - "
                                        f"Image {matching_image.name} and XML {xml_file.name}"
                                    )

                                if (
                                    matching_image is None
                                    and xml_file.stem in global_image_index
                                ):
                                    matching_image = global_image_index[xml_file.stem]
                                    logger.warning(
                                        "Strategy 4: Recovered image "
                                        f"{matching_image.name} from DIFFERENT "
                                        f"directory: {matching_image.parent}"
                                    )
                                    if context.csv_writer is not None:
                                        write_csv_row(
                                            context,
                                            iid,
                                            xml_file,
                                            matching_image,
                                            "WARNING",
                                            "CROSS_LINK",
                                            f"Image recovered from: {matching_image.parent.name}",
                                        )

                                if matching_image is None:
                                    logger.warning(
                                        f"No matching Image found for XML {xml_file.name} (IID: {iid})"
                                    )
                                    if context.csv_writer is not None:
                                        write_csv_row(
                                            context,
                                            iid,
                                            xml_file,
                                            None,
                                            "WARNING",
                                            "MISSING_IMAGE",
                                            "No matching Image file found",
                                        )
                                    continue

                                files = FilePair(
                                    xml=xml_file, image=matching_image, iid=iid
                                )
                                success = process_file_set_with_context(
                                    files, iid, photo_set.manifest_file, context
                                )
                                if success:
                                    success_count += 1
                                else:
                                    error_count += 1

                            except Exception as e:
                                iid = "UNKNOWN"
                                try:
                                    iid = (
                                        extract_iid_from_xml(xml_file)
                                        if xml_file
                                        else "UNKNOWN"
                                    )
                                except Exception:
                                    pass
                                logger.error(
                                    f"Error processing file {xml_file.name} (IID: {iid}): {str(e)}",
                                    exc_info=True,
                                )
                                if context.csv_writer is not None:
                                    write_csv_row(
                                        context,
                                        iid,
                                        xml_file,
                                        None,
                                        "ERROR",
                                        "PROCESSING",
                                        str(e),
                                    )
                                error_count += 1

            except Exception as e:
                import traceback

                traceback_str = traceback.format_exc()
                log_user_friendly(
                    f"Error during {workflow_name.lower()} batch processing: {e}"
                )
                logger.error(f"Error in batch processing: {str(e)}\n{traceback_str}")
                print(f"\n{'='*60}\nFULL TRACEBACK:\n{'='*60}")
                print(traceback_str)
                print(f"{'='*60}\n")
                if context.csv_writer is not None:
                    write_csv_row(
                        context,
                        "",
                        Path(folder_path),
                        None,
                        "ERROR",
                        "DETECTION",
                        str(e),
                    )
                error_count += 1

            logger.info(
                f"Batch process completed - Success: {success_count}, Errors: {error_count}"
            )
            if context.csv_writer is not None:
                context.csv_writer.writerow(
                    [
                        "SUMMARY",
                        "",
                        "",
                        "SUMMARY",
                        f"Success: {success_count}",
                        f"Errors: {error_count}; Dry run: {dry_run}; Workflow: {workflow}",
                    ]
                )

        cleanup_path(run_work_dir)
        remove_empty_directory(work_root)

        try:
            validation_result = validate_batch_output(
                photo_sets=processing_units,
                output_dir=output_dir,
                success_count=success_count,
                dry_run=dry_run,
                expected_asset_type=expected_asset_type,
                work_root=work_root,
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
                if dry_run:
                    log_user_friendly(
                        "[PASS] Dry-run validation: no ZIPs created, as expected"
                    )
                    logger.info(
                        "[PASS] Dry-run validation: no ZIPs created, as expected"
                    )
                else:
                    log_user_friendly(
                        f"[PASS] Post-processing validation: {validation_result.valid_zips} valid ZIPs"
                    )
                    logger.info(
                        f"[PASS] Post-processing validation: {validation_result.valid_zips} valid ZIPs"
                    )

            if not dry_run:
                reconciliation = generate_reconciliation_report(
                    photo_sets=processing_units,
                    csv_path=csv_path,
                    output_dir=output_dir,
                    expected_asset_type=expected_asset_type,
                    work_root=work_root,
                )

                log_user_friendly("=== Reconciliation Report ===")
                log_user_friendly(f"Input XML files: {reconciliation.input_xml_count}")
                log_user_friendly(
                    f"CSV SUCCESS rows: {reconciliation.csv_success_rows}"
                )
                log_user_friendly(
                    f"Actual ZIP files: {reconciliation.actual_zip_count}"
                )
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
                    log_user_friendly(
                        f"Orphaned files found: {len(reconciliation.orphaned_files)}"
                    )
                    logger.warning(
                        f"Orphaned files found: {len(reconciliation.orphaned_files)}"
                    )
                    for orphaned in reconciliation.orphaned_files[:5]:
                        log_user_friendly(f"  - {orphaned}")
                        logger.warning(f"  - {orphaned}")
        except Exception as e:
            logger.warning(f"Post-processing validation skipped due to error: {e}")
            log_user_friendly(f"[WARNING] Post-processing validation skipped: {e}")

        return success_count, error_count, csv_path

    except Exception as e:
        cleanup_path(run_work_dir)
        remove_empty_directory(work_root)
        logger.error(f"Critical error in batch process: {str(e)}")
        raise


def _open_path_in_default_app(target_path: Path) -> Path:
    """Open a local path using the platform default application."""
    resolved_path = target_path.resolve()
    system = platform.system().lower()

    if system == "windows":
        os.startfile(str(resolved_path))
    elif system == "darwin":
        subprocess.run(["open", str(resolved_path)], check=False)
    else:
        subprocess.run(["xdg-open", str(resolved_path)], check=False)

    return resolved_path


def view_log_file():
    """Open the technical log file in the default system application."""
    try:
        if log_file.exists():
            resolved_path = _open_path_in_default_app(log_file)
            logging.info(f"Opened log file: {resolved_path}")
        else:
            messagebox.showwarning(
                "Log File Not Found", f"Log file does not exist: {log_file}"
            )
            logging.warning("Attempted to open non-existent log file")
    except Exception as e:
        messagebox.showerror("Error Opening Log", f"Could not open log file: {e}")
        logging.error(f"Error opening log file: {e}")


def view_user_friendly_log():
    """Open the user-facing summary log in the default system application."""
    summary_log_file = Path("batch_process_summary.log")
    try:
        if summary_log_file.exists():
            resolved_path = _open_path_in_default_app(summary_log_file)
            logging.info(f"Opened summary log file: {resolved_path}")
        else:
            messagebox.showwarning(
                "Summary Log Not Found",
                f"Summary log file does not exist: {summary_log_file}",
            )
            logging.warning("Attempted to open non-existent summary log file")
    except Exception as e:
        messagebox.showerror(
            "Error Opening Summary Log", f"Could not open summary log file: {e}"
        )
        logging.error(f"Error opening summary log file: {e}")


def get_active_workflow() -> str:
    """Read the current workflow from the main-window selector."""
    if workflow_selector_var is None:
        return WORKFLOW_PHOTO
    try:
        return workflow_selector_var.get()
    except Exception:
        return WORKFLOW_PHOTO


def set_status_text(message: str, color: str = TEXT_PRIMARY):
    """Update the status line with consistent styling."""
    if status_label:
        status_label.config(text=f"Status: {message}", fg=color)


def reset_progress_state(message: str = "Idle"):
    """Reset the coarse progress indicator used by the GUI."""
    if progress:
        try:
            progress.stop()
        except Exception as exc:
            logging.debug(f"Progress bar stop skipped during reset: {exc}")
        progress.configure(mode="determinate", value=0)
    if progress_label:
        progress_label.config(text=message, fg=TEXT_MUTED)


def refresh_folder_selection_summary():
    """Refresh workflow-specific readiness details for the currently selected folder."""
    workflow = get_active_workflow()
    workflow_name = get_workflow_display_name(workflow)

    if workflow_description_label:
        workflow_description_label.config(text=get_workflow_description(workflow))
    if btn_select:
        btn_select.config(text=f"Select {workflow_name} Folder")
    if btn_process:
        btn_process.config(text=f"Review and Run {workflow_name} Batch")

    if selected_folder_path is None:
        if label:
            label.config(text="No folder selected yet", fg=TEXT_MUTED)
        if folder_summary_label:
            folder_summary_label.config(
                text=(
                    f"Choose a folder to preview {workflow_name.lower()} readiness. "
                    "Dry Run, Staging, and log detail are configured when you start a run."
                ),
                fg=TEXT_MUTED,
            )
        if btn_process:
            btn_process.config(state="disabled")
        set_status_text(
            f"Choose a {workflow_name.lower()} folder to begin.", TEXT_MUTED
        )
        reset_progress_state("Ready")
        return

    try:
        summary = scan_folder_for_workflow(str(selected_folder_path), workflow)
        if label:
            label.config(text=str(selected_folder_path), fg=TEXT_PRIMARY)
        if folder_summary_label:
            folder_summary_label.config(
                text=f"{summary.status_text}\n{summary.detail_text}",
                fg=TEXT_PRIMARY if summary.ready else WARNING_COLOR,
            )
        if btn_process:
            btn_process.config(state="normal" if summary.ready else "disabled")
        set_status_text(
            summary.status_text,
            TEXT_PRIMARY if summary.ready else WARNING_COLOR,
        )
        reset_progress_state("Ready")
    except Exception as e:
        if label:
            label.config(text=str(selected_folder_path), fg=WARNING_COLOR)
        if folder_summary_label:
            folder_summary_label.config(
                text="The selected folder could not be scanned. Review the technical log for details.",
                fg=WARNING_COLOR,
            )
        if btn_process:
            btn_process.config(state="disabled")
        set_status_text("Error scanning selected folder", WARNING_COLOR)
        reset_progress_state("Scan failed")
        logging.error(
            f"Error scanning folder {selected_folder_path} for workflow {workflow}: {e}"
        )


def on_workflow_changed():
    """Handle workflow changes from the main-window selector."""
    refresh_folder_selection_summary()


def select_folder():
    """Prompt for the source folder and refresh the readiness summary."""
    global selected_folder_path

    folder_selected = filedialog.askdirectory()
    if folder_selected:
        selected_folder_path = Path(folder_selected)
    refresh_folder_selection_summary()


# Function to display instructions in a new window
def show_instructions():
    return _show_instructions_final()


def _show_instructions_final():
    """Display updated workflow guidance."""
    try:
        instruction_text = """CETAMURA BATCH PACKAGING TOOL
=============================

This tool creates ingest-ready ZIP packages for both photo and patent workflows.
All generated files are written only to output folders. Source folders stay read-only.

WORKFLOWS
---------
Photo workflow
- Detects photo sets with image files, XML metadata, and manifest.ini.
- Converts source images to TIFF inside an output-side scratch workspace.
- Packages TIFF + XML + manifest.ini into ZIP files named from the IID.

Patent workflow
- Detects directories containing patent XML files and one shared manifest.ini.
- Uses the XML IID as the package name.
- Packages PDF + XML + manifest.ini into ZIP files named from the patent ID.
- Falls back to configured patent search roots only when the selected folder lacks a matching PDF.

RUN MODES
---------
Dry Run
- Creates only the CSV report.
- Performs discovery and validation without creating ZIPs.

Staging
- Writes ZIPs and reports to staging_output.
- Leaves the selected source folder unchanged.

Production
- Writes ZIPs and reports to output.
- Leaves the selected source folder unchanged.

TYPICAL FLOW
------------
1. Choose the workflow on the main screen.
2. Select the folder you want to package.
3. Review the readiness summary shown in the main window.
4. Click Review and Run to choose Dry Run, Staging, or Production.
5. Review the CSV report and the generated ZIP files in the output folder.

OUTPUTS
-------
- ZIP files named from the package ID
- CSV processing report
- batch_tool.log for technical details
- batch_process_summary.log for user-facing run notes
"""

        instructions_window = Toplevel(root_window)
        instructions_window.title("How to Use")
        instructions_window.geometry("760x620")
        instructions_window.configure(bg=APP_BG)
        instructions_window.transient(root_window)

        header = Label(
            instructions_window,
            text="Workflow Guide",
            bg=APP_BG,
            fg=TEXT_PRIMARY,
            font=("Georgia", 18, "bold"),
        )
        header.pack(anchor="w", padx=18, pady=(18, 6))

        subheader = Label(
            instructions_window,
            text="Photo and patent packaging now share the same non-mutating output model.",
            bg=APP_BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 10),
            justify="left",
        )
        subheader.pack(anchor="w", padx=18, pady=(0, 12))

        scrollbar = Scrollbar(instructions_window)
        scrollbar.pack(side="right", fill="y", pady=(0, 18), padx=(0, 18))

        text_area = Text(
            instructions_window,
            wrap="word",
            yscrollcommand=scrollbar.set,
            bg=SURFACE_BG,
            fg=TEXT_PRIMARY,
            relief="flat",
            padx=18,
            pady=18,
            font=("Consolas", 10),
        )
        text_area.pack(expand=True, fill="both", padx=(18, 0), pady=(0, 18))
        text_area.insert("1.0", instruction_text)
        text_area.config(state="disabled")
        scrollbar.config(command=text_area.yview)
    except Exception as e:
        logging.error(f"Error displaying instructions: {e}")


def show_processing_options_dialog():
    return _show_processing_options_dialog_final()


def _show_processing_options_dialog_final():
    """Show the run-settings dialog."""
    from tkinter import (
        Toplevel,
        BooleanVar,
        Checkbutton,
        Frame as TkFrame,
        Button as TkButton,
    )

    workflow = get_active_workflow()
    workflow_name = get_workflow_display_name(workflow)
    folder_text = (
        str(selected_folder_path) if selected_folder_path else "No folder selected"
    )

    dialog = Toplevel(root_window)
    dialog.title("Run Settings")
    dialog.geometry("520x560")
    dialog.configure(bg=APP_BG)
    dialog.transient(root_window)
    dialog.grab_set()
    dialog.resizable(False, False)

    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (520 // 2)
    y = (dialog.winfo_screenheight() // 2) - (560 // 2)
    dialog.geometry(f"520x560+{x}+{y}")

    dry_run_var = BooleanVar(value=False)
    staging_var = BooleanVar(value=False)
    advanced_logs_var = BooleanVar(value=False)
    result = {"cancelled": True}

    shell_frame = TkFrame(dialog, bg=APP_BG)
    shell_frame.pack(fill="both", expand=True, padx=18, pady=18)

    title_label = Label(
        shell_frame,
        text="Run Settings",
        bg=APP_BG,
        fg=TEXT_PRIMARY,
        font=("Georgia", 18, "bold"),
    )
    title_label.pack(anchor="w")

    subtitle_label = Label(
        shell_frame,
        text=f"{workflow_name} workflow selected. Source files will remain unchanged in every mode.",
        bg=APP_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=460,
    )
    subtitle_label.pack(anchor="w", pady=(4, 14))

    summary_card = TkFrame(shell_frame, bg=CARD_BG, bd=1, relief="solid")
    summary_card.pack(fill="x", pady=(0, 12))

    Label(
        summary_card,
        text="Selected Folder",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI Semibold", 9),
    ).pack(anchor="w", padx=14, pady=(12, 2))
    Label(
        summary_card,
        text=folder_text,
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=440,
    ).pack(anchor="w", padx=14, pady=(0, 6))
    Label(
        summary_card,
        text=get_workflow_description(workflow),
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 9),
        justify="left",
        wraplength=440,
    ).pack(anchor="w", padx=14, pady=(0, 12))

    options_card = TkFrame(shell_frame, bg=SURFACE_BG, bd=1, relief="solid")
    options_card.pack(fill="both", expand=True)

    warning_label = Label(
        options_card,
        text="",
        bg=SURFACE_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=430,
    )
    warning_label.pack(anchor="w", padx=14, pady=(14, 8))

    def make_toggle(title: str, description: str, variable: BooleanVar, command=None):
        block = TkFrame(options_card, bg=SURFACE_BG)
        block.pack(fill="x", padx=14, pady=(0, 12))
        check = Checkbutton(
            block,
            text=title,
            variable=variable,
            command=command,
            bg=SURFACE_BG,
            activebackground=SURFACE_BG,
            fg=TEXT_PRIMARY,
            selectcolor=CARD_BG,
            font=("Segoe UI Semibold", 11),
            anchor="w",
            justify="left",
        )
        check.pack(anchor="w")
        Label(
            block,
            text=description,
            bg=SURFACE_BG,
            fg=TEXT_MUTED,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=410,
        ).pack(anchor="w", padx=24, pady=(2, 0))

    def check_mode_conflict():
        dry_run = dry_run_var.get()
        staging = staging_var.get()

        if dry_run and staging:
            warning_label.config(
                text=(
                    "Dry Run overrides Staging. No ZIP files will be created, "
                    "and the run will produce only the CSV preview report."
                ),
                fg=WARNING_COLOR,
            )
            proceed_btn.config(text="Start Dry Run")
        elif dry_run:
            warning_label.config(
                text="Preview the run without creating ZIP files.",
                fg=TEXT_PRIMARY,
            )
            proceed_btn.config(text="Start Dry Run")
        elif staging:
            warning_label.config(
                text="Create reviewable ZIP files in staging_output.",
                fg=TEXT_PRIMARY,
            )
            proceed_btn.config(text="Start Staging Run")
        else:
            warning_label.config(
                text="Create final ZIP files in output.",
                fg=TEXT_PRIMARY,
            )
            proceed_btn.config(text="Start Production Run")

    make_toggle(
        "Dry Run",
        "Run discovery and validation only. This mode generates the CSV report but creates no ZIP files.",
        dry_run_var,
        check_mode_conflict,
    )
    make_toggle(
        "Staging",
        "Write ZIP files and reports to staging_output so the batch can be reviewed before production.",
        staging_var,
        check_mode_conflict,
    )
    make_toggle(
        "Advanced Logs",
        "Include detailed debug logging in the technical log for troubleshooting and deeper review.",
        advanced_logs_var,
    )

    button_row = TkFrame(shell_frame, bg=APP_BG)
    button_row.pack(fill="x", pady=(14, 0))

    def on_proceed():
        dry_run = dry_run_var.get()
        staging = staging_var.get()

        if dry_run and staging:
            response = messagebox.askyesno(
                "Run Settings",
                (
                    "Dry Run and Staging are both selected.\n\n"
                    "Dry Run will take precedence, so no ZIP files will be created.\n\n"
                    "Continue with Dry Run?"
                ),
                parent=dialog,
            )
            if not response:
                return

        result["cancelled"] = False
        result["dry_run"] = dry_run
        result["staging"] = staging if not dry_run else False
        result["advanced_logs"] = advanced_logs_var.get()
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    proceed_btn = TkButton(
        button_row,
        text="Start Production Run",
        command=on_proceed,
        bg=ACCENT_BG,
        fg=SURFACE_BG,
        activebackground=ACCENT_BG_DARK,
        activeforeground=SURFACE_BG,
        relief="flat",
        padx=16,
        pady=10,
        font=("Segoe UI Semibold", 10),
    )
    proceed_btn.pack(side="left")

    cancel_btn = TkButton(
        button_row,
        text="Cancel",
        command=on_cancel,
        bg=DISABLED_BG,
        fg=TEXT_PRIMARY,
        activebackground=ACCENT_ALT,
        activeforeground=TEXT_PRIMARY,
        relief="flat",
        padx=16,
        pady=10,
        font=("Segoe UI", 10),
    )
    cancel_btn.pack(side="left", padx=(10, 0))

    check_mode_conflict()
    dialog.wait_window()
    return result


def start_batch_process():
    return _start_batch_process_final()


def _start_batch_process_final():
    """Start the selected workflow using the refreshed UI state."""
    if selected_folder_path is None or not selected_folder_path.is_dir():
        messagebox.showerror(
            "Error", "Please select a valid folder before starting a run."
        )
        return

    options = show_processing_options_dialog()
    if options["cancelled"]:
        return

    folder = str(selected_folder_path)
    dry_run = options.get("dry_run", False)
    staging = options.get("staging", False)
    advanced_logs = options.get("advanced_logs", False)
    workflow = get_active_workflow()

    configure_logging_level(advanced_logs)

    workflow_label = get_workflow_display_name(workflow)
    mode_text = (
        f"{workflow_label} Dry Run"
        if dry_run
        else f"{workflow_label} Staging" if staging else f"{workflow_label} Production"
    )

    if btn_select:
        btn_select.config(state="disabled")
    if btn_process:
        btn_process.config(state="disabled")
    if progress:
        progress.configure(mode="indeterminate", value=0)
        progress.start(12)
    if progress_label:
        progress_label.config(text=f"{mode_text} running", fg=TEXT_PRIMARY)
    set_status_text(f"{mode_text} in progress", TEXT_PRIMARY)

    logging.info(
        f"Batch processing started for folder: {folder} "
        f"(workflow={workflow}, dry_run={dry_run}, staging={staging})"
    )

    def finish_ui(success: bool, status_message: str):
        if progress:
            try:
                progress.stop()
            except Exception as exc:
                logging.debug(f"Progress bar stop skipped during finish_ui: {exc}")
            progress.configure(mode="determinate", value=100 if success else 0)
        if progress_label:
            progress_label.config(
                text="Run complete" if success else "Run failed",
                fg=SUCCESS_COLOR if success else WARNING_COLOR,
            )
        set_status_text(status_message, SUCCESS_COLOR if success else WARNING_COLOR)
        if btn_select:
            btn_select.config(state="normal")
        if btn_process:
            btn_process.config(state="normal")

    def run_process():
        try:
            success_count, error_count, csv_path = batch_process_with_safety_nets(
                folder,
                dry_run,
                staging,
                workflow=workflow,
            )

            mode_desc = f"{workflow_label.upper()} - " + (
                "DRY RUN - " if dry_run else "STAGING - " if staging else ""
            )
            if dry_run:
                success_message = (
                    f"{mode_desc}Processing simulation completed.\n\n"
                    f"Would process: {success_count} item(s)\n"
                    f"Issues found: {error_count} item(s)\n\n"
                    f"Review the report: {csv_path}\n\n"
                    "No ZIP files were created."
                )
            else:
                success_message = (
                    f"{mode_desc}Processing completed.\n\n"
                    f"Successfully processed: {success_count} item(s)\n"
                    f"Errors: {error_count} item(s)\n\n"
                    f"Detailed report: {csv_path}"
                )
                if staging:
                    success_message = success_message.replace(
                        "Detailed report:",
                        "Output saved to staging_output.\nDetailed report:",
                    )

            logging.info(
                f"Batch processing completed - Success: {success_count}, Errors: {error_count}"
            )
            if root_window:
                root_window.after(
                    0, lambda: finish_ui(True, f"{mode_text} completed successfully")
                )
                root_window.after(
                    0, lambda: messagebox.showinfo("Run Complete", success_message)
                )

        except Exception as e:
            error_msg = f"An error occurred during processing:\n{str(e)}"
            logging.error(f"Error during batch processing: {e}")
            if root_window:
                root_window.after(0, lambda: finish_ui(False, f"{mode_text} failed"))
                root_window.after(0, lambda: messagebox.showerror("Error", error_msg))

    threading.Thread(target=run_process, daemon=True).start()


def main():
    return _main_final()


def _main_final():
    """Build and run the refreshed main window."""
    global root_window, btn_select, btn_process, progress, progress_label, status_label, label
    global folder_summary_label, workflow_description_label, selected_folder_path, workflow_selector_var

    selected_folder_path = None
    root_window = Tk()
    root_window.title("Cetamura Batch Ingest Tool")
    root_window.geometry("860x680")
    root_window.minsize(820, 620)
    root_window.configure(bg=APP_BG)

    try:
        icon_path = Path(__file__).resolve().parent / "../assets/app.ico"
        if icon_path.exists():
            icon_image = Image.open(icon_path).resize(
                (32, 32), Image.Resampling.LANCZOS
            )
            icon_photo = ImageTk.PhotoImage(icon_image)
            root_window.wm_iconphoto(False, icon_photo)  # type: ignore
            setattr(root_window, "_icon_ref", icon_photo)
    except Exception as e:
        logging.debug(f"Optional window icon could not be loaded: {e}")

    logo_photo = None
    try:
        logo_path = Path(__file__).resolve().parent / "../assets/app.png"
        if logo_path.exists():
            logo_image = Image.open(logo_path).resize(
                (200, 50), Image.Resampling.LANCZOS
            )
            logo_photo = ImageTk.PhotoImage(logo_image)
            setattr(root_window, "_logo_ref", logo_photo)
    except Exception as e:
        logging.debug(f"Optional logo could not be loaded: {e}")

    style = Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("App.TFrame", background=APP_BG)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("Hero.TFrame", background=ACCENT_BG)
    style.configure(
        "Primary.TButton",
        padding=(16, 10),
        font=("Segoe UI Semibold", 10),
        background=ACCENT_BG,
        foreground=SURFACE_BG,
        borderwidth=0,
    )
    style.map(
        "Primary.TButton",
        background=[("active", ACCENT_BG_DARK), ("disabled", DISABLED_BG)],
        foreground=[("disabled", SURFACE_BG)],
    )
    style.configure(
        "Secondary.TButton",
        padding=(12, 9),
        font=("Segoe UI", 10),
        background=ACCENT_ALT,
        foreground=TEXT_PRIMARY,
        borderwidth=0,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", ACCENT_ALT_SOFT), ("disabled", DISABLED_BG)],
        foreground=[("disabled", TEXT_MUTED)],
    )
    style.configure(
        "Workflow.TRadiobutton",
        background=CARD_BG,
        foreground=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 10),
    )
    style.map("Workflow.TRadiobutton", background=[("active", CARD_BG)])
    style.configure(
        "Accent.Horizontal.TProgressbar",
        background=ACCENT_ALT,
        troughcolor=ACCENT_ALT_SOFT,
        lightcolor=ACCENT_ALT,
        darkcolor=ACCENT_ALT,
        thickness=14,
    )

    main_frame = Frame(root_window, style="App.TFrame")
    main_frame.pack(fill="both", expand=True)

    hero_frame = Frame(main_frame, style="Hero.TFrame")
    hero_frame.pack(fill="x", padx=22, pady=(22, 14))

    if logo_photo:
        logo_label = Label(hero_frame, image=logo_photo, bg=ACCENT_BG)
        logo_label.pack(anchor="ne", padx=18, pady=(16, 0))

    badge_label = Label(
        hero_frame,
        text="PHOTO + PATENT WORKFLOWS",
        bg=ACCENT_ALT,
        fg=TEXT_PRIMARY,
        font=("Segoe UI Semibold", 9),
        padx=10,
        pady=4,
    )
    badge_label.pack(anchor="w", padx=18, pady=(18, 8))

    title_label = Label(
        hero_frame,
        text="Cetamura Batch Ingest",
        bg=ACCENT_BG,
        fg=SURFACE_BG,
        font=("Georgia", 24, "bold"),
    )
    title_label.pack(anchor="w", padx=18)

    subtitle_label = Label(
        hero_frame,
        text=(
            "Non-mutating staging and production packaging for photo sets and patent batches. "
            "Select a workflow, scan a folder, then choose how you want to run it."
        ),
        bg=ACCENT_BG,
        fg=ACCENT_ALT_SOFT,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=760,
    )
    subtitle_label.pack(anchor="w", padx=18, pady=(8, 18))

    content_frame = Frame(main_frame, style="App.TFrame")
    content_frame.pack(fill="both", expand=True, padx=22, pady=(0, 20))

    workflow_card = Frame(content_frame, style="Card.TFrame")
    workflow_card.pack(fill="x", pady=(0, 12))

    Label(
        workflow_card,
        text="Workflow",
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        font=("Georgia", 16, "bold"),
    ).pack(anchor="w", padx=18, pady=(16, 4))
    Label(
        workflow_card,
        text="Choose the workflow before selecting a folder so the readiness scan matches the batch type.",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=760,
    ).pack(anchor="w", padx=18, pady=(0, 12))

    workflow_selector_var = StringVar(value=WORKFLOW_PHOTO)
    workflow_options = Frame(workflow_card, style="Card.TFrame")
    workflow_options.pack(fill="x", padx=18, pady=(0, 10))
    workflow_options.columnconfigure(0, weight=1)
    workflow_options.columnconfigure(1, weight=1)

    photo_option = Frame(workflow_options, style="Card.TFrame")
    photo_option.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    patent_option = Frame(workflow_options, style="Card.TFrame")
    patent_option.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    Radiobutton(
        photo_option,
        text="Photo Workflow",
        variable=workflow_selector_var,
        value=WORKFLOW_PHOTO,
        command=on_workflow_changed,
        style="Workflow.TRadiobutton",
    ).pack(anchor="w")
    Label(
        photo_option,
        text="Package image + XML pairs as TIFF-based ingest ZIPs.",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 9),
        justify="left",
        wraplength=320,
    ).pack(anchor="w", padx=22, pady=(2, 0))

    Radiobutton(
        patent_option,
        text="Patent Workflow",
        variable=workflow_selector_var,
        value=WORKFLOW_PATENT,
        command=on_workflow_changed,
        style="Workflow.TRadiobutton",
    ).pack(anchor="w")
    Label(
        patent_option,
        text="Package PDF + XML patent pairs using the shared manifest.ini.",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 9),
        justify="left",
        wraplength=320,
    ).pack(anchor="w", padx=22, pady=(2, 0))

    workflow_description_label = Label(
        workflow_card,
        text="",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=760,
    )
    workflow_description_label.pack(anchor="w", padx=18, pady=(2, 16))

    selection_card = Frame(content_frame, style="Card.TFrame")
    selection_card.pack(fill="x", pady=(0, 12))

    Label(
        selection_card,
        text="Selected Folder",
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        font=("Georgia", 16, "bold"),
    ).pack(anchor="w", padx=18, pady=(16, 4))

    label = Label(
        selection_card,
        text="No folder selected yet",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI Semibold", 10),
        justify="left",
        wraplength=760,
    )
    label.pack(anchor="w", padx=18)

    folder_summary_label = Label(
        selection_card,
        text="",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=760,
    )
    folder_summary_label.pack(anchor="w", padx=18, pady=(8, 16))

    actions_card = Frame(content_frame, style="Card.TFrame")
    actions_card.pack(fill="x", pady=(0, 12))

    Label(
        actions_card,
        text="Actions",
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        font=("Georgia", 16, "bold"),
    ).pack(anchor="w", padx=18, pady=(16, 4))
    Label(
        actions_card,
        text=(
            "Use Select Folder to scan readiness. Review and Run opens the "
            "mode picker for Dry Run, Staging, and Production."
        ),
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=760,
    ).pack(anchor="w", padx=18, pady=(0, 12))

    button_row = Frame(actions_card, style="Card.TFrame")
    button_row.pack(anchor="w", padx=18, pady=(0, 16))

    btn_select = Button(
        button_row, text="Select Folder", command=select_folder, style="Primary.TButton"
    )
    btn_select.grid(row=0, column=0, padx=(0, 10))

    btn_process = Button(
        button_row,
        text="Review and Run Photo Batch",
        command=start_batch_process,
        state="disabled",
        style="Secondary.TButton",
    )
    btn_process.grid(row=0, column=1)

    status_card = Frame(content_frame, style="Card.TFrame")
    status_card.pack(fill="x")

    Label(
        status_card,
        text="Run Status",
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        font=("Georgia", 16, "bold"),
    ).pack(anchor="w", padx=18, pady=(16, 4))

    progress = Progressbar(
        status_card,
        orient="horizontal",
        mode="determinate",
        style="Accent.Horizontal.TProgressbar",
    )
    progress.pack(fill="x", padx=18, pady=(4, 8))

    progress_label = Label(
        status_card,
        text="Ready",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI Semibold", 10),
    )
    progress_label.pack(anchor="w", padx=18)

    status_label = Label(
        status_card,
        text="Status: Choose a workflow, then select a folder.",
        bg=CARD_BG,
        fg=TEXT_MUTED,
        font=("Segoe UI", 10),
        justify="left",
        wraplength=760,
    )
    status_label.pack(anchor="w", padx=18, pady=(6, 12))

    utility_row = Frame(status_card, style="Card.TFrame")
    utility_row.pack(anchor="w", padx=18, pady=(0, 16))

    Button(
        utility_row,
        text="How to Use",
        command=show_instructions,
        style="Secondary.TButton",
    ).grid(row=0, column=0, padx=(0, 8))
    Button(
        utility_row,
        text="Summary Log",
        command=view_user_friendly_log,
        style="Secondary.TButton",
    ).grid(row=0, column=1, padx=(0, 8))
    Button(
        utility_row,
        text="Technical Log",
        command=view_log_file,
        style="Secondary.TButton",
    ).grid(row=0, column=2)

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

    refresh_folder_selection_summary()
    root_window.mainloop()


if __name__ == "__main__":
    main()

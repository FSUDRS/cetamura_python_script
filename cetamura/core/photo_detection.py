"""
Enhanced photo set detection with hierarchical structure support
"""

from pathlib import Path
from typing import Dict, List
import logging
from collections import defaultdict

from .types import PhotoSet
from .validation import validate_photo_set


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
        'jpg': [],
        'xml': [],
        'manifest': []
    }
    
    def search_directory(directory: Path, current_depth: int):
        if current_depth > max_depth:
            return
            
        try:
            for item in directory.iterdir():
                if item.is_file():
                    if item.suffix.lower() in ['.jpg', '.jpeg']:
                        files['jpg'].append(item)
                    elif item.suffix.lower() == '.xml':
                        files['xml'].append(item)
                    elif item.name.lower() == 'manifest.ini':
                        files['manifest'].append(item)
                elif item.is_dir():
                    search_directory(item, current_depth + 1)
        except (PermissionError, OSError) as e:
            logging.warning(f"Cannot access directory {directory}: {e}")
    
    search_directory(parent_folder, 0)
    logging.debug(f"Enhanced finder discovered - JPG: {len(files['jpg'])}, XML: {len(files['xml'])}, Manifest: {len(files['manifest'])}")
    return files


def group_files_by_directory(files: Dict[str, List[Path]]) -> List[Dict]:
    """
    Group files by their containing directory.
    
    Args:
        files: Dictionary of file lists by type
        
    Returns:
        List of dictionaries containing grouped files
    """
    directory_groups = defaultdict(lambda: {'jpg': [], 'xml': [], 'manifest': []})
    
    # Group files by their parent directory
    for file_type, file_list in files.items():
        for file_path in file_list:
            directory_groups[file_path.parent][file_type].append(file_path)
    
    # Convert to list of dictionaries
    file_groups = []
    for directory, grouped_files in directory_groups.items():
        if grouped_files['jpg'] and grouped_files['xml'] and grouped_files['manifest']:
            file_groups.append({
                'directory': directory,
                **grouped_files
            })
    
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
        associated_jpg = [f for f in files['jpg'] if manifest_dir in f.parents or f.parent == manifest_dir]
        associated_xml = [f for f in files['xml'] if manifest_dir in f.parents or f.parent == manifest_dir]
        
        if associated_jpg and associated_xml:
            # Group by immediate subdirectory if files are not in manifest directory
            if any(f.parent != manifest_dir for f in associated_jpg + associated_xml):
                # Group files by their immediate directory under manifest_dir
                subdir_groups = defaultdict(lambda: {'jpg': [], 'xml': []})
                
                for jpg_file in associated_jpg:
                    if jpg_file.parent == manifest_dir:
                        subdir_groups[manifest_dir]['jpg'].append(jpg_file)
                    else:
                        # Find the immediate subdirectory under manifest_dir
                        relative_parts = jpg_file.relative_to(manifest_dir).parts
                        if relative_parts:
                            subdir = manifest_dir / relative_parts[0]
                            subdir_groups[subdir]['jpg'].append(jpg_file)
                
                for xml_file in associated_xml:
                    if xml_file.parent == manifest_dir:
                        subdir_groups[manifest_dir]['xml'].append(xml_file)
                    else:
                        # Find the immediate subdirectory under manifest_dir
                        relative_parts = xml_file.relative_to(manifest_dir).parts
                        if relative_parts:
                            subdir = manifest_dir / relative_parts[0]
                            subdir_groups[subdir]['xml'].append(xml_file)
                
                # Create PhotoSet for each subdirectory with files
                for subdir, subdir_files in subdir_groups.items():
                    if subdir_files['jpg'] and subdir_files['xml']:
                        photo_set = PhotoSet(
                            base_directory=subdir,
                            jpg_files=subdir_files['jpg'],
                            xml_files=subdir_files['xml'],
                            manifest_file=manifest_file,
                            structure_type='hierarchical'
                        )
                        hierarchical_sets.append(photo_set)
                        logging.info(f"Hierarchical photo set found: {subdir.relative_to(base_path)} (manifest in {manifest_dir.relative_to(base_path)})")
            else:
                # All files are in the same directory as manifest
                photo_set = PhotoSet(
                    base_directory=manifest_dir,
                    jpg_files=associated_jpg,
                    xml_files=associated_xml,
                    manifest_file=manifest_file,
                    structure_type='hierarchical'
                )
                hierarchical_sets.append(photo_set)
                logging.debug(f"Standard photo set found via hierarchical search: {manifest_dir.relative_to(base_path)}")
    
    return hierarchical_sets


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
        directory = group['directory']
        already_found = any(ps.base_directory == directory for ps in photo_sets)
        if not already_found:
            try:
                photo_set = PhotoSet(
                    base_directory=directory,
                    jpg_files=group['jpg'],
                    xml_files=group['xml'],
                    manifest_file=group['manifest'][0],  # Take first manifest
                    structure_type='standard'
                )
                if validate_photo_set(photo_set):
                    photo_sets.append(photo_set)
                    logging.debug(f"Standard photo set found: {directory.relative_to(parent_path)}")
            except (IndexError, Exception) as e:
                logging.warning(f"Could not create photo set for {directory}: {e}")
    
    logging.info(f"Enhanced detection found {len(photo_sets)} valid photo sets")
    return photo_sets


def find_photo_sets(parent_folder: str) -> list:
    """
    Backward-compatible interface that returns tuples instead of PhotoSet objects.
    This function provides the same interface as the original find_photo_sets
    but uses the enhanced detection logic internally.
    
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
            photo_set.jpg_files,           # list of JPG/JPEG files  
            photo_set.xml_files,           # list of XML files
            [photo_set.manifest_file]      # list of manifest files (original expects list)
        )
        compatible_results.append(compatible_tuple)
    
    return compatible_results

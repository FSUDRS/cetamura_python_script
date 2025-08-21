"""
Validation functions for photo sets and directory structures
"""

from pathlib import Path
from typing import List
import logging

from .types import PhotoSet


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


def validate_photo_set(photo_set: PhotoSet) -> bool:
    """
    Validate that a photo set has matching XML files for JPG files.
    
    Args:
        photo_set: PhotoSet to validate
        
    Returns:
        True if valid, False otherwise
    """
    if len(photo_set.jpg_files) == 0 or len(photo_set.xml_files) == 0:
        logging.debug(f"Invalid photo set {photo_set.base_directory}: insufficient files")
        return False
    
    # Check if we can extract IIDs from XML files
    valid_xml_count = 0
    for xml_file in photo_set.xml_files:
        try:
            from ..utils.xml_utils import extract_iid_from_xml_enhanced
            if extract_iid_from_xml_enhanced(xml_file):
                valid_xml_count += 1
        except Exception:
            continue
    
    if valid_xml_count == 0:
        logging.debug(f"Invalid photo set {photo_set.base_directory}: no valid XML files found")
        return False
    
    logging.debug(f"Valid photo set {photo_set.base_directory}: {len(photo_set.jpg_files)} JPG, {valid_xml_count} valid XML")
    return True

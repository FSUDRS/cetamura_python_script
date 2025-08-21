"""
Core business logic for Cetamura Batch Ingest Tool
"""

from .types import FilePair, BatchContext, PhotoSet
from .validation import validate_single_manifest, validate_directory_structure, validate_photo_set
from .photo_detection import (
    find_all_files_recursive, 
    find_hierarchical_sets, 
    find_photo_sets_enhanced,
    find_photo_sets
)
from .file_processing import (
    convert_jpg_to_tiff,
    extract_iid_from_xml,
    rename_files,
    package_to_zip
)
from .batch_processor import (
    batch_process_with_safety_nets,
    batch_process_legacy,
    process_file_set_with_context
)

__all__ = [
    'FilePair', 'BatchContext', 'PhotoSet',
    'validate_single_manifest', 'validate_directory_structure', 'validate_photo_set',
    'find_all_files_recursive', 'find_hierarchical_sets', 'find_photo_sets_enhanced', 'find_photo_sets',
    'convert_jpg_to_tiff', 'extract_iid_from_xml', 'rename_files', 'package_to_zip',
    'batch_process_with_safety_nets', 'batch_process_legacy', 'process_file_set_with_context'
]

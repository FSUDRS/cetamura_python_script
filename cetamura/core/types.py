"""
Core data structures and types for the Cetamura Batch Tool
"""

from pathlib import Path
from typing import Optional, List, NamedTuple


class FilePair(NamedTuple):
    """Represents a paired XML and JPG file with IID"""
    xml: Path
    jpg: Optional[Path]
    iid: str


class BatchContext(NamedTuple):
    """Context object to pass configuration flags and resources"""
    output_dir: Path
    dry_run: bool
    staging: bool
    csv_path: Path
    csv_writer: Optional[object]  # csv.writer
    logger: object  # logging.Logger


class PhotoSet(NamedTuple):
    """Data structure for a complete photo set"""
    base_directory: Path
    jpg_files: List[Path]
    xml_files: List[Path]
    manifest_file: Path
    structure_type: str  # 'standard', 'hierarchical'

"""
Utility functions for file operations and system interactions
"""

import os
import platform
import subprocess
from pathlib import Path
import logging
from typing import Optional


def open_file_with_system_app(file_path: Path) -> bool:
    """
    Open a file with the default system application.
    
    Args:
        file_path: Path to the file to open
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not file_path.exists():
            logging.warning(f"File does not exist: {file_path}")
            return False
            
        system = platform.system().lower()
        if system == "windows":
            os.startfile(str(file_path))
        elif system == "darwin":  # macOS
            subprocess.call(["open", str(file_path)])
        else:  # Linux and others
            subprocess.call(["xdg-open", str(file_path)])
            
        logging.info(f"Opened file: {file_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error opening file {file_path}: {e}")
        return False


def ensure_directory_exists(directory: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create directory {directory}: {e}")
        return False


def get_file_size_mb(file_path: Path) -> Optional[float]:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB, or None if file doesn't exist
    """
    try:
        if file_path.exists():
            size_bytes = file_path.stat().st_size
            return size_bytes / (1024 * 1024)  # Convert to MB
        return None
    except Exception as e:
        logging.error(f"Error getting file size for {file_path}: {e}")
        return None


def safe_file_operation(operation_func, *args, **kwargs):
    """
    Safely execute a file operation with error handling.
    
    Args:
        operation_func: Function to execute
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the operation or None if failed
    """
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        logging.error(f"File operation failed: {e}")
        return None


def clean_filename(filename: str) -> str:
    """
    Clean a filename by removing or replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for filesystem use
    """
    # Characters that are invalid in Windows filenames
    invalid_chars = '<>:"/\\|?*'
    cleaned = filename
    
    for char in invalid_chars:
        cleaned = cleaned.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    cleaned = cleaned.strip(' .')
    
    # Ensure filename isn't empty
    if not cleaned:
        cleaned = "unnamed_file"
    
    return cleaned

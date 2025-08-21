"""
File processing operations for image conversion, renaming, and packaging
"""

from pathlib import Path
from PIL import Image
import zipfile
import shutil
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Tuple


def convert_jpg_to_tiff(jpg_path: Path, quality: int = 95) -> Optional[Path]:
    """
    Convert JPG file to TIFF format.
    
    Args:
        jpg_path: Path to the JPG file
        quality: Conversion quality (not applicable to TIFF but kept for compatibility)
        
    Returns:
        Path to converted TIFF file, or None if conversion failed
    """
    try:
        tiff_path = jpg_path.with_suffix('.tiff')
        
        with Image.open(jpg_path) as img:
            # Convert to RGB if not already (handles various formats)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as TIFF with high quality
            img.save(tiff_path, format='TIFF', compression='none')
        
        logging.debug(f"Converted {jpg_path.name} to {tiff_path.name}")
        return tiff_path
        
    except Exception as e:
        logging.error(f"Failed to convert {jpg_path} to TIFF: {e}")
        return None


def extract_iid_from_xml(xml_file: Path) -> str:
    """
    Extract IID from XML file.
    
    Args:
        xml_file: Path to the XML metadata file
        
    Returns:
        Extracted IID string
        
    Raises:
        ValueError: If IID cannot be found in XML file
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Look for IID in common XML structures
        iid_element = root.find('.//iid')
        if iid_element is not None and iid_element.text:
            return iid_element.text.strip()
        
        # Try alternative structures
        iid_element = root.find('.//IID')
        if iid_element is not None and iid_element.text:
            return iid_element.text.strip()
            
        # Try as attribute
        if 'iid' in root.attrib:
            return root.attrib['iid'].strip()
            
        if 'IID' in root.attrib:
            return root.attrib['IID'].strip()
        
        raise ValueError(f"No IID found in XML file: {xml_file}")
        
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format in {xml_file}: {e}")
    except Exception as e:
        raise ValueError(f"Error reading XML file {xml_file}: {e}")


def rename_files(base_directory: Path, tiff_file: Path, xml_file: Path, iid: str) -> Tuple[Path, Path]:
    """
    Rename TIFF and XML files using the IID.
    
    Args:
        base_directory: Base directory for the files
        tiff_file: Path to TIFF file
        xml_file: Path to XML file
        iid: Identifier to use for renaming
        
    Returns:
        Tuple of (new_tiff_path, new_xml_path)
    """
    try:
        # Create new file paths with IID
        new_tiff = base_directory / f"{iid}.tiff"
        new_xml = base_directory / f"{iid}.xml"
        
        # Rename files
        tiff_file.rename(new_tiff)
        xml_file.rename(new_xml)
        
        logging.debug(f"Renamed files for IID {iid}")
        return new_tiff, new_xml
        
    except Exception as e:
        logging.error(f"Failed to rename files for IID {iid}: {e}")
        raise


def package_to_zip(tiff_file: Path, xml_file: Path, manifest_file: Path, output_folder: Path) -> Path:
    """
    Package files into a ZIP archive.
    
    Args:
        tiff_file: Path to TIFF file
        xml_file: Path to XML file
        manifest_file: Path to manifest file
        output_folder: Output directory for ZIP file
        
    Returns:
        Path to created ZIP file
    """
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Create ZIP filename based on IID
        iid = tiff_file.stem
        zip_path = output_folder / f"{iid}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files to ZIP
            zipf.write(tiff_file, tiff_file.name)
            zipf.write(xml_file, xml_file.name)
            zipf.write(manifest_file, manifest_file.name)
        
        logging.debug(f"Created ZIP package: {zip_path}")
        return zip_path
        
    except Exception as e:
        logging.error(f"Failed to create ZIP package for {iid}: {e}")
        raise

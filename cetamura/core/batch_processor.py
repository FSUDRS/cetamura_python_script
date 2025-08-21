"""
Core batch processing logic with safety nets and context management
"""

import csv
from pathlib import Path
import logging
from datetime import datetime
from typing import Optional, Tuple, NamedTuple
from dataclasses import dataclass

from .types import PhotoSet, FilePair, BatchContext
from .validation import validate_single_manifest
from .photo_detection import find_photo_sets
from .file_processing import extract_iid_from_xml, convert_jpg_to_tiff, rename_files, package_to_zip


@dataclass
class ProcessingResult:
    """Result of processing a single file set"""
    success: bool
    iid: str
    error_message: Optional[str] = None
    files_processed: Optional[list] = None


def process_file_set_with_context(file_pair: FilePair, iid: str, directory: Path, context: BatchContext) -> bool:
    """
    Process a single file set (XML+JPG) with proper context logging.
    
    Args:
        file_pair: FilePair containing XML and JPG files
        iid: Identifier extracted from XML
        directory: Base directory for processing
        context: BatchContext with processing configuration
        
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        logger = context.logger
        csv_writer = context.csv_writer
        
        # Check if JPG file was found
        if file_pair.jpg is None:
            logger.warning(f"No matching JPG found for XML {file_pair.xml.name} (IID: {iid})")
            csv_writer.writerow([iid, str(file_pair.xml), '', 'WARNING', 'MISSING_JPG', 'No matching JPG file found'])
            return False
        
        # Log file pairing success
        logger.debug(f"Processing file pair - XML: {file_pair.xml.name}, JPG: {file_pair.jpg.name}, IID: {iid}")
        
        if context.dry_run:
            # Dry run mode - just validate and log
            csv_writer.writerow([iid, str(file_pair.xml), str(file_pair.jpg), 'SUCCESS', 'DRY_RUN', 'Would process files'])
            logger.debug(f"DRY RUN: Would process {iid}")
            return True
        else:
            # Convert JPG to TIFF
            tiff_path = convert_jpg_to_tiff(file_pair.jpg)
            if tiff_path is None:
                csv_writer.writerow([iid, str(file_pair.xml), str(file_pair.jpg), 'ERROR', 'CONVERSION', 'Failed to convert JPG to TIFF'])
                return False
            
            # Rename files
            new_tiff, new_xml = rename_files(directory, tiff_path, file_pair.xml, iid)
            
            # Find manifest file for this directory
            manifest_files = list(directory.glob('MANIFEST.ini')) + list(directory.glob('manifest.ini'))
            if not manifest_files:
                # Look in parent directories
                for parent in directory.parents:
                    manifest_files = list(parent.glob('MANIFEST.ini')) + list(parent.glob('manifest.ini'))
                    if manifest_files:
                        break
            
            if not manifest_files:
                csv_writer.writerow([iid, str(file_pair.xml), str(file_pair.jpg), 'ERROR', 'MANIFEST', 'No manifest file found'])
                return False
            
            manifest_file = manifest_files[0]  # Use first found
            
            # Package to ZIP
            zip_path = package_to_zip(new_tiff, new_xml, manifest_file, context.output_dir)
            csv_writer.writerow([iid, str(new_xml), str(new_tiff), 'SUCCESS', 'PROCESSED', f'Packaged to {zip_path.name}'])
            logger.info(f"Successfully processed {iid} -> {zip_path.name}")
            return True
            
    except Exception as e:
        logger.error(f"Error processing file set {iid}: {e}")
        context.csv_writer.writerow([iid, str(file_pair.xml) if file_pair.xml else '', 
                                   str(file_pair.jpg) if file_pair.jpg else '', 
                                   'ERROR', 'PROCESSING', str(e)])
        return False


def batch_process_with_safety_nets(folder_path: str, output_dir: str, dry_run: bool = False, 
                                 staging: bool = False, csv_path: Optional[Path] = None) -> Tuple[int, int, Path]:
    """
    Enhanced batch processing with comprehensive safety nets and dual logging.
    
    Args:
        folder_path: Source directory to process
        output_dir: Output directory for processed files
        dry_run: If True, perform validation only without file operations
        staging: If True, process to staging directory
        csv_path: Optional custom CSV report path
        
    Returns:
        Tuple of (success_count, error_count, csv_report_path)
    """
    from ..utils.logging_utils import log_user_friendly, configure_logging_level
    
    logger = logging.getLogger(__name__)
    
    # Set up output paths
    folder_path = Path(folder_path).resolve()
    output_dir = Path(output_dir).resolve()
    
    if csv_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = Path(__file__).parent.parent.parent / f"batch_report_{folder_path.name}_{timestamp}.csv"
    
    # User-friendly logging
    mode = "Dry Run Preview" if dry_run else "Staging" if staging else "Production"
    log_user_friendly(f"🚀 Starting {mode} processing")
    log_user_friendly(f"📁 Source folder: {folder_path}")
    
    if dry_run:
        log_user_friendly("🔍 Dry Run Mode - Previewing processing, no files will be changed")
    elif staging:
        log_user_friendly(f"📋 Staging Mode - Output to: {output_dir}")
    else:
        log_user_friendly(f"⚡ Production Mode - Output to: {output_dir}")
    
    # Advanced logging (technical details)
    logger.info(f"Starting batch process - Dry run: {dry_run}, Staging: {staging}")
    logger.info(f"Source folder: {folder_path}")
    logger.info(f"Output folder: {output_dir}")
    
    if dry_run:
        logger.info("DRY RUN MODE - No files will be modified")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize CSV writer
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
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
            
            success_count = 0
            error_count = 0
            
            # Use enhanced photo set detection to handle complex directory structures
            try:
                photo_sets = find_photo_sets(str(folder_path))
                log_user_friendly(f"🔍 Found {len(photo_sets)} photo sets to process")
                logger.info(f"Enhanced detection found {len(photo_sets)} photo sets")
                
                for directory, jpg_files, xml_files, manifest_files in photo_sets:
                    # Validate single manifest requirement
                    try:
                        validate_single_manifest(manifest_files)
                        context.csv_writer.writerow(['', str(directory), '', 'MANIFEST_OK', 'VALIDATION', 'Single manifest found'])
                        log_user_friendly(f"✅ Validated photo set: {directory.name}")
                    except ValueError as e:
                        logger.error(f"Manifest validation failed for {directory}: {e}")
                        context.csv_writer.writerow(['', str(directory), '', 'MANIFEST_ERROR', 'VALIDATION', str(e)])
                        log_user_friendly(f"❌ Manifest error in {directory.name}: {e}")
                        error_count += 1
                        continue
                    
                    # Create file pairs from the enhanced detection results
                    file_pairs = []
                    for xml_file in xml_files:
                        try:
                            iid = extract_iid_from_xml(xml_file)
                            matching_jpg = None
                            
                            # Look for matching JPG file
                            for jpg_file in jpg_files:
                                if iid.lower() in jpg_file.stem.lower() or jpg_file.stem.lower() in iid.lower():
                                    matching_jpg = jpg_file
                                    break
                            
                            file_pairs.append(FilePair(xml=xml_file, jpg=matching_jpg, iid=iid))
                            
                        except Exception as e:
                            logger.warning(f"Could not process XML {xml_file}: {e}")
                            context.csv_writer.writerow(['', str(xml_file), '', 'WARNING', 'XML_ERROR', str(e)])
                    
                    # Process each file pair
                    for file_pair in file_pairs:
                        try:
                            result = process_file_set_with_context(file_pair, file_pair.iid, directory, context)
                            if result:
                                success_count += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            logger.error(f"Error processing {file_pair.iid} in {directory}: {str(e)}")
                            context.csv_writer.writerow([file_pair.iid, '', '', 'ERROR', 'PROCESSING', str(e)])
                            error_count += 1
                            
            except Exception as e:
                logger.error(f"Error during enhanced photo set detection: {e}")
                log_user_friendly(f"❌ Error finding photo sets: {e}")
                # Fallback to basic error handling
                context.csv_writer.writerow(['', str(folder_path), '', 'ERROR', 'DETECTION', str(e)])
                error_count += 1
            
            # Log final results
            logger.info(f"Batch process completed - Success: {success_count}, Errors: {error_count}")
            log_user_friendly(f"✅ Processing complete - Success: {success_count}, Errors: {error_count}")
            context.csv_writer.writerow(['SUMMARY', '', '', f'Success: {success_count}', f'Errors: {error_count}', f'Dry run: {dry_run}'])
            
            return success_count, error_count, csv_path
            
    except Exception as e:
        logger.error(f"Critical error in batch process: {str(e)}")
        log_user_friendly(f"❌ Critical error: {str(e)}")
        raise


def batch_process_legacy(root: str, jpg_files: list, xml_files: list, ini_files: list) -> None:
    """
    Legacy batch processing function for backward compatibility.
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

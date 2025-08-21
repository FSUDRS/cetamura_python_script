"""
Logging utilities for dual logging system (technical + user-friendly)
"""

import logging
import os
from pathlib import Path


# Global flag for advanced logging
advanced_logs = False


def configure_logging_level(advanced: bool = False):
    """
    Configure logging level based on user preference.
    
    Args:
        advanced: If True, enable detailed technical logging
    """
    global advanced_logs
    advanced_logs = advanced
    
    # Set logging level based on preference
    if advanced:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Advanced logging enabled - showing detailed technical information")
    else:
        logging.getLogger().setLevel(logging.INFO)
        logging.info("Standard logging enabled - user-friendly mode")


def log_user_friendly(message: str):
    """
    Log a user-friendly message to both console and summary log file.
    
    Args:
        message: User-friendly message to log
    """
    # Create summary log handler if it doesn't exist
    summary_log_file = "batch_process_summary.log"
    
    # Create or get the summary logger
    summary_logger = logging.getLogger('user_friendly')
    if not summary_logger.handlers:
        # Set up file handler for user-friendly logs
        summary_handler = logging.FileHandler(summary_log_file, mode='w', encoding='utf-8')
        summary_formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        summary_handler.setFormatter(summary_formatter)
        summary_logger.addHandler(summary_handler)
        summary_logger.setLevel(logging.INFO)
        summary_logger.propagate = False  # Don't propagate to root logger
    
    # Log to summary file
    summary_logger.info(message)
    
    # Also log to main logger if advanced logging is enabled
    if advanced_logs:
        main_logger = logging.getLogger(__name__)
        main_logger.info(f"USER: {message}")


def setup_logging(log_file: str = "batch_tool.log", level: int = logging.INFO):
    """
    Set up the main logging configuration.
    
    Args:
        log_file: Path to the main log file
        level: Logging level
    """
    # Configure root logger for technical logs
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler()  # Console output
        ]
    )
    
    # Initialize user-friendly logging
    log_user_friendly("Cetamura Batch Tool - Logging System Initialized")


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Name for the logger (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

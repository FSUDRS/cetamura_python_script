"""
Cetamura Batch Ingest Tool

A professional tool for batch processing archaeological photo collections
from the Cetamura dig site, with support for TIFF conversion, XML metadata
processing, and ZIP packaging for digital repository submission.

Enhanced with modular architecture for better maintainability.
"""

from . import core, gui, utils, config

__version__ = "2024.08.21"
__author__ = "FSUDRS"
__description__ = "Professional archaeological photo batch processing tool"

# Version info for runtime access
VERSION_INFO = {
    'version': __version__,
    'release_date': '2024-08-21',
    'features': [
        'Modular architecture',
        'Hierarchical directory detection',
        'Dual-mode processing (dry-run/staging)',
        'Enhanced safety nets',
        'User-friendly logging',
        'Mode conflict guardrails'
    ]
}

# Main application entry point
from .gui import MainApplication

__all__ = [
    'core',
    'gui', 
    'utils',
    'config',
    'MainApplication',
    'VERSION_INFO'
]

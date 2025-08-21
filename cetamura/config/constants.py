"""
Configuration and constants for the Cetamura Batch Ingest Tool
"""

# XML Processing Constants
NAMESPACES = {
    'mods': 'http://www.loc.gov/mods/v3'
}

# File Processing Settings
MAX_SEARCH_DEPTH = 5
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg']
SUPPORTED_XML_FORMATS = ['.xml']
MANIFEST_FILENAME = 'MANIFEST.ini'

# Logging Settings
DEFAULT_LOG_FILE = 'batch_tool.log'
USER_LOG_FILE = 'batch_process_summary.log'

# Output Directory Names
STAGING_DIR_NAME = 'staging_output'
PRODUCTION_DIR_NAME = 'output'

# CSV Report Settings
CSV_HEADERS = ['IID', 'XML_Path', 'JPG_Path', 'Status', 'Action', 'Notes']

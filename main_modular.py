"""
New modular entry point for Cetamura Batch Tool
"""

import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cetamura import MainApplication
from cetamura.utils import setup_logging


def main():
    """Main entry point for the modular version"""
    try:
        # Initialize logging
        setup_logging("batch_tool.log", logging.INFO)
        
        # Create and run application
        app = MainApplication()
        app.run()
        
    except Exception as e:
        print(f"Critical error starting application: {e}")
        logging.critical(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

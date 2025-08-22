# Cetamura Archaeological Photo Processing Tool - Project Structure

## Overview
This project is organized to provide a clean, maintainable structure for the Cetamura archaeological photo processing system.

## Directory Structure

```
cetamura_python_script/
├── src/                    # Main application source code
│   └── main.py            # Primary application entry point
├── cetamura/              # Core application modules
│   ├── config/            # Configuration and constants
│   ├── core/              # Core processing logic
│   ├── gui/               # User interface components
│   └── utils/             # Utility functions and helpers
├── scripts/               # Organized script collection
│   ├── build/             # Build and packaging scripts
│   ├── setup/             # Environment setup scripts
│   └── utilities/         # Development and maintenance utilities
├── tests/                 # Unit tests and test data
├── test_data/             # Sample data for testing
├── docs/                  # Documentation files
├── logs/                  # Application log files
├── dist_package/          # Distribution packages
├── legacy_backup/         # Backup of legacy versions
└── assets/                # Static assets (icons, images, etc.)
```

## Key Files

### Main Application
- `src/main.py` - Primary application entry point (proven working system)

### Scripts Organization
- `scripts/build/` - Build scripts for creating executables
- `scripts/setup/` - Environment setup and dependency installation
- `scripts/utilities/` - Development utilities and diagnostic tools

### Configuration
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies
- `pytest.ini` - Test configuration
- `.gitignore` - Git ignore patterns

## Usage

### Running the Application
```bash
python src/main.py
```

### Building Executables
```bash
# Windows
scripts/build/build_exe.ps1

# macOS
scripts/build/build_exe_macos.sh

# Cross-platform
scripts/build/build_cross_platform.sh
```

### Development Setup
```bash
# Windows
scripts/setup/setup_dev.ps1

# macOS
scripts/setup/setup_macos.sh
```

## Notes
- The main working application is in `src/main.py`
- The `cetamura/` directory contains modular components for future development
- All build and utility scripts are now organized under `scripts/`
- Logs are automatically stored in the `logs/` directory

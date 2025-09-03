# CETAMURA BATCH INGEST TOOL

## Overview

This tool automates the process for creating ingest files for the Cetamura Digital Collections.

> **Project Structure**: See [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) for detailed information about the organized project layout.

## Quick Start

### Windows Users
1. Download the project
2. Navigate to `dist_package/`
3. Double-click `executables/Cetamura_Batch_Tool_Windows.exe`

### macOS Users
1. Download the project
2. Navigate to `dist_package/`
3. Run: `chmod +x install_macos.sh && ./install_macos.sh`

### Linux Users
1. Download the project
2. Install dependencies: `pip3 install -r dist_package/requirements.txt`
3. Run: `python3 dist_package/source/main.py`

## Complete Documentation

For detailed instructions, build guides, and troubleshooting:
- **Distribution Guide**: `dist_package/README_DISTRIBUTION.md`
- **Build Instructions**: `dist_package/docs/README_BUILD.md`
- **Quick Reference**: `dist_package/docs/BUILD_SUMMARY.md`

## Project Structure

```
cetamura_python_script/
├── src/                        # Source code
│   └── main.py                 # Main application
├── tests/                      # Unit tests
├── assets/                     # Optional icons/logos
├── dist_package/               # Complete distribution package
│   ├── executables/            # Pre-built executables
│   ├── source/                 # Source code copy
│   ├── build_scripts/          # Build scripts for all platforms
│   ├── docs/                   # Documentation
│   └── install_*.sh|.ps1       # Installation scripts
├── .venv/                      # Virtual environment
└── requirements/               # Python dependencies
    ├── requirements.txt        # Production dependencies
    └── requirements-dev.txt    # Development dependencies
```

## Requirements

### File Structure
The tool expects this folder structure:
```
Parent_Folder/
├── 2006/
│   ├── 46N-3W/
│   │   ├── image.jpg
│   │   ├── metadata.xml
│   │   └── MANIFEST.ini
│   └── ...
└── ...
```

### System Requirements
- **TIFF/JPG image files**
- **Corresponding XML metadata files** 
- **MANIFEST.ini file** in each folder
- **Python 3.6+** (for source execution)

## Processing Steps

1. **Extract IID** from XML metadata files
2. **Convert JPG to TIFF** format
3. **Rename files** to match extracted IID
4. **Package into ZIP** archives with MANIFEST.ini
5. **Organize output** in structured folders

## Development

### Running from Source
```bash
# Install dependencies
pip install -r requirements/requirements.txt

# Run the application
python src/main.py
```

### Building Executables
See `dist_package/docs/BUILD_SUMMARY.md` for platform-specific build instructions.

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=cetamura tests/
```

### CI/CD Pipeline

This project uses GitHub Actions for CI/CD:

- **Continuous Integration**: Automated testing on code push and pull requests
- **Continuous Deployment**: Automatic release building when version tags are pushed

For detailed information:

- [CI/CD Guide](docs/CICD_GUIDE.md) - Complete guide to the CI/CD setup
- [Phased Implementation](docs/PHASED_IMPLEMENTATION.md) - Step-by-step implementation plan

## Important Notes

- **Backup files** before processing
- **File pairing**: Ensure matching TIFF and XML files
- **Valid IID identifiers**: XML files must contain valid IID identifiers
- **Logging**: Check `batch_tool.log` for detailed processing logs
- **Irreversible actions**: Processing cannot be undone

## Support

1. Check the logs: `batch_tool.log`
2. Review documentation in `dist_package/docs/`
3. Verify file structure requirements
4. Ensure all dependencies are installed

---

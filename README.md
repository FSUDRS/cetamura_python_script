# CETAMURA BATCH INGEST TOOL

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

## Overview

This tool automates the process for creating ingest files for the Cetamura Digital Collections.

> 
## Quick Start


### Run from Source(Best way)
```bash
git clone [repo-url]
cd cetamura_python_script
pip install -r requirements.txt
python src/main.py
```

## How to Use

1. **Select Folder**: Choose the parent folder containing your photo sets
2. **Processing Options**: 
   - **Dry Run**: Preview what will happen without changing files
   - **Staging**: Process to staging folder for review
   - **Production**: Final processing
3. **Start Processing**: Click the button and wait for completion
4. **Check Results**: Review the CSV report and output folder

## What Gets Processed
The tool looks for photo sets with:
- Image file (JPG, TIFF, or PDF)
- XML metadata file
- INI manifest file

## Output
- Processed image files (TIFF/PDF preserved or converted)
- ZIP packages (one per photo set)
- CSV report of all processing results
- Detailed logs
- **NEW:** Post-processing validation reports

## Post-Processing Validation (New Feature)

The tool now includes comprehensive validation to ensure outputs match expectations:

### Pre-Flight Checks
Before processing starts, the tool verifies:
-  Sufficient disk space available
-  Write permissions to output directory
-  Orphaned files from previous runs (warning)

**Example Output:**
```
[INFO] Running pre-flight checks...
[PASS] Pre-flight checks passed. Disk space: 125.3 GB available
```

### Post-Processing Validation
After processing completes, the tool validates:
-  Expected number of ZIPs match actual ZIPs created
-  Each ZIP contains correct structure (TIFF, XML, manifest.ini)
-  No ZIPs created during dry run mode

**Example Output:**
```
[PASS] Post-processing validation: 25 valid ZIPs
```

### Reconciliation Report
The tool generates a detailed reconciliation report comparing:
- Input XML file count
- CSV SUCCESS row count
- Actual ZIP file count
- Valid ZIP file count

**Example Output:**
```
=== Reconciliation Report ===
Input XML files: 25
CSV SUCCESS rows: 25
Actual ZIP files: 25
Valid ZIP files: 25
[PASS] No discrepancies found.
```

### What Validation Detects
-  Missing ZIPs (success logged but no ZIP created)
-  Corrupted ZIPs (wrong number of files or missing components)
-  Disk full scenarios (caught before processing starts)
-  Orphaned files (*_PROC.tif, *_PROC.xml without ZIPs)
-  Dry run violations (ZIPs created when they shouldn't be)

**Note:** Validation reports issues but doesn't block completed processing. Pre-flight checks will block processing if critical issues are found (disk space, permissions).

## File Locations
- **Output**: `output/` folder in your selected directory
- **Staging**: `staging_output/` folder (for staging mode)
- **Reports**: CSV files with timestamp in filename
- **Logs**: `batch_tool.log` in application folder

## Troubleshooting
- **No photo sets found**: Check folder structure and file naming
- **Processing fails**: Check the CSV report for specific errors
- **Application won't start**: Ensure Python 3.11+ or download fresh executable
## Current Structure
```
cetamura_python_script/
 src/
    main.py              # Complete application (1500+ lines)
    __init__.py
 tests/
    test_main.py         # Core functionality tests
    test_utils.py        # Utility function tests
    test_pairing_improvements.py
    run_tests.py         # Test runner
 dist_package/
    build_scripts/       # Cross-platform build scripts
    docs/               # Build documentation
    install_windows.ps1 # Windows installer
    install_macos.sh    # macOS installer
 docs/
    cicd.md             # Build automation guide
    project_structure.md # This file
    readme.md           # User guide
    bugs.md             # Known issues
 scripts/
    build/              # Legacy build scripts
    setup/              # Environment setup
    utilities/          # Development utilities
 requirements/
    requirements.txt    # Production dependencies
 .github/workflows/      # GitHub Actions CI/CD
 requirements-dev.txt    # Development dependencies
 pytest.ini            # Test configuration
 README.md             # Main project readme
```

## What Each Part Does

**src/main.py**
- Complete GUI application
- Batch processing logic
- Image orientation correction
- File validation and conversion
- CSV reporting
- Everything runs from this one file

**tests/**
- Unit tests for all main functions
- Test runner and configuration
- Validates core functionality

**dist_package/**
- Cross-platform build scripts
- Windows and macOS installers
- Distribution documentation

**docs/**
- User and developer documentation
- Straightforward, no-jargon guides
- Build and troubleshooting info

## How It Works
1. User runs `python src/main.py` or the built executable
2. GUI opens for folder selection
3. App finds photo sets (JPG + XML + manifest files)
4. Processes images with orientation correction
5. Creates ZIP packages for each photo set
6. Generates CSV report of results

## Dependencies
- PIL/Pillow - Image processing and orientation correction
- PyMuPDF - PDF processing and rendering
- tkinter - GUI (built into Python)
- pathlib - File handling
- csv - Report generation
- logging - Error tracking and debugging

## Recent Changes
- **v1.2.0**: Expanded file support (PDF/TIFF) and comprehensive safety nets (Dry-Run, Staging).
- Consolidated all functionality into `src/main.py`
- Added a function to automatically adjust wrongly positioned images using EXIF metadata

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
- All build and utility scripts are now organized under `scripts/`
- Logs are automatically stored in the `logs/` directory

---

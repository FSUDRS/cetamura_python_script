# Project Structure

## Current Structure
```
cetamura_python_script/
├── src/
│   ├── main.py              # Complete application (1500+ lines)
│   └── __init__.py
├── tests/
│   ├── test_main.py         # Core functionality tests
│   ├── test_utils.py        # Utility function tests
│   ├── test_pairing_improvements.py
│   └── run_tests.py         # Test runner
├── dist_package/
│   ├── build_scripts/       # Cross-platform build scripts
│   ├── docs/               # Build documentation
│   ├── install_windows.ps1 # Windows installer
│   └── install_macos.sh    # macOS installer
├── docs/
│   ├── cicd.md             # Build automation guide
│   ├── project_structure.md # This file
│   ├── readme.md           # User guide
│   └── bugs.md             # Known issues
├── scripts/
│   ├── build/              # Legacy build scripts
│   ├── setup/              # Environment setup
│   └── utilities/          # Development utilities
├── requirements/
│   └── requirements.txt    # Production dependencies
├── .github/workflows/      # GitHub Actions CI/CD
├── requirements-dev.txt    # Development dependencies
├── pytest.ini            # Test configuration
└── README.md             # Main project readme
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
- tkinter - GUI (built into Python)
- pathlib - File handling
- csv - Report generation
- logging - Error tracking and debugging

## Recent Changes
- Removed redundant `cetamura/` modular structure (Sept 2025)
- Consolidated all functionality into `src/main.py`
- Streamlined documentation to 4 essential files
- Cleaned up generated files and build artifacts

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

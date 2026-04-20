# Project Structure

## Current Structure
```
cetamura_python_script/
 src/
    main.py              # Complete GUI application and batch workflow
    validation.py        # Pre-flight, ZIP, and reconciliation validation
    __init__.py
 tests/
    test_main.py         # Core functionality tests
    test_validation.py   # Validation module tests
    test_global_recovery.py
    run_tests.py         # Test runner
 dist_package/
    build_scripts/       # Cross-platform build scripts
    docs/               # Build documentation
    install_windows.ps1 # Windows installer
    install_macos.sh    # macOS installer
 docs/
    PROJECT_STRUCTURE.md # This file
    readme.md           # User guide
    RELEASE_CHECKLIST.md # Release verification and packaging steps
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

**src/validation.py**
- Pre-flight validation
- ZIP content checks
- Reconciliation reports

**tests/**
- Unit and integration tests for main workflow behavior
- Validation and recovery regression tests
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
3. App scans the selected folder for the chosen workflow
4. Runs validation and packaging without mutating source files
5. Creates ingest ZIP packages under `output/` or `staging_output/`
6. Generates CSV and reconciliation reports

## Dependencies
- PIL/Pillow - Image processing and orientation correction
- PyMuPDF - PDF rendering support
- defusedxml - Safer XML parsing
- tkinter - GUI (built into Python)
- pathlib - File handling
- csv - Report generation
- logging - Error tracking and debugging

## Recent Changes
- Removed redundant `cetamura/` modular structure (Sept 2025)
- Consolidated all functionality into `src/main.py`
- Streamlined documentation to 4 essential files
- Cleaned up generated files and build artifacts
- Added patent workflow support, validation checks, and release checklist

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
- Validation helpers are in `src/validation.py`
- All build and utility scripts are now organized under `scripts/`
- Logs are automatically stored in the `logs/` directory

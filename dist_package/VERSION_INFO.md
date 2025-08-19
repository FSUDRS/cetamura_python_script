# Cetamura Batch Ingest Tool - Version Information

**Version:** Safety Net v2024.08.19  
**Release Date:** August 19, 2025  
**Platform Support:** Windows, macOS, Linux  
**Status:** Production Ready with Safety Net Features ✅

## New in This Release - Safety Net Features

### 🎯 Major Improvements Completed
- **Dry-Run Mode**: Preview processing without file changes
- **Staging Mode**: Non-destructive output to staging directories
- **CSV Reporting**: Detailed processing logs with timestamps  
- **Enhanced Error Handling**: Graceful failures with clear messages
- **Processing Options Dialog**: User-friendly interface for mode selection
- **Manifest Validation**: Single manifest file enforcement
- **UX Polish**: Enhanced folder selection and status feedback  

## Package Contents

### Executables
- **Windows**: `Cetamura_Batch_Tool_Windows.exe` (17.9 MB)
- **macOS**: Build script provided (`build_exe_macos.sh`)
- **Linux**: Build script provided (`build_cross_platform.sh`)

### Source Code
- **Python Version**: Self-contained `main.py`
- **Dependencies**: Pillow, PyInstaller
- **Compatibility**: Python 3.6+

### Build Scripts
- **Windows**: PowerShell (`.ps1`)
- **macOS**: Bash (`.sh`)
- **Cross-platform**: Auto-detect (`.sh`)

## Features

### Core Functionality
- JPG to TIFF conversion
- XML IID extraction
- File renaming based on IID
- ZIP packaging with MANIFEST.ini
- Batch processing of multiple directories
- Progress tracking with GUI
- Comprehensive logging

### User Interface
- Modern Tkinter GUI
- Progress bar and status updates
- Folder selection dialog
- Instructions window
- Error handling and notifications

### Cross-platform Support
- Windows executable (pre-built)
- macOS build scripts
- Linux compatibility
- Python source (universal)

## Technical Details

### Python Dependencies
```
Pillow>=8.0.0          # Image processing
pyinstaller>=5.0.0     # Executable building
```

### System Requirements
- **Minimum RAM**: 512 MB
- **Disk Space**: 50 MB for installation
- **Python**: 3.6 or higher
- **OS Support**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)

### File Processing
- **Input Formats**: JPG, JPEG, XML, INI
- **Output Formats**: TIFF, XML, ZIP
- **Max File Size**: Limited by available memory
- **Batch Size**: Unlimited (memory permitting)

## Changelog

### Version 1.0.0 (July 11, 2025)
- Initial release
- Self-contained Python script (no utils dependency)
- Cross-platform build system
- Windows executable included
- Complete documentation package
- Installation scripts for all platforms

## Known Issues

### Windows
- May require "Run as Administrator" for some directories
- Windows Defender may flag executable (false positive)

### macOS
- May show "App from unidentified developer" warning
- Requires manual approval in System Preferences

### Linux
- `python3-tk` package required on some distributions
- May need manual font configuration

## Support

For issues or questions:
1. Check the logs: `batch_tool.log`
2. Review documentation in `docs/` folder
3. Verify file structure requirements
4. Ensure all dependencies are installed

---

**Build Date:** July 11, 2025  
**Builder:** GitHub Copilot + PyInstaller  
**Target:** Cetamura Digital Collections Project

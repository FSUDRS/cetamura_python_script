# Cetamura Batch Ingest Tool - Build Instructions

This tool automates the process for creating ingest files for the Cetamura Digital Collections.

## Requirements

### All Platforms
- Python 3.6 or higher
- Pillow (PIL) library
- PyInstaller (for building executables)

### Platform-Specific Requirements

#### macOS
- Python 3 (install from [python.org](https://www.python.org/downloads/))
- Xcode Command Line Tools (for some dependencies)

#### Windows
- Python 3 (install from [python.org](https://www.python.org/downloads/))
- PowerShell (included with Windows)

#### Linux
- Python 3 and pip (`sudo apt-get install python3 python3-pip`)
- tkinter (`sudo apt-get install python3-tk`)

## Quick Start

### Install Dependencies
```bash
pip install Pillow pyinstaller
```

### Run from Source
```bash
python src/main.py           # Windows/Linux
python3 src/main.py          # macOS/Linux
```

## Building Executables

### macOS
```bash
# Make the script executable
chmod +x build_exe_macos.sh

# Build
./build_exe_macos.sh
```

**Output:** `dist/Cetamura_Batch_Tool` (macOS executable)

### Windows
```powershell
# Run in PowerShell
.\build_exe.ps1
```

**Output:** `dist/main.exe` (Windows executable)

### Cross-Platform (Auto-detect)
```bash
# Make the script executable
chmod +x build_cross_platform.sh

# Build (auto-detects OS)
./build_cross_platform.sh
```

## Project Structure

```
cetamura_python_script/
├── src/
│   └── main.py              # Main application (self-contained)
├── assets/                  # Optional icons/logos
├── dist/                    # Built executables
├── build/                   # Build artifacts
├── requirements.txt         # Python dependencies
├── build_exe.ps1           # Windows build script
├── build_exe_macos.sh      # macOS build script
├── build_cross_platform.sh # Cross-platform build script
└── README_BUILD.md         # This file
```

## Usage

1. **Select Folder**: Choose the parent directory containing your year folders
2. **Process**: Click "Start Batch Process" to begin processing
3. **Output**: Processed ZIP files will be created in `CetamuraUploadBatch_[year]` folders

### Expected Folder Structure
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

## Troubleshooting

### macOS Issues
- **"App can't be opened"**: Right-click → Open → Open
- **Permission denied**: `chmod +x dist/Cetamura_Batch_Tool`
- **Python not found**: Install from [python.org](https://www.python.org/downloads/)

### Windows Issues
- **"Scripts disabled"**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **PyInstaller not found**: Install with `pip install pyinstaller`

### Linux Issues
- **tkinter missing**: `sudo apt-get install python3-tk`
- **Permission denied**: `chmod +x build_cross_platform.sh`

## Dependencies

- **Pillow**: Image processing
- **PyInstaller**: Executable building
- **tkinter**: GUI framework (usually included with Python)

## Development

To modify the application:

1. Edit `src/main.py`
2. Test with `python src/main.py`
3. Rebuild executable using appropriate build script

## License

This tool is designed for the Cetamura Digital Collections project.

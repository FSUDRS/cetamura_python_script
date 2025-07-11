# Cetamura Batch Ingest Tool - Build Summary

## Available Build Scripts

| Platform | Script | Output | Command |
|----------|---------|---------|----------|
| **macOS** | `build_exe_macos.sh` | `dist/Cetamura_Batch_Tool` | `./build_exe_macos.sh` |
| **Windows** | `build_exe.ps1` | `dist/main.exe` | `.\build_exe.ps1` |
| **Cross-Platform** | `build_cross_platform.sh` | Platform-specific | `./build_cross_platform.sh` |
| **macOS Setup** | `setup_macos.sh` | Full setup + build | `./setup_macos.sh` |

## Quick Build Commands

### macOS Users (Complete Setup)
```bash
# One-command setup (installs everything + builds)
chmod +x setup_macos.sh && ./setup_macos.sh
```

### macOS Users (Build Only)
```bash
# If dependencies already installed
chmod +x build_exe_macos.sh && ./build_exe_macos.sh
```

### Windows Users
```powershell
# PowerShell (run as Administrator if needed)
.\build_exe.ps1
```

### Any Platform
```bash
# Auto-detect and build
chmod +x build_cross_platform.sh && ./build_cross_platform.sh
```

## Output Files

- **macOS**: `dist/Cetamura_Batch_Tool` (Unix executable)
- **Windows**: `dist/main.exe` (Windows executable)
- **Source**: `src/main.py` (Cross-platform Python script)

## Manual Build

If the scripts don't work, build manually:

```bash
# Install dependencies
pip install pyinstaller Pillow

# macOS/Linux
pyinstaller --onefile --windowed --name "Cetamura_Batch_Tool" src/main.py --clean

# Windows
pyinstaller --onefile --noconsole src/main.py --clean
```

## Usage After Build

- **macOS**: Double-click `dist/Cetamura_Batch_Tool` or `./dist/Cetamura_Batch_Tool`
- **Windows**: Double-click `dist/main.exe` or `.\dist\main.exe`
- **Any Platform**: `python src/main.py` or `python3 src/main.py`

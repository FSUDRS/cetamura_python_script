# Cetamura Batch Ingest Tool - Distribution Package

**Complete cross-platform distribution package for the Cetamura Digital Collections batch processing tool.**

---

## Package Contents

```
dist_package/
├── README_DISTRIBUTION.md       # This file
├── requirements.txt             # Python dependencies
├── executables/                 # Pre-built executables
│   └── Cetamura_Batch_Tool_Windows.exe
├── source/                      # Python source code
│   └── main.py                  # Main application (cross-platform)
├── build_scripts/               # Build scripts for all platforms
│   ├── build_exe.ps1           # Windows build script
│   ├── build_exe_macos.sh      # macOS build script
│   ├── build_cross_platform.sh # Auto-detect platform script
│   └── setup_macos.sh          # Complete macOS setup
└── docs/                        # Documentation
    ├── README.md                # Main documentation
    ├── README_BUILD.md          # Detailed build instructions
    └── BUILD_SUMMARY.md         # Quick build reference
```

---

## Quick Start Guide

### **Windows Users**

#### Option 1: Use Pre-built Executable (Recommended)
1. Navigate to `executables/`
2. Double-click `Cetamura_Batch_Tool_Windows.exe`
3. Ready to use!

#### Option 2: Run from Source
```powershell
# Install Python dependencies
pip install -r requirements.txt

# Run the application
python source/main.py
```

#### Option 3: Build Your Own Executable
```powershell
# Copy build script to main directory
copy build_scripts\build_exe.ps1 .

# Run build script
.\build_exe.ps1
```

---

### **macOS Users**

#### Option 1: Complete Setup (Recommended)
```bash
# Copy setup script to main directory
cp build_scripts/setup_macos.sh .

# Make executable and run
chmod +x setup_macos.sh
./setup_macos.sh
```

#### Option 2: Run from Source
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Run the application
python3 source/main.py
```

#### Option 3: Build Executable Only
```bash
# Copy build script
cp build_scripts/build_exe_macos.sh .

# Make executable and run
chmod +x build_exe_macos.sh
./build_exe_macos.sh
```

---

### **Linux Users**

#### Option 1: Run from Source
```bash
# Install dependencies (Ubuntu/Debian)
sudo apt-get install python3 python3-pip python3-tk

# Install Python dependencies
pip3 install -r requirements.txt

# Run the application
python3 source/main.py
```

#### Option 2: Build Executable
```bash
# Copy cross-platform script
cp build_scripts/build_cross_platform.sh .

# Make executable and run
chmod +x build_cross_platform.sh
./build_cross_platform.sh
```

---

## What This Tool Does

### **Purpose**
Automates the creation of ingest files for the Cetamura Digital Collections.

### **Processing Steps**
1. **Extract IID** from XML metadata files
2. **Convert JPG to TIFF** format
3. **Rename files** to match extracted IID
4. **Package into ZIP** archives with MANIFEST.ini
5. **Organize output** in structured folders

### **Required File Structure**
```
Parent_Folder/
├── 2006/
│   ├── 46N-3W/
│   │   ├── image.jpg           # Image file
│   │   ├── metadata.xml        # Metadata with IID
│   │   └── MANIFEST.ini        # Manifest file
│   └── ...
└── ...
```

---

## System Requirements

### **All Platforms**
- Python 3.6 or higher
- 50MB+ free disk space
- Read/write permissions for target directories

### **Python Dependencies**
- `Pillow` (image processing)
- `PyInstaller` (for building executables)

### **Platform-Specific**
- **Windows**: PowerShell (included with Windows)
- **macOS**: Xcode Command Line Tools (for some dependencies)
- **Linux**: `python3-tk` package

---

## Troubleshooting

### **Common Issues**

#### "Python not found"
- **Windows**: Install from [python.org](https://www.python.org/downloads/)
- **macOS**: Install from [python.org](https://www.python.org/downloads/) or use `brew install python3`
- **Linux**: `sudo apt-get install python3`

#### "Permission denied" (macOS/Linux)
```bash
chmod +x script_name.sh
```

#### "Scripts disabled" (Windows)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### "tkinter not found" (Linux)
```bash
sudo apt-get install python3-tk
```

### **Getting Help**
1. Check the logs: `batch_tool.log` and `batch_tool_debug.log`
2. Verify file structure matches requirements
3. Ensure all required files (JPG, XML, MANIFEST.ini) are present

---

## Additional Documentation

- **`docs/README.md`** - Complete user guide
- **`docs/README_BUILD.md`** - Detailed build instructions  
- **`docs/BUILD_SUMMARY.md`** - Quick build reference

---

## Tips

- **Backup your files** before processing
- **Test with a small subset** of files first
- **Check logs** if processing fails
- **Verify file structure** matches requirements

---

**Ready to start? Choose your platform above and follow the Quick Start Guide!**

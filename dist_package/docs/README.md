# CETAMURA BATCH INGEST TOOL

## Overview

This tool automates the process for creating ingest files for the Cetamura Digital Collections.

## REQUIREMENTS

- **TIFF image files**
- **Corresponding XML metadata files**
- **MANIFEST.ini file** in each folder
- **Organized Folder Structure:** Files must be organized in a `year/trench` structure.

## USAGE INSTRUCTIONS

1. **Select Parent Folder:**
   
   - Click the **"Select Folder"** button to choose the parent directory containing your year folders.
   
   - **Example Folder Structure:**
   
     ```
     Parent_Folder/
     ├── 2006/
     │   ├── 46N-3W/
     │   │   ├── image.tiff
     │   │   ├── metadata.xml
     │   │   └── MANIFEST.ini
     │   └── ...
     └── ...
     ```

2. **Processing Steps:**
   
   The tool will perform the following actions:
   
   - **Update `MANIFEST.ini` Files:**
     - Correct **submitter email**
     - Update **content model**
     - Set **parent collection** information
     
   - **Extract IID:**
     - Retrieve IID values from XML metadata files.
     
   - **Rename Files:**
     - Rename TIFF and XML files to match the extracted IID.
     - Rename ZIP files to match the IID.
     
   - **Organize Renamed Files:**
     - Create a new folder containing the renamed files to maintain organization and prevent clutter.

## IMPORTANT NOTES

- **Backup Files:** Always back up your files before processing them to prevent accidental data loss.
- **File Pairing:** Ensure each trench folder contains matching TIFF and XML files.
- **Valid IID Identifiers:** XML files must contain valid IID identifiers for successful processing.
- **Logging:** Refer to the `batch_tool.log` file for detailed processing logs and error messages.
- **Irreversible Actions:** Processing actions such as renaming cannot be undone. Please make sure it's accurate before proceeding.

## TROUBLESHOOTING

- **Missing Files:** If the tool reports missing or invalid files, verify that all required files are present and correctly named.
- **Log Review:** Check the `batch_tool.log` for detailed error messages and processing steps.
- **Permissions:** Ensure you have permission to read and write files in the selected directories.


## Building Standalone Executables

The application can be bundled into a single executable for different platforms.

### Prerequisites
```bash
pip install pyinstaller Pillow
```

### Build Scripts

#### macOS
```bash
chmod +x build_exe_macos.sh
./build_exe_macos.sh
```
**Output:** `dist/Cetamura_Batch_Tool` (macOS executable)

#### Windows
```powershell
.\build_exe.ps1
```
**Output:** `dist/main.exe` (Windows executable)

#### Cross-Platform (Auto-detect)
```bash
chmod +x build_cross_platform.sh
./build_cross_platform.sh
```

### Manual Build
```bash
# macOS/Linux
pyinstaller --onefile --windowed --name "Cetamura_Batch_Tool" src/main.py --clean

# Windows
pyinstaller --onefile --noconsole src/main.py --clean
```

The resulting executables will be placed in the `dist/` directory. Optional icon and logo files can be added to the `assets/` folder.

For detailed build instructions, see [README_BUILD.md](README_BUILD.md).

# Cetamura Batch Tool

## What It Does
Processes archaeological photo collections by converting JPG images to TIFF format with proper orientation and packaging them into ZIP files.

## Requirements
- Windows 10/11
- Python 3.11+ (or use the executable)

## Quick Start

### Option 1: Run the Executable
1. Download `Cetamura_Batch_Tool.exe` from GitHub releases
2. Double-click to run
3. Select your source folder
4. Click "Start Batch Process"

### Option 2: Run from Source
```bash
git clone [repo-url]
cd cetamura_python_script
pip install -r requirements.txt
python src/main.py
```

## How to Use

1. **Select Folder**: Choose the parent folder containing your photo sets
2. **Processing Options**:
   - **Workflow Type**: `Photo` or `Patent`
   - **Dry Run**: Preview what will happen without changing files
   - **Staging**: Build ZIPs in `staging_output/`
   - **Production**: Build ZIPs in `output/`
3. **Start Processing**: Click the button and wait for completion
4. **Check Results**: Review the CSV report and output folder

## What Gets Processed
- **Photo workflow**: image file + XML metadata + `manifest.ini`
- **Patent workflow**: patent PDF + patent XML + shared `manifest.ini`

## Output
- ZIP packages (one per photo set / patent)
- CSV report of all processing results
- Detailed logs

Source folders remain unchanged in both staging and production. Temporary TIFF conversion work is created only inside the output root and cleaned up after packaging.

## File Locations
- **Output**: `output/` folder in your selected directory
- **Staging**: `staging_output/` folder (for staging mode)
- **Reports**: CSV files with timestamp in filename
- **Logs**: `batch_tool.log` in application folder

## Troubleshooting
- **No photo sets found**: Check folder structure and file naming
- **Processing fails**: Check the CSV report for specific errors
- **Application won't start**: Ensure Python 3.11+ or download fresh executable

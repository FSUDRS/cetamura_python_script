#!/usr/bin/env python3
"""
Production Deployment Script for Cetamura Batch Tool Safety Net Improvements
Creates a production-ready distribution with the enhanced safety features.
"""

import shutil
import os
from pathlib import Path
from datetime import datetime

def create_production_deployment():
    """Create a production deployment with safety net improvements"""
    
    print("🚀 Creating Production Deployment - Safety Net Version")
    print("=" * 60)
    
    # Get current directory (repo root)
    project_root = Path(__file__).resolve().parents[2]
    
    # Create production deployment directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prod_dir = project_root / f"production_deploy_{timestamp}"
    
    print(f"📁 Creating deployment directory: {prod_dir.name}")
    prod_dir.mkdir(exist_ok=True)
    
    # Copy essential files to production
    # Define files as (source_rel_to_root, dest_rel_to_prod)
    files_candidates = [
        ("src/main.py", "main.py"),
        ("requirements/requirements.txt", "requirements.txt"),
        ("README.md", "README.md"),
        ("batch_tool.log", "batch_tool.log"),
        ("assets/", "assets/")
    ]
    
    print("\n📋 Copying files to production deployment:")
    
    for source, dest in files_candidates:
        source_path = project_root / source
        dest_path = prod_dir / dest
        
        if source_path.exists():
            if source_path.is_dir():
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                print(f"✓ {source} -> {dest} (directory)")
            else:
                shutil.copy2(source_path, dest_path)
                print(f"✓ {source} -> {dest}")
        else:
            if source not in ["batch_tool.log", "assets/"]: # Optional files
                 print(f"⚠ {source} not found, skipping")
    
    # Create production documentation
    create_production_docs(prod_dir)
    
    # Create deployment scripts
    create_deployment_scripts(prod_dir)
    
    # Create version info
    create_version_info(prod_dir)
    
    print(f"\n🎉 Production deployment created successfully!")
    print(f"📍 Location: {prod_dir}")
    print(f"\n📋 Deployment includes:")
    print("• Enhanced main.py with safety net features")
    print("• Dry-run and staging mode capabilities")
    print("• CSV reporting system")
    print("• Processing options dialog")
    print("• Comprehensive error handling")
    print("• Production documentation")
    print("• Deployment scripts")
    
    return prod_dir

def create_production_docs(prod_dir):
    """Create production-specific documentation"""
    
    docs_dir = prod_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Production README
    prod_readme = f"""# Cetamura Batch Ingest Tool - Production Release
## Safety Net Version {datetime.now().strftime("%Y.%m.%d")}

### 🎯 NEW SAFETY FEATURES

This production release includes comprehensive safety net improvements:

#### **Dry-Run Mode**
- Preview processing without modifying any files
- Generate detailed CSV reports
- Test folder structure and file validity
- Perfect for testing new datasets

#### **Staging Mode**  
- Output to separate staging directory
- Keep original files completely untouched
- Review and validate before final processing
- Ideal for production workflows

#### **Enhanced Processing Options**
- User-friendly dialog for mode selection
- Clear descriptions of each option
- Modal interface with proceed/cancel options
- Professional user experience

#### **CSV Reporting System**
- Timestamped processing reports
- Track every file: processed, skipped, failed
- Include IID, paths, status, actions, notes
- Summary statistics for audit trails

#### **Robust Error Handling**
- Manifest validation with clear messages
- File pairing validation
- Graceful failure modes
- Comprehensive logging

### 🚀 QUICK START

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Application:**
   ```bash
   python main.py
   ```

3. **Select Processing Mode:**
   - Choose "Start Batch Process"
   - Select desired options:
     - **Dry Run**: Preview without changes
     - **Staging**: Safe output directory
     - **Normal**: Standard processing

4. **Review Results:**
   - Check CSV reports for detailed logs
   - Review staging output before final processing
   - Monitor batch_tool.log for system logs

### 📋 FOLDER STRUCTURE REQUIREMENTS

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

### 🔧 DEPLOYMENT FEATURES

- **Safe Deployment**: Non-destructive processing options
- **Comprehensive Logging**: Full audit trail
- **User-Friendly Interface**: Clear options and feedback
- **Professional Grade**: Ready for production use

### 📞 SUPPORT

- Check `batch_tool.log` for detailed logs
- Review CSV reports for processing details
- Use dry-run mode to test new datasets
- Contact system administrator for issues

---
**Version:** Safety Net Release {datetime.now().strftime("%Y.%m.%d")}  
**Build Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Features:** Dry-Run, Staging, CSV Reporting, Enhanced UX
"""
    
    (docs_dir / "README_PRODUCTION.md").write_text(prod_readme, encoding="utf-8")
    print("✓ Production documentation created")

def create_deployment_scripts(prod_dir):
    """Create deployment scripts for different environments"""
    
    # Windows deployment script
    windows_script = f"""@echo off
REM Cetamura Batch Tool - Production Deployment Script
REM Safety Net Version {datetime.now().strftime("%Y.%m.%d")}

echo Cetamura Batch Ingest Tool - Production Deployment
echo Safety Net Version {datetime.now().strftime("%Y.%m.%d")}
echo ================================================

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo Python installation found

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Dependencies installed successfully

REM Run the application
echo Starting Cetamura Batch Ingest Tool...
python main.py

echo Application closed
pause
"""
    
    (prod_dir / "deploy_windows.bat").write_text(windows_script, encoding="utf-8")
    
    # Linux/macOS deployment script
    unix_script = f"""#!/bin/bash
# Cetamura Batch Tool - Production Deployment Script
# Safety Net Version {datetime.now().strftime("%Y.%m.%d")}

echo "Cetamura Batch Ingest Tool - Production Deployment"
echo "Safety Net Version {datetime.now().strftime("%Y.%m.%d")}"
echo "================================================"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.7+ from your package manager or https://python.org"
    exit 1
fi

echo "Python 3 installation found"

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "Dependencies installed successfully"

# Run the application
echo "Starting Cetamura Batch Ingest Tool..."
python3 main.py

echo "Application closed"
"""
    
    (prod_dir / "deploy_unix.sh").write_text(unix_script, encoding="utf-8")
    
    # Make Unix script executable
    try:
        os.chmod(prod_dir / "deploy_unix.sh", 0o755)
    except:
        pass  # Windows doesn't support chmod
    
    print("✓ Deployment scripts created")

def create_version_info(prod_dir):
    """Create version information file"""
    
    version_info = f"""# Cetamura Batch Ingest Tool - Version Information
# Production Release - Validation & Safety Net Update

VERSION="{datetime.now().strftime('%Y.%m.%d')}"
BUILD_DATE="{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
RELEASE_TYPE="Production - Validation Features"

# Key Features in This Release:
FEATURES = [
    "Post-Processing Validation - Automated verification of ZIP outputs",
    "Reconciliation Reporting - detailed input/output auditing",
    "Expanded File Support - Native processing of PDF and TIFF formats",
    "Pre-Flight Checks - disk space and orphan file detection",
    "Dry-Run Mode - Preview processing without file changes",
    "Staging Mode - Non-destructive output to staging directory", 
    "CSV Reporting - Detailed processing logs with timestamps",
    "Processing Options Dialog - User-friendly mode selection",
    "Enhanced Error Handling - Graceful failures with clear messages",
    "Manifest Validation - Single manifest file enforcement",
    "File Pairing Validation - Robust JPG-XML matching",
    "Comprehensive Logging - Full audit trail capabilities"
]

# Improvements Completed:
COMPLETED_IMPROVEMENTS = [
    "#5 Post-Processing Validation - 100% Complete",
    "#8 UX Polish - 100% Complete",
    "#3 Manifest Validation - 100% Complete", 
    "#6 Safety Nets - 100% Complete",
    "Expanded File Format Support (PDF/TIFF) - 100% Complete",
    "CI/Test Infrastructure - Refactored and Stable"
]

# Technical Details:
PYTHON_VERSION_MIN = "3.7"
DEPENDENCIES = [
    "tkinter (GUI framework)",
    "PIL/Pillow (image processing)",
    "PyMuPDF (PDF processing)",
    "pathlib (file operations)",
    "xml.etree.ElementTree (XML parsing)",
    "csv (report generation)"
]

# Deployment Tested On:
TESTED_PLATFORMS = [
    "Windows 10/11 with Python 3.7+",
    "macOS with Python 3.7+", 
    "Linux with Python 3.7+"
]
"""
    
    (prod_dir / "VERSION_INFO.txt").write_text(version_info, encoding="utf-8")
    print("✓ Version information created")

def main():
    """Main deployment function"""
    try:
        prod_dir = create_production_deployment()
        
        print(f"\n🎯 PRODUCTION DEPLOYMENT READY")
        print("=" * 40)
        print(f"📍 Location: {prod_dir}")
        print("\n📋 Next Steps:")
        print("1. Test the deployment in a safe environment")
        print("2. Use dry-run mode to validate functionality")
        print("3. Deploy to production systems")
        print("4. Train users on new safety features")
        print("\n✅ Ready for production use!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    input("\\nPress Enter to exit...")
    exit(0 if success else 1)

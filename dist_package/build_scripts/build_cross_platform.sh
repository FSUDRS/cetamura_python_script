#!/bin/bash
# Cross-platform build script for Cetamura Batch Ingest Tool
# Automatically detects the operating system and builds accordingly

echo "Detecting operating system..."

# Detect the operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "macOS detected"
    echo "Building for macOS..."
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is not installed or not in PATH"
        echo "Install Python 3 from https://www.python.org/downloads/"
        exit 1
    fi
    
    # Install required packages
    echo "Installing required packages..."
    pip3 install pyinstaller Pillow
    
    # Build the executable
    echo "Building executable..."
    pyinstaller --onefile --windowed --name "Cetamura_Batch_Tool" src/main.py --clean
    
    # Check if build was successful
    if [ -f "dist/Cetamura_Batch_Tool" ]; then
        chmod +x dist/Cetamura_Batch_Tool
        echo "Build completed successfully!"
        echo "Executable created: dist/Cetamura_Batch_Tool"
        echo "To run: ./dist/Cetamura_Batch_Tool"
    else
        echo "Build failed!"
        exit 1
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Linux detected"
    echo "Building for Linux..."
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is not installed"
        echo "Install with: sudo apt-get install python3 python3-pip"
        exit 1
    fi
    
    # Install required packages
    echo "Installing required packages..."
    pip3 install pyinstaller Pillow
    
    # Build the executable
    echo "Building executable..."
    pyinstaller --onefile --name "Cetamura_Batch_Tool" src/main.py --clean
    
    # Check if build was successful
    if [ -f "dist/Cetamura_Batch_Tool" ]; then
        chmod +x dist/Cetamura_Batch_Tool
        echo "Build completed successfully!"
        echo "Executable created: dist/Cetamura_Batch_Tool"
        echo "To run: ./dist/Cetamura_Batch_Tool"
    else
        echo "Build failed!"
        exit 1
    fi
    
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash or Cygwin)
    echo "Windows detected (Git Bash/Cygwin)"
    echo "For Windows, please use build_exe.ps1 in PowerShell instead"
    echo "   Run: .\build_exe.ps1"
    exit 1
    
else
    echo "Unsupported operating system: $OSTYPE"
    echo "Supported platforms: macOS, Linux"
    echo "For Windows, use build_exe.ps1"
    exit 1
fi

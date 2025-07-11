#!/bin/bash
# Build the Tkinter GUI into a single executable on macOS
# Requires PyInstaller to be installed (pip install pyinstaller Pillow)

echo "Building Cetamura Batch Ingest Tool for macOS..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed or not in PATH"
    exit 1
fi

# Install required packages if not already installed
echo "Installing required packages..."
pip3 install pyinstaller Pillow

# Build the executable
echo "Building executable..."
pyinstaller --onefile --windowed --name "Cetamura_Batch_Tool" src/main.py --clean

# Check if build was successful
if [ -f "dist/Cetamura_Batch_Tool" ]; then
    echo "Build completed successfully!"
    echo "Executable created: dist/Cetamura_Batch_Tool"
    echo "To run: ./dist/Cetamura_Batch_Tool"
    
    # Make it executable
    chmod +x dist/Cetamura_Batch_Tool
    echo "Made executable"
else
    echo "Build failed! Check the output above for errors."
    exit 1
fi

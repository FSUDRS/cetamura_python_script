#!/bin/bash
# Setup script for macOS - Cetamura Batch Ingest Tool
# This script installs dependencies and builds the macOS executable

echo "Cetamura Batch Ingest Tool - macOS Setup"
echo "========================================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "This script is for macOS only"
    exit 1
fi

# Check if Python 3 is installed
echo "Checking Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed"
    echo "Please install Python 3 from: https://www.python.org/downloads/"
    echo "Or install via Homebrew: brew install python3"
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    echo "Found: $PYTHON_VERSION"
fi

# Check if pip3 is available
echo "Checking pip3..."
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not available"
    echo "Please install pip3 or reinstall Python 3"
    exit 1
else
    echo "pip3 is available"
fi

# Install required packages
echo "Installing required packages..."
pip3 install --user pyinstaller Pillow

# Check if installation was successful
if pip3 show pyinstaller > /dev/null 2>&1 && pip3 show Pillow > /dev/null 2>&1; then
    echo "Dependencies installed successfully"
else
    echo "Failed to install dependencies"
    exit 1
fi

# Make build script executable
echo "Setting up build script..."
chmod +x build_exe_macos.sh
chmod +x build_cross_platform.sh

# Build the executable
echo "Building macOS executable..."
./build_exe_macos.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "Setup completed successfully!"
    echo "Executable location: dist/Cetamura_Batch_Tool"
    echo "To run: ./dist/Cetamura_Batch_Tool"
    echo ""
    echo "You can also run the Python script directly:"
    echo "   python3 src/main.py"
else
    echo "Build failed. Check the output above for errors."
    exit 1
fi

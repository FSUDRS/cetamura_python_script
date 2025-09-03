#!/bin/bash
# macOS Installation Script for Cetamura Batch Ingest Tool
# Save this as install_macos.sh and run with: chmod +x install_macos.sh && ./install_macos.sh

echo "macOS - Cetamura Batch Ingest Tool Installer"
echo "============================================"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "This installer is for macOS only"
    exit 1
fi

# Check if Python 3 is installed
echo "Checking for Python 3..."
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
echo "Checking for pip3..."
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not available"
    echo "Please install pip3 or reinstall Python 3"
    exit 1
else
    echo "pip3 is available"
fi

# Install required packages
echo "Installing required packages..."
if pip3 install -r requirements/requirements.txt; then
    echo "Dependencies installed successfully"
else
    echo "Failed to install dependencies"
    exit 1
fi

# Copy source file to main directory for easy access
cp source/main.py . 2>/dev/null || echo "Could not copy source file"
echo "Source file copied to main directory"

# Make build scripts executable
chmod +x build_scripts/*.sh 2>/dev/null || echo "Could not make build scripts executable"

# Copy setup script to main directory
cp build_scripts/setup_macos.sh . 2>/dev/null
chmod +x setup_macos.sh 2>/dev/null

echo ""
echo "Installation completed successfully!"
echo ""
echo "How to run:"
echo "   1. Run from Python: python3 main.py"
echo "   2. Build macOS executable: ./setup_macos.sh"
echo "   3. Build manually: python3 -m pip install pyinstaller && pyinstaller --onefile --windowed --name 'Cetamura_Batch_Tool' source/main.py"
echo ""
echo "To build the macOS executable, run: ./setup_macos.sh"
echo ""

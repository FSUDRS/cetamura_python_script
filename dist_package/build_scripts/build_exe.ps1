# Build the Tkinter GUI into a single executable on Windows
# Requires PyInstaller to be installed (pip install pyinstaller Pillow)
# This version uses a self-contained main.py with all utility functions included

# Use the virtual environment's pyinstaller
C:\Users\saa24b\Cetamura_Fork\cetamura_python_script\.venv\Scripts\pyinstaller.exe --onefile --noconsole src\main.py --clean

Write-Host "Build completed! Check the 'dist' folder for the executable."

#!/bin/bash
# Build the Tkinter GUI into a single executable.
# Requires PyInstaller to be installed (pip install pyinstaller Pillow)
pyinstaller --onefile --noconsole src/main.py

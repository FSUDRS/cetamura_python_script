# CI/CD Setup

## What This Does
Automatically builds Windows executables when you push code to GitHub.

## Setup Steps

1. **Enable GitHub Actions**
   - GitHub Actions is already configured in `.github/workflows/`
   - Pushes to `main` branch trigger builds automatically

2. **Build Process**
   - Uses PyInstaller to create `Cetamura_Batch_Tool.exe`
   - Builds on Windows runner with Python 3.11
   - Includes all dependencies in single executable

3. **Get Your Build**
   - Go to Actions tab in GitHub
   - Download the executable from latest successful run
   - File is ready to distribute

## Manual Build
```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed src/main.py --name Cetamura_Batch_Tool

# Find your .exe in dist/ folder
```

## Troubleshooting
- **Build fails**: Check Python version matches (3.11)
- **Missing modules**: Add to `requirements.txt`
- **Large file size**: Normal for bundled executable (~50MB)
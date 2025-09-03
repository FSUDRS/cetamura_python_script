How to build the Windows installer (NSIS)

Prerequisites
- NSIS (makensis) installed and available on PATH: https://nsis.sourceforge.io/Download
- Ensure the onedir build is present at `dist/Cetamura_Batch_Tool/`

Build steps (PowerShell):

```powershell
# From repository root
cd release\installer
makensis Cetamura_Batch_Tool_installer.nsi
```

Output
- `Cetamura_Batch_Tool_Installer.exe` will be created in the same folder.

Notes
- The NSIS script copies the contents of `..\..\dist\Cetamura_Batch_Tool` into the installer. Adjust the path in `Cetamura_Batch_Tool_installer.nsi` if your build output is elsewhere.
- If you want an install that writes to Program Files (requires admin), change `RequestExecutionLevel user` to `RequestExecutionLevel admin` in the NSIS script.

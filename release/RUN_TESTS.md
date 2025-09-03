Cetamura Batch Tool — Quick start (one-folder ZIP)

Overview
- This README explains how to run the packaged one-folder distribution `Cetamura_Batch_Tool_onedir.zip` by extracting it and running the bundled `Cetamura_Batch_Tool.exe`.

Prerequisites
- Windows 10/11, x64 recommended.
- No admin rights required to run the extracted onedir binary. Installer (if used) may require elevation.

Files shipped in this release
- `Cetamura_Batch_Tool_onedir.zip` — one-folder distribution. Contains `Cetamura_Batch_Tool.exe` and its supporting files.
- `Cetamura_Batch_Tool_Windows.exe` — single-file packaged build (available as a release asset). Use the onedir ZIP if you see runtime bootstrap issues.

Extracting and running (PowerShell)
1) Open PowerShell and change to a folder where you want to extract the onedir (for example `C:\temp`).

```powershell
cd C:\temp
Expand-Archive -Path "<path-to-release>\Cetamura_Batch_Tool_onedir.zip" -DestinationPath . -Force
cd .\Cetamura_Batch_Tool
.\Cetamura_Batch_Tool.exe --help
```

- Replace `<path-to-release>` with the local path where you downloaded the ZIP.
- The `--help` flag prints usage information; running the EXE without flags launches the GUI.

Run the GUI (double-click)
- After extraction, double-click `Cetamura_Batch_Tool.exe` in File Explorer to launch the GUI.

Simple processing smoke test
1) Prepare a small sample photo set: a folder with 2–5 JPEG/PNG files.
2) In the app, use the folder picker to point to the sample folder.
3) Use default settings and start processing.
Expected: processing begins, progress updates appear, and the app does not crash.

CLI quick checks
- Version: `Cetamura_Batch_Tool.exe --version`
- Help: `Cetamura_Batch_Tool.exe --help`

Troubleshooting
- If the single-file EXE fails at startup with import/bootstrap errors, extract `Cetamura_Batch_Tool_onedir.zip` and run the extracted `Cetamura_Batch_Tool.exe`.
- If the GUI launches but processing fails, collect these items and attach them to an issue:
   - `batch_tool.log` (if created in the working folder)
   - stdout/stderr output from running the EXE in PowerShell (run `.\Cetamura_Batch_Tool.exe` from PowerShell and copy output)

Where to find artifacts
- Release: FSUDRS/cetamura_python_script — tag `v2025.08.26-7e386f2`.
- Release assets include `Cetamura_Batch_Tool_onedir.zip`, `Cetamura_Batch_Tool_Windows.exe`, and this `RUN_TESTS.md` file.

Contact / reporting
- Open an issue in the repository and mention the release tag: `v2025.08.26-7e386f2`.

Last updated: 2025-08-26

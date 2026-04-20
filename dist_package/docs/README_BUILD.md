# Cetamura Batch Ingest Tool - Build Instructions

These instructions build the Tkinter desktop application from the repository root.

## Prerequisites

- Python 3.9+
- Runtime dependencies from `requirements/requirements.txt`
- PyInstaller, installed through the build scripts when `--install-dependencies` or `-InstallDependencies` is used

## Windows

```powershell
.\scripts\build\build_exe.ps1 -InstallDependencies
```

Output:

```text
dist\CetamuraBatchIngest.exe
```

## macOS

```bash
./scripts/build/build_exe_macos.sh --install-dependencies
```

Output:

```text
dist/CetamuraBatchIngest
```

## Linux

```bash
./scripts/build/build_cross_platform.sh --install-dependencies
```

Output:

```text
dist/CetamuraBatchIngest
```

## Manual Build

```bash
python -m pip install -r requirements/requirements.txt
python -m pip install pyinstaller
python -m PyInstaller src/main.py --name CetamuraBatchIngest --onefile --clean --noconfirm --hidden-import PIL --hidden-import fitz --collect-all fitz
```

For Windows and macOS GUI builds, include the `--windowed` flag.

# Cetamura Batch Ingest Tool

## Overview

The Cetamura Batch Ingest Tool creates ingest-ready ZIP packages for two workflows:

- `Photo`: image asset + XML metadata + `manifest.ini`
- `Patent`: PDF + XML metadata + shared `manifest.ini`

Current staging and production runs are non-mutating. Source folders are treated as read-only, and generated ZIPs, reports, and scratch files are written under `staging_output/`, `output/`, or the active output workspace.

## Requirements

- Windows 10 or 11 for the primary supported desktop workflow
- Python 3.9+
- Runtime dependencies from `requirements/requirements.txt`

## Run From Source

```bash
python -m pip install -r requirements/requirements.txt
python src/main.py
```

## Photo Workflow

Expected input:

- image file such as `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, or `.pdf`
- matching XML metadata containing an IID
- `manifest.ini`

Each successful ZIP contains one TIFF, one XML file, and `manifest.ini`.

## Patent Workflow

Expected input:

- one or more patent XML files in a batch directory
- one shared `manifest.ini` in that same batch directory
- matching patent PDFs in the batch directory, or in configured fallback search roots

Each successful ZIP contains one PDF, one XML file, and `manifest.ini`.

## Run Modes

- `Dry Run`: validates and reports without creating ZIP files.
- `Staging`: writes reviewable ZIPs and reports to `staging_output/`.
- `Production`: writes final ZIPs and reports to `output/`.

## Build Executables

Windows:

```powershell
.\scripts\build\build_exe.ps1 -InstallDependencies
```

macOS:

```bash
./scripts/build/build_exe_macos.sh --install-dependencies
```

Linux:

```bash
./scripts/build/build_cross_platform.sh --install-dependencies
```

## Release Package

Generate a source package from the repository root:

```powershell
.\scripts\build\create_dist_package.ps1 -Version 1.3.0
```

See `docs/RELEASE_CHECKLIST.md` for the full release verification workflow.

# Cetamura Batch Ingest Tool

![Version](https://img.shields.io/badge/version-1.3.0-blue)
![Build](https://img.shields.io/badge/build-GitHub_Actions-brightgreen)

## Overview

The Cetamura Batch Ingest Tool packages ingest-ready ZIP files for two workflows:

- `Photo`: image asset + XML metadata + `manifest.ini`
- `Patent`: PDF + XML metadata + shared `manifest.ini`

The current application is workflow-aware, non-mutating, and designed so staging and production runs never modify source folders. Generated ZIPs, reports, and temporary scratch files are written only under the selected folder's `output/` or `staging_output/` directory.

## Key Features

- GUI workflow selector for `Photo` and `Patent`
- `Dry Run`, `Staging`, and `Production` run modes
- Non-mutating processing in both staging and production
- Output-side scratch workspace for photo TIFF conversion
- Patent batch packaging with shared manifest validation
- Optional fallback patent PDF lookup via `CETAMURA_PATENT_SEARCH_ROOTS`
- CSV reporting, technical logs, and user-facing summary logs
- Pre-flight checks, ZIP validation, and reconciliation reporting
- GitHub Actions CI for tests and regression coverage

## Supported Workflows

### Photo Workflow

Expected input:

- image file such as `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, or `.pdf`
- matching XML metadata containing an IID
- `manifest.ini`

Behavior:

- source images are read only
- TIFF conversion happens in an output-side scratch workspace
- ZIP contents are `TIFF + XML + manifest.ini`

### Patent Workflow

Expected input:

- one or more patent XML files in a batch directory
- one shared `manifest.ini` in that same batch directory
- matching patent PDFs in the batch directory, or in configured fallback search roots

Behavior:

- canonical package name comes from XML `<identifier type="IID">`
- XML filename stem must match the IID
- normalized XML `document ID` must match the IID
- ZIP contents are `PDF + XML + manifest.ini`

Required patent manifest values:

```ini
[package]
submitter_email = rmr17b@fsu.edu
content_model = ir:citationCModel
parent_collection = fsu:florida_state_university_patents
```

## Run Modes

### Dry Run

- performs discovery, validation, and CSV reporting
- creates no ZIP files
- leaves source and output packages untouched

### Staging

- writes ZIP files and reports to `staging_output/`
- intended for review before production

### Production

- writes ZIP files and reports to `output/`
- intended for final ingest-ready packaging

## Running From Source

### Requirements

- Windows 10 or 11
- Python `3.9+`

### Install

```bash
git clone https://github.com/FSUDRS/cetamura_python_script.git
cd cetamura_python_script
python -m pip install --upgrade pip
python -m pip install -r requirements/requirements.txt
```

### Launch

```bash
python src/main.py
```

### Optional Development Dependencies

```bash
python -m pip install -r requirements/requirements-dev.txt
```

## Patent PDF Fallback Configuration

If patent PDFs may live outside the selected batch folder, configure fallback search roots with the `CETAMURA_PATENT_SEARCH_ROOTS` environment variable.

Windows example:

```powershell
$env:CETAMURA_PATENT_SEARCH_ROOTS = "C:\patents\primary;D:\cetamura\archive"
python src\main.py
```

Use the platform path separator when providing multiple roots.

## Output and Logs

For a selected source folder:

- staging ZIPs are written to `staging_output/`
- production ZIPs are written to `output/`
- CSV reports are written to the active output folder, or to the selected folder during dry run
- technical logs are written to `batch_tool.log`
- user-facing summary logs are written to `batch_process_summary.log`

The application may create a temporary `.work/` directory under the active output root during processing. It is cleaned up after successful runs.

## Validation and Safety Nets

Before processing:

- disk space is checked
- output write access is checked
- configured patent fallback roots are validated when patent mode is active

After processing:

- ZIP counts are validated against successful CSV rows
- ZIP contents are validated by workflow
- reconciliation compares XML count, CSV success count, actual ZIP count, and valid ZIP count

## Testing

Run the local test suite:

```bash
python -m pytest
```

Run the project test runner:

```bash
python tests/run_tests.py
```

The GitHub Actions workflow runs on pushes to `main`, `master`, and `ci-cd-development`.

## Repository Layout

```text
cetamura_python_script/
  .github/
    workflows/
      ci.yml
  docs/
    readme.md
  requirements/
    requirements.txt
    requirements-dev.txt
  src/
    main.py
    validation.py
  tests/
    run_tests.py
    test_global_recovery.py
    test_main.py
    test_validation.py
  README.md
  pytest.ini
```

## Troubleshooting

- `No valid photo sets detected`: verify image files, XML files, and `manifest.ini` placement.
- `No valid patent batch directories detected`: verify patent XML files and exactly one shared `manifest.ini` in the batch directory.
- `No PDF found for ...`: either place the PDF in the selected patent batch folder or configure `CETAMURA_PATENT_SEARCH_ROOTS`.
- `Post-processing validation failed`: review the CSV report and `batch_tool.log` for ZIP or count mismatches.

## Current Status

The current release includes:

- non-mutating staging and production behavior
- patent batch packaging
- workflow-aware GUI refresh
- garnet-and-gold UI theme
- expanded regression coverage and CI compatibility updates

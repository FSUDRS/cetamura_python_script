# Cetamura Batch Tool User Guide

## What The Tool Does

The Cetamura Batch Tool creates ingest-ready ZIP packages for:

- `Photo` batches
- `Patent` batches

The application is non-mutating. Source folders are treated as read-only in both staging and production runs.

## Before You Start

### Photo Workflow

Have these ready:

- image files
- matching XML metadata files
- `manifest.ini`

### Patent Workflow

Have these ready:

- patent XML files in one batch directory
- one shared `manifest.ini` in that same directory
- matching PDFs in the same directory, or accessible through configured fallback search roots

Required patent manifest values:

```ini
[package]
submitter_email = rmr17b@fsu.edu
content_model = ir:citationCModel
parent_collection = fsu:florida_state_university_patents
```

## Main Screen

The refreshed interface is organized around the current system:

- choose a workflow first
- select a folder
- review the readiness summary
- start a run from the run-settings dialog

The UI theme uses garnet and gold to reflect the current design refresh.

## How To Run A Batch

1. Open the application.
2. Choose `Photo Workflow` or `Patent Workflow`.
3. Click `Select Folder`.
4. Review the summary shown in the main window.
5. Click `Review and Run ... Batch`.
6. Choose one of the run modes below.

## Run Modes

### Dry Run

Use this when you want to preview the batch.

- no ZIP files are created
- a CSV report is still generated
- validation still runs

### Staging

Use this when you want reviewable output.

- ZIP files are written to `staging_output/`
- source files stay unchanged

### Production

Use this when you want final output.

- ZIP files are written to `output/`
- source files stay unchanged

## What Gets Written

### Photo Output

Each successful package contains:

- one TIFF
- one XML
- `manifest.ini`

### Patent Output

Each successful package contains:

- one PDF
- one XML
- `manifest.ini`

ZIPs are named from the package ID:

- photo packages use the IID
- patent packages use the patent IID

## Logs And Reports

The tool writes:

- CSV report for the run
- `batch_tool.log` for detailed technical logging
- `batch_process_summary.log` for user-facing run output

The CSV report is the first place to check when a file is skipped or a batch fails validation.

## Patent PDF Fallback

If patent PDFs are not always stored in the selected batch folder, set the environment variable:

- `CETAMURA_PATENT_SEARCH_ROOTS`

Windows example:

```powershell
$env:CETAMURA_PATENT_SEARCH_ROOTS = "C:\patents\primary;D:\cetamura\archive"
python src\main.py
```

## Validation

The tool performs:

- pre-flight checks before packaging
- ZIP validation after packaging
- reconciliation reporting after successful non-dry-run runs

This helps catch:

- missing output ZIPs
- invalid ZIP structure
- patent manifest issues
- missing or ambiguous patent PDFs
- dry-run violations

## Common Problems

### No valid photo sets detected

Check:

- images are present
- XML files are present
- `manifest.ini` is present

### No valid patent batch directories detected

Check:

- XML files are present
- exactly one `manifest.ini` is present
- patent XML filenames match the IID values

### No PDF found for a patent

Check:

- the PDF exists in the selected batch folder
- or `CETAMURA_PATENT_SEARCH_ROOTS` points to the correct fallback location

### Validation failed after processing

Check:

- the CSV report
- `batch_tool.log`
- the output ZIP contents

## Running From Source

```bash
python -m pip install -r requirements/requirements.txt
python src/main.py
```

For local development and testing:

```bash
python -m pip install -r requirements/requirements-dev.txt
python -m pytest
```

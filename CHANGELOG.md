# Changelog

## Unreleased

### Changed
- Increased the Tkinter UI font scale for better readability across the main window, run-settings dialog, workflow guide, buttons, radio controls, status text, and helper copy.
- Set the main app window to a fixed 1100x700 size while keeping scrollable main content, dynamic text wrapping, and narrow-window stacking for workflow/action controls.
- Enlarged the run-settings dialog, workflow guide, and progress bar to keep the larger text comfortable.

## 1.3.0 - 2026-04-20

### Added
- Photo and patent workflow selection from the GUI.
- Non-mutating staging and production packaging for source folders.
- Patent batch packaging with shared manifest validation and optional PDF fallback roots.
- Post-processing ZIP validation, reconciliation reporting, and pre-flight checks.
- Expanded regression coverage for multi-file photo sets, patent batches, and validation logic.
- Security scanning in CI with Bandit and dependency auditing.
- Reproducible release helper scripts under `scripts/build/`.

### Changed
- Production output now writes only to `output/`; staging output writes only to `staging_output/`.
- Photo TIFF conversion now runs in output-side scratch space during current batch workflows.
- Development requirements can be installed from either `requirements-dev.txt` or `requirements/requirements-dev.txt`.
- The production deployment helper now includes `validation.py`, which is required by `main.py`.

### Fixed
- Local `main` is fast-forwarded to `origin/main` so the release includes newline, degree-symbol, and validation assertion fixes.
- Tracked utility scripts are Black and flake8 clean.
- Removed a NUL-corrupted line from `.gitignore`.

### Verified
- `python -m pytest tests/ -v --tb=short`: 65 passed.
- `python tests/run_tests.py`: 65 passed plus import and quick checks.
- `python -m black --check ...`: passing for tracked Python release files.
- `python -m flake8 --jobs 1 ...`: passing for tracked Python release files.
- `python -m bandit -r src -ll`: no medium or high severity issues identified.
- `python -m pip_audit -r requirements/requirements.txt`: no known vulnerabilities found.

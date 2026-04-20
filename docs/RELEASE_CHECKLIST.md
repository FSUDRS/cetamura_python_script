# Release Checklist

Use this checklist for the 1.3.0 release and future maintenance releases.

## 1. Confirm Branch State

```bash
git status --short --branch
git log --oneline --decorate -5
```

The release branch should be clean and up to date with `origin/main`.

## 2. Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements/requirements.txt
python -m pip install -r requirements/requirements-dev.txt
```

## 3. Run Verification

```bash
python -m pytest tests/ -v --tb=short
python tests/run_tests.py
python -m black --check src tests test_expanded_support.py scripts/utilities/analyze_structure.py scripts/utilities/create_manifest_test.py scripts/utilities/create_production_deploy.py scripts/utilities/debug_validation.py scripts/utilities/diagnostic_tool.py scripts/utilities/main_modular.py
python -m flake8 --jobs 1 src tests test_expanded_support.py scripts/utilities/analyze_structure.py scripts/utilities/create_manifest_test.py scripts/utilities/create_production_deploy.py scripts/utilities/debug_validation.py scripts/utilities/diagnostic_tool.py scripts/utilities/main_modular.py
python -m bandit -r src -ll
python -m pip_audit -r requirements/requirements.txt
```

## 4. Build Optional Executable

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

## 5. Prepare Source Package

```powershell
.\scripts\build\create_dist_package.ps1 -Version 1.3.0
```

The package includes `src/main.py`, `src/validation.py`, runtime requirements, release docs, and build scripts. If a Windows executable already exists in `dist/`, it is copied into the package.

## 6. Release Notes

Use [CHANGELOG.md](../CHANGELOG.md) as the source for the GitHub release summary. Include:

- release version and date
- user-facing workflow changes
- validation and safety improvements
- verification commands that passed
- any known limitations from [Bugs.md](Bugs.md)

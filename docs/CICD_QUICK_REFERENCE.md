# CI/CD Quick Reference Guide

A quick reference for common CI/CD operations in the Cetamura Batch Tool project.

## Testing

### Run All Tests
```bash
python -m pytest
```

### Run Tests with Coverage
```bash
python -m pytest --cov=cetamura
```

### Generate Coverage Report
```bash
python -m pytest --cov=cetamura --cov-report=html
# Opens HTML report in browser
```

## Code Quality

### Run Pre-commit Hooks
```bash
pre-commit run --all-files
```

### Format Code with Black
```bash
black src tests
```

### Run Linting
```bash
flake8 src tests
```

### Run Type Checking
```bash
mypy src
```

## CI Workflows

### Check CI Status
1. Go to your repository on GitHub
2. Click on "Actions" tab
3. View recent workflow runs

### Troubleshoot Failed CI
1. Click on the failed workflow run
2. Expand the failed job
3. Review the logs for error messages
4. Fix issues locally and push changes

## CD/Release Process

### Create a New Release
```bash
# Update version in relevant files
# Commit changes
git commit -m "Bump version to x.y.z"

# Create and push tag
git tag vx.y.z
git push origin vx.y.z
```

### Verify Release Build
1. Go to GitHub repository
2. Click on "Actions" tab
3. Check the release workflow
4. Verify artifacts were created

### Access Release Artifacts
1. Go to GitHub repository
2. Click on "Releases"
3. Find your release
4. Download artifacts

## Local Build

### Build Executable
```bash
# Windows
pyinstaller Cetamura_Batch_Tool.spec

# Output will be in dist/ directory
```

## Tips and Tricks

### Skip CI for Minor Changes
Add `[skip ci]` to your commit message to skip CI workflows:
```bash
git commit -m "Update documentation [skip ci]"
```

### Trigger Manual Workflow Run
1. Go to GitHub repository
2. Click on "Actions"
3. Select the workflow
4. Click "Run workflow" button
5. Select branch and click "Run workflow"

### Clean Build Files
```bash
# Remove build artifacts
rm -rf build/ dist/ *.spec
```

### Force Re-download Dependencies in CI
Add a unique comment to requirements.txt to bypass caching.

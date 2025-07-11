# Cetamura Batch Ingest Tool - Development Setup
# Run this script to set up the development environment

Write-Host "Cetamura Batch Ingest Tool - Development Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "Python 3 is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3 from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Write-Host ""
Write-Host "Development setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the application:" -ForegroundColor Cyan
Write-Host "  python src/main.py" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor Cyan
Write-Host "  pytest tests/" -ForegroundColor White
Write-Host ""
Write-Host "To build executables:" -ForegroundColor Cyan
Write-Host "  See dist_package/docs/BUILD_SUMMARY.md" -ForegroundColor White
Write-Host ""

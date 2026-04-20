# Windows installation helper for Cetamura Batch Ingest Tool.

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$Requirements = Join-Path $PackageRoot "requirements\requirements.txt"
$MainScript = Join-Path $PackageRoot "src\main.py"
$ExePath = Join-Path $PackageRoot "executables\CetamuraBatchIngest.exe"

if (-not (Test-Path $Requirements)) {
    $Requirements = Resolve-Path (Join-Path $PackageRoot "..\requirements\requirements.txt")
}

if (-not (Test-Path $MainScript)) {
    $MainScript = Resolve-Path (Join-Path $PackageRoot "..\src\main.py")
}

Write-Host "Windows - Cetamura Batch Ingest Tool Installer" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

try {
    $PythonVersion = python --version 2>&1
    Write-Host "Python found: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python 3.9+ is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Install Python from https://www.python.org/downloads/ and enable PATH." -ForegroundColor Yellow
    exit 1
}

python -m pip install --upgrade pip
python -m pip install -r $Requirements

if (Test-Path $ExePath) {
    Write-Host "Executable available: $ExePath" -ForegroundColor Green
} else {
    Write-Host "Run from source with:" -ForegroundColor Cyan
    Write-Host "python `"$MainScript`"" -ForegroundColor White
}

Write-Host "Installation completed successfully." -ForegroundColor Green

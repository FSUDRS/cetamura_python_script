Write-Host "Starting Build Process for Cetamura Batch Tools..."

# Ensure PyInstaller is installed
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "PyInstaller not found in path. Trying via python -m..."
    $PY = ".venv\Scripts\python.exe"
} else {
    $PY = "pyinstaller"
}

# Clean previous builds
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Run PyInstaller
# --onefile: Create a single EXE
# --windowed: No console window (GUI app)
# --name: Output name
# --add-data: Include src folder for runtime resources
# --hidden-import: Ensure critical libraries are found
Write-Host "Running PyInstaller..."
& $PY -m PyInstaller src/main.py `
    --name "CetamuraBatchIngest" `
    --onefile `
    --windowed `
    --clean `
    --noconfirm `
    --hidden-import="PIL" `
    --hidden-import="fitz" `
    --collect-all="fitz"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build Successful!"
    Write-Host "Executable is located at: dist\CetamuraBatchIngest.exe"
} else {
    Write-Host "Build Failed!"
    exit 1
}

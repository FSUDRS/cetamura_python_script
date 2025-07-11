# Windows Installation Script for Cetamura Batch Ingest Tool
# Save this as install_windows.ps1 and run in PowerShell

Write-Host "Windows - Cetamura Batch Ingest Tool Installer" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

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
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Copy source file to main directory for easy access
Copy-Item "source\main.py" "." -Force
Write-Host "Source file copied to main directory" -ForegroundColor Green

# Create desktop shortcut for the executable
$exePath = Join-Path (Get-Location) "executables\Cetamura_Batch_Tool_Windows.exe"
$shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Cetamura Batch Tool.lnk"

try {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = Get-Location
    $shortcut.Description = "Cetamura Batch Ingest Tool"
    $shortcut.Save()
    Write-Host "Desktop shortcut created" -ForegroundColor Green
} catch {
    Write-Host "Could not create desktop shortcut" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "How to run:" -ForegroundColor Cyan
Write-Host "   1. Use desktop shortcut (if created)" -ForegroundColor White
Write-Host "   2. Double-click: executables\Cetamura_Batch_Tool_Windows.exe" -ForegroundColor White
Write-Host "   3. Run from Python: python main.py" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"

param(
    [switch]$InstallDependencies
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Python = "python"
if (Test-Path $VenvPython) {
    try {
        & $VenvPython --version *> $null
        if ($LASTEXITCODE -eq 0) {
            $Python = $VenvPython
        } else {
            Write-Warning "Ignoring broken virtual environment Python at $VenvPython"
        }
    } catch {
        Write-Warning "Ignoring broken virtual environment Python at $VenvPython"
    }
}

Write-Host "Building Cetamura Batch Ingest for Windows..." -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot"
Write-Host "Python: $Python"

if ($InstallDependencies) {
    & $Python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed with exit code $LASTEXITCODE" }

    & $Python -m pip install -r requirements/requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "dependency install failed with exit code $LASTEXITCODE" }
}

& $Python -m PyInstaller src/main.py `
    --name "CetamuraBatchIngest" `
    --onefile `
    --windowed `
    --clean `
    --noconfirm `
    --hidden-import="PIL" `
    --hidden-import="fitz" `
    --collect-all="fitz"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

Write-Host "Build successful: dist\CetamuraBatchIngest.exe" -ForegroundColor Green

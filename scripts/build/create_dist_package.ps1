param(
    [string]$Version = "1.3.0"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ReleaseRoot = Join-Path $RepoRoot "release"
$PackageName = "cetamura-batch-ingest-$Version"
$PackageRoot = Join-Path $ReleaseRoot $PackageName

Set-Location $RepoRoot

if (Test-Path $PackageRoot) {
    Remove-Item -Recurse -Force $PackageRoot
}

New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot "src") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot "requirements") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot "docs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot "scripts\build") | Out-Null

Copy-Item README.md $PackageRoot
Copy-Item src\main.py (Join-Path $PackageRoot "src")
Copy-Item src\validation.py (Join-Path $PackageRoot "src")
Copy-Item requirements\requirements.txt (Join-Path $PackageRoot "requirements")
Copy-Item docs\readme.md (Join-Path $PackageRoot "docs")
Copy-Item docs\RELEASE_CHECKLIST.md (Join-Path $PackageRoot "docs") -ErrorAction SilentlyContinue
Copy-Item scripts\build\build_exe.ps1 (Join-Path $PackageRoot "scripts\build")
Copy-Item scripts\build\build_exe_macos.sh (Join-Path $PackageRoot "scripts\build")
Copy-Item scripts\build\build_cross_platform.sh (Join-Path $PackageRoot "scripts\build")

$DistExe = Join-Path $RepoRoot "dist\CetamuraBatchIngest.exe"
if (Test-Path $DistExe) {
    New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot "executables") | Out-Null
    Copy-Item $DistExe (Join-Path $PackageRoot "executables")
}

$VersionInfo = @"
Cetamura Batch Ingest Tool
Version: $Version
Release package created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Run from source:
  python -m pip install -r requirements/requirements.txt
  python src/main.py

Build Windows executable:
  .\scripts\build\build_exe.ps1 -InstallDependencies
"@

Set-Content -Path (Join-Path $PackageRoot "VERSION_INFO.txt") -Value $VersionInfo -Encoding UTF8

Write-Host "Release package prepared: $PackageRoot" -ForegroundColor Green

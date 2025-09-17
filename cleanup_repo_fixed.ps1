﻿# Cetamura Project Major Cleanup Script
# Removes redundant folders and files while preserving essential working components

Write-Host "ðŸ§¹ Starting Cetamura Project Major Cleanup..." -ForegroundColor Green
Write-Host "ðŸŽ¯ Target: Remove redundant modular structure, keep working src/main.py" -ForegroundColor Cyan

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "âŒ Error: Not in a git repository root. Please run from project root." -ForegroundColor Red
    exit 1
}

# Create backup branch before major cleanup
Write-Host "ðŸ“¦ Creating backup branch before cleanup..." -ForegroundColor Yellow
$backupBranch = "cleanup-backup-$(Get-Date -Format "yyyyMMdd-HHmmss")"
git branch $backupBranch 2>$null
Write-Host "âœ… Created backup branch: $backupBranch" -ForegroundColor Green

# MAJOR REDUNDANCY: Remove entire cetamura/ modular structure
Write-Host "`nðŸ—‚ï¸  MAJOR CLEANUP: Removing redundant cetamura/ modular structure..." -ForegroundColor Red
if (Test-Path "cetamura") {
    Write-Host "  ðŸ“ cetamura/ folder contains modular structure that duplicates src/main.py" -ForegroundColor Yellow
    Write-Host "  ðŸ—‘ï¸  Removing cetamura/ directory and all subdirectories..." -ForegroundColor Red
    Remove-Item -Recurse -Force "cetamura"
    git rm -r "cetamura" 2>$null
    Write-Host "  âœ… Removed redundant cetamura/ modular structure" -ForegroundColor Green
}

# Remove other redundant/generated items
$itemsToRemove = @(
    # Generated files and logs
    "*.csv",
    "*.log", 
    "*.spec",
    
    # Build artifacts and releases  
    "release",
    
    # Legacy and backup folders
    "legacy_backup",
    
    # Test data (can be regenerated)
    "test_data",
    
    # Redundant Python files
    "src/ipaddress.py",
    "origin_src_main.py",
    "create_test_environment.py"
)

Write-Host "`nðŸ—‘ï¸  Removing other redundant/generated files..." -ForegroundColor Yellow

Write-Host "`nðŸ—‘ï¸  Removing other redundant/generated files..." -ForegroundColor Yellow

# Remove files by pattern
foreach ($pattern in @("*.csv", "*.log", "*.spec")) {
    $files = Get-ChildItem -Path . -Name $pattern -File 2>$null
    foreach ($file in $files) {
        if (Test-Path $file) {
            Write-Host "  ðŸ—‘ï¸  $file" -ForegroundColor Red
            Remove-Item -Force $file
            git rm $file 2>$null
        }
    }
}

# Remove directories and specific files
$directoriesToRemove = @("release", "legacy_backup", "test_data")
$filesToRemove = @("src/ipaddress.py", "origin_src_main.py", "create_test_environment.py")

foreach ($dir in $directoriesToRemove) {
    if (Test-Path $dir) {
        Write-Host "  ðŸ“ Removing: $dir/" -ForegroundColor Red
        Remove-Item -Recurse -Force $dir
        git rm -r $dir 2>$null
    }
}

foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Write-Host "  ðŸ—‘ï¸  Removing: $file" -ForegroundColor Red
        Remove-Item -Force $file
        git rm $file 2>$null
    }
}

# Essential items that should be KEPT (verification)
$essentialItems = @(
    "src/main.py",
    "requirements.txt", 
    "requirements-dev.txt",
    "tests/",
    "dist_package/build_scripts/",
    "docs/",
    ".gitignore",
    "README.md",
    "pytest.ini"
)

Write-Host "`nðŸ” Verifying essential files still exist..." -ForegroundColor Blue
$allEssentialExist = $true
foreach ($item in $essentialItems) {
    if (Test-Path $item) {
        Write-Host "  âœ… $item" -ForegroundColor Green
    } else {
        Write-Host "  âŒ MISSING: $item" -ForegroundColor Red
        $allEssentialExist = $false
    }
}

if (-not $allEssentialExist) {
    Write-Host "`nâš ï¸  WARNING: Some essential files are missing!" -ForegroundColor Yellow
}

# Clean up build artifacts
Write-Host "`nðŸ§¹ Cleaning build artifacts..." -ForegroundColor Yellow

# Clean up build artifacts
Write-Host "`nðŸ§¹ Cleaning build artifacts..." -ForegroundColor Yellow

$buildDirs = @("build", "dist", "temp_release_test")
foreach ($dir in $buildDirs) {
    if (Test-Path $dir) {
        Write-Host "  ðŸ“ Removing build directory: $dir/" -ForegroundColor Red
        Remove-Item -Path $dir -Recurse -Force
    }
}

# Clean __pycache__ directories
$pycacheDirs = Get-ChildItem -Path "." -Filter "__pycache__" -Directory -Recurse
if ($pycacheDirs.Count -gt 0) {
    Write-Host "  ðŸ—‘ï¸  Removing $($pycacheDirs.Count) __pycache__ directories..." -ForegroundColor Red
    foreach ($dir in $pycacheDirs) {
        Remove-Item -Path $dir.FullName -Recurse -Force
    }
}

# Test that main application still works
Write-Host "`nðŸ”¬ Testing main application after cleanup..." -ForegroundColor Blue
$testResult = & "C:/Users/saa24b/Cetamura Batch Script/cetamura_python_script/.venv/Scripts/python.exe" -c "import src.main; print('âœ… Import successful after cleanup')" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host $testResult -ForegroundColor Green
} else {
    Write-Host "âŒ Import test failed: $testResult" -ForegroundColor Red
    Write-Host "âš ï¸  You may need to restore from backup branch: $backupBranch" -ForegroundColor Yellow
}

Write-Host "`nðŸ“Š Major Cleanup Summary:" -ForegroundColor Cyan
Write-Host "  âœ… Kept essential working components (src/main.py, tests/, docs/, etc.)" -ForegroundColor Green
Write-Host "  ðŸ—‘ï¸  REMOVED redundant cetamura/ modular structure" -ForegroundColor Red
Write-Host "  ðŸ§¹ Cleaned up generated files, logs, and build artifacts" -ForegroundColor Yellow
Write-Host "  ðŸ“¦ Created backup branch: $backupBranch" -ForegroundColor Blue

Write-Host "`nðŸŽ¯ Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review changes: git status" -ForegroundColor White
Write-Host "  2. Test application: python src/main.py" -ForegroundColor White
Write-Host "  3. Commit cleanup: git add -A && git commit -m 'cleanup: remove redundant modular structure, streamline to working src/main.py'" -ForegroundColor White
Write-Host "  4. If issues occur, restore: git checkout $backupBranch" -ForegroundColor White

Write-Host "`nâœ¨ Major cleanup complete! Project is now streamlined around working src/main.py" -ForegroundColor Green

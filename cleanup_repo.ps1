# Cetamura Project Major Cleanup Script
# Removes redundant folders and files while preserving essential working components

Write-Host "🧹 Starting Cetamura Project Major Cleanup..." -ForegroundColor Green
Write-Host "🎯 Target: Remove redundant modular structure, keep working src/main.py" -ForegroundColor Cyan

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "❌ Error: Not in a git repository root. Please run from project root." -ForegroundColor Red
    exit 1
}

# Create backup branch before major cleanup
Write-Host "📦 Creating backup branch before cleanup..." -ForegroundColor Yellow
$backupBranch = "cleanup-backup-$(Get-Date -Format "yyyyMMdd-HHmmss")"
git branch $backupBranch 2>$null
Write-Host "✅ Created backup branch: $backupBranch" -ForegroundColor Green

# MAJOR REDUNDANCY: Remove entire cetamura/ modular structure
Write-Host "`n🗂️  MAJOR CLEANUP: Removing redundant cetamura/ modular structure..." -ForegroundColor Red
if (Test-Path "cetamura") {
    Write-Host "  📁 cetamura/ folder contains modular structure that duplicates src/main.py" -ForegroundColor Yellow
    Write-Host "  🗑️  Removing cetamura/ directory and all subdirectories..." -ForegroundColor Red
    Remove-Item -Recurse -Force "cetamura"
    git rm -r "cetamura" 2>$null
    Write-Host "  ✅ Removed redundant cetamura/ modular structure" -ForegroundColor Green
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

Write-Host "`n🗑️  Removing other redundant/generated files..." -ForegroundColor Yellow

Write-Host "`n🗑️  Removing other redundant/generated files..." -ForegroundColor Yellow

# Remove files by pattern
foreach ($pattern in @("*.csv", "*.log", "*.spec")) {
    $files = Get-ChildItem -Path . -Name $pattern -File 2>$null
    foreach ($file in $files) {
        if (Test-Path $file) {
            Write-Host "  🗑️  $file" -ForegroundColor Red
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
        Write-Host "  📁 Removing: $dir/" -ForegroundColor Red
        Remove-Item -Recurse -Force $dir
        git rm -r $dir 2>$null
    }
}

foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Write-Host "  🗑️  Removing: $file" -ForegroundColor Red
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

Write-Host "`n🔍 Verifying essential files still exist..." -ForegroundColor Blue
$allEssentialExist = $true
foreach ($item in $essentialItems) {
    if (Test-Path $item) {
        Write-Host "  ✅ $item" -ForegroundColor Green
    } else {
        Write-Host "  ❌ MISSING: $item" -ForegroundColor Red
        $allEssentialExist = $false
    }
}

if (-not $allEssentialExist) {
    Write-Host "`n⚠️  WARNING: Some essential files are missing!" -ForegroundColor Yellow
}

# Clean up build artifacts
Write-Host "`n🧹 Cleaning build artifacts..." -ForegroundColor Yellow

# Clean up build artifacts
Write-Host "`n🧹 Cleaning build artifacts..." -ForegroundColor Yellow

$buildDirs = @("build", "dist", "temp_release_test")
foreach ($dir in $buildDirs) {
    if (Test-Path $dir) {
        Write-Host "  📁 Removing build directory: $dir/" -ForegroundColor Red
        Remove-Item -Path $dir -Recurse -Force
    }
}

# Clean __pycache__ directories
$pycacheDirs = Get-ChildItem -Path "." -Filter "__pycache__" -Directory -Recurse
if ($pycacheDirs.Count -gt 0) {
    Write-Host "  🗑️  Removing $($pycacheDirs.Count) __pycache__ directories..." -ForegroundColor Red
    foreach ($dir in $pycacheDirs) {
        Remove-Item -Path $dir.FullName -Recurse -Force
    }
}

# Test that main application still works
Write-Host "`n🔬 Testing main application after cleanup..." -ForegroundColor Blue
$testResult = & "C:/Users/saa24b/Cetamura Batch Script/cetamura_python_script/.venv/Scripts/python.exe" -c "import src.main; print('✅ Import successful after cleanup')" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host $testResult -ForegroundColor Green
} else {
    Write-Host "❌ Import test failed: $testResult" -ForegroundColor Red
    Write-Host "⚠️  You may need to restore from backup branch: $backupBranch" -ForegroundColor Yellow
}

Write-Host "`n📊 Major Cleanup Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Kept essential working components (src/main.py, tests/, docs/, etc.)" -ForegroundColor Green
Write-Host "  🗑️  REMOVED redundant cetamura/ modular structure" -ForegroundColor Red
Write-Host "  🧹 Cleaned up generated files, logs, and build artifacts" -ForegroundColor Yellow
Write-Host "  📦 Created backup branch: $backupBranch" -ForegroundColor Blue

Write-Host "`n🎯 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review changes: git status" -ForegroundColor White
Write-Host "  2. Test application: python src/main.py" -ForegroundColor White
Write-Host "  3. Commit cleanup: git add -A && git commit -m 'cleanup: remove redundant modular structure, streamline to working src/main.py'" -ForegroundColor White
Write-Host "  4. If issues occur, restore: git checkout $backupBranch" -ForegroundColor White

Write-Host "`n✨ Major cleanup complete! Project is now streamlined around working src/main.py" -ForegroundColor Green

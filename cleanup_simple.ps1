Write-Host "🧹 Cetamura Project Major Cleanup" -ForegroundColor Green

# Create backup branch
git branch "cleanup-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')" 2>$null

# Remove redundant cetamura folder
if (Test-Path "cetamura") {
    Write-Host "🗑️  Removing redundant cetamura/ folder..." -ForegroundColor Red
    Remove-Item -Recurse -Force "cetamura"
    git rm -r "cetamura" 2>$null
}

# Remove other redundant items
$items = @("release", "legacy_backup", "test_data")
foreach ($item in $items) {
    if (Test-Path $item) {
        Write-Host "🗑️  Removing $item..." -ForegroundColor Red
        Remove-Item -Recurse -Force $item
        git rm -r $item 2>$null
    }
}

# Remove generated files
Get-ChildItem -Name "*.csv" | ForEach-Object { 
    Remove-Item $_ -Force
    git rm $_ 2>$null
}
Get-ChildItem -Name "*.log" | ForEach-Object { 
    Remove-Item $_ -Force  
    git rm $_ 2>$null
}
Get-ChildItem -Name "*.spec" | ForEach-Object { 
    Remove-Item $_ -Force
    git rm $_ 2>$null
}

# Test import
Write-Host "🔬 Testing import..." -ForegroundColor Blue
& ".venv\Scripts\python.exe" -c "import src.main; print('✅ Success')"

Write-Host "✨ Cleanup complete!" -ForegroundColor Green
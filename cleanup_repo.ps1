# Repository cleanup script
Write-Host "Starting repository cleanup..." -ForegroundColor Green

# Remove redundant Python files
$redundantFiles = @(
    "src/ipaddress.py",
    "origin_src_main.py"
)

foreach ($file in $redundantFiles) {
    if (Test-Path $file) {
        Write-Host "Removing redundant file: $file" -ForegroundColor Yellow
        Remove-Item -Path $file -Force
    }
}

# Clean up log files that shouldn't be in version control
$logFiles = @(
    "batch_process_summary.log",
    "batch_tool.log"
)

foreach ($logFile in $logFiles) {
    if (Test-Path $logFile) {
        Write-Host "Removing log file: $logFile" -ForegroundColor Yellow
        Remove-Item -Path $logFile -Force
    }
}

# Check temp_release_test directory
if (Test-Path "temp_release_test") {
    Write-Host "The temp_release_test directory contains:" -ForegroundColor Yellow
    Get-ChildItem -Path "temp_release_test" -Recurse | Measure-Object -Property Length -Sum | 
        Select-Object @{Name="FileCount";Expression={$_.Count}}, @{Name="Size(MB)";Expression={"{0:N2}" -f ($_.Sum / 1MB)}}
    
    $response = Read-Host "Do you want to remove the temp_release_test directory? (y/n)"
    if ($response -eq "y") {
        Write-Host "Removing temp_release_test directory..." -ForegroundColor Yellow
        Remove-Item -Path "temp_release_test" -Recurse -Force
    }
}

# Check for PyInstaller build artifacts
$buildDirs = @(
    "build",
    "dist"
)

foreach ($dir in $buildDirs) {
    if (Test-Path $dir) {
        $dirInfo = Get-ChildItem -Path $dir -Recurse | Measure-Object -Property Length -Sum
        Write-Host "$dir directory contains $($dirInfo.Count) files, total size: $([math]::Round($dirInfo.Sum / 1MB, 2)) MB" -ForegroundColor Yellow
        
        $response = Read-Host "Do you want to clean the $dir directory? (y/n)"
        if ($response -eq "y") {
            Write-Host "Cleaning $dir directory..." -ForegroundColor Yellow
            Remove-Item -Path $dir -Recurse -Force
        }
    }
}

# Check for __pycache__ directories
$pycacheDirs = Get-ChildItem -Path "." -Filter "__pycache__" -Directory -Recurse
if ($pycacheDirs.Count -gt 0) {
    Write-Host "Found $($pycacheDirs.Count) __pycache__ directories" -ForegroundColor Yellow
    $response = Read-Host "Do you want to clean all __pycache__ directories? (y/n)"
    if ($response -eq "y") {
        Write-Host "Removing __pycache__ directories..." -ForegroundColor Yellow
        foreach ($dir in $pycacheDirs) {
            Remove-Item -Path $dir.FullName -Recurse -Force
        }
    }
}

Write-Host "Repository cleanup completed!" -ForegroundColor Green

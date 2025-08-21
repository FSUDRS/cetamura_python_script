#!/usr/bin/env powershell

# Complete Git Cleanup Script
# This script finishes removing test data from git tracking

Write-Host "=== Completing Git Repository Cleanup ===" -ForegroundColor Green

# Set location to project directory
Set-Location "C:\Users\saa24b\Cetamura Batch Script\cetamura_python_script"

# Check current git status
Write-Host "Checking git status..." -ForegroundColor Yellow
git status --short

# Commit any staged deletions
Write-Host "Committing staged test data removal..." -ForegroundColor Yellow
git commit -m "cleanup: Remove test data from production repository

REPOSITORY CLEANUP:
- Removed 572+ test files from git tracking
- Updated .gitignore to exclude test infrastructure  
- Test data remains available locally for development

REMOVED FROM GIT:
- test_data/ directory (8 test scenarios)
- Test documentation files
- Test generation scripts

RESULT: Production repository is now lightweight and focused."

# Push changes
Write-Host "Pushing changes to remote..." -ForegroundColor Yellow
git push origin main

# Final status check
Write-Host "Final git status:" -ForegroundColor Green
git status

Write-Host "=== Cleanup Complete ===" -ForegroundColor Green
Write-Host "Repository should now show significantly fewer tracked files." -ForegroundColor Cyan

# Optional: Show file count
Write-Host "Current tracked file count:" -ForegroundColor Yellow
git ls-files | Measure-Object | Select-Object Count

pause

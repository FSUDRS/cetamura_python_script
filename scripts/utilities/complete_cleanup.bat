@echo off
REM Complete Git Cleanup - Batch Version
echo === Git Repository Cleanup Script ===

cd /d "C:\Users\saa24b\Cetamura Batch Script\cetamura_python_script"

echo Current directory: %CD%

echo Checking git status...
git status --short

echo Committing staged deletions...
git commit -m "cleanup: Remove test data from production repository - Staged deletions of 572+ test files - Updated .gitignore to exclude test infrastructure"

echo Pushing to remote...
git push origin main

echo Final status check...
git status

echo Counting tracked files...
git ls-files > temp_file_list.txt
for /f %%i in ('type temp_file_list.txt ^| find /c /v ""') do echo Tracked files: %%i
del temp_file_list.txt

echo === Cleanup Complete ===
pause

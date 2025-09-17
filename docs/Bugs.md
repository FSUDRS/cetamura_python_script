# Known Issues

## Current Bugs

### GUI Issues
- **Missing icon/logo warnings**: App works fine, just shows warnings in console
- **Widget None errors**: Fixed in latest version

### Processing Issues  
- **Large batch timeouts**: Very large folders (1000+ photos) may take a long time
- **Memory usage**: High memory usage with many large images
- **Path length limits**: Windows long path issues with deep folder structures

### File Handling
- **Permission errors**: Need write access to output folders
- **Network drives**: May be slow, copy to local drive first
- **Locked files**: Can't process files opened in other programs

## Workarounds

### For Large Batches
- Process in smaller chunks
- Close other programs to free memory
- Use staging mode first to test

### For Path Issues
- Keep folder names short
- Avoid deep nested folders
- Move data closer to drive root if needed

### For Permission Problems
- Run as administrator if needed
- Check folder permissions
- Ensure output folder isn't read-only

## Fixed Issues
- ✅ CSV writer None errors (v2025.09.17)
- ✅ Orientation correction failures (v2025.09.16)  
- ✅ Duplicate processing (v2025.09.15)
- ✅ GUI freezing during processing (v2025.09.14)

## Reporting New Bugs
Include this info:
- What you were doing
- Error message (full text)
- Input folder structure
- Windows version
- Log file if available
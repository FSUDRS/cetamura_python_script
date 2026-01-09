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
- **'tuple' object has no attribute 'iid' error** (v2025.10.03)
  - Root cause: `batch_process_with_safety_nets` was calling `find_photo_sets()` which returns plain tuples instead of `find_photo_sets_enhanced()` which returns PhotoSet NamedTuples
  - Fix: Changed line 1011 to call `find_photo_sets_enhanced()` directly, ensuring PhotoSet objects with named attributes (base_directory, jpg_files, xml_files, manifest_file, structure_type) are used throughout batch processing


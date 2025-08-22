#!/usr/bin/env python3
"""
Test directory structure analysis
"""

import sys
from pathlib import Path

def analyze_structure(base_path):
    """Analyze the directory structure"""
    
    print(f"🔍 Analyzing structure: {base_path}")
    print("=" * 50)
    
    path = Path(base_path)
    if not path.exists():
        print(f"❌ Path does not exist: {path}")
        return
    
    print("📁 Directory traversal simulation:")
    print()
    
    # Simulate what the batch processing code does
    level1_count = 0
    level2_count = 0
    
    for year_dir in path.iterdir():
        if not year_dir.is_dir():
            continue
            
        level1_count += 1
        print(f"Level 1 (year_dir): {year_dir.name}")
        
        for subfolder in year_dir.iterdir():
            if not subfolder.is_dir():
                continue
                
            level2_count += 1
            print(f"  Level 2 (subfolder): {subfolder.name}")
            print(f"  Full path: {subfolder}")
            
            # Check what files exist at this level
            ini_files = list(subfolder.glob("*.ini"))
            xml_files = list(subfolder.glob("*.xml"))
            jpg_files = list(subfolder.glob("*.jpg"))
            
            print(f"    📋 .ini files: {len(ini_files)} {[f.name for f in ini_files]}")
            print(f"    📄 .xml files: {len(xml_files)}")
            print(f"    🖼️ .jpg files: {len(jpg_files)}")
            
            if len(ini_files) == 0:
                print(f"    🚨 MANIFEST_ERROR: No MANIFEST.ini found for photo set")
            
            # Check if there are subdirectories that might contain the actual files
            subdirs = [d for d in subfolder.iterdir() if d.is_dir()]
            if subdirs:
                print(f"    📁 Subdirectories: {[d.name for d in subdirs]}")
                for subdir in subdirs:
                    sub_ini = list(subdir.glob("*.ini"))
                    sub_xml = list(subdir.glob("*.xml"))
                    sub_jpg = list(subdir.glob("*.jpg"))
                    if sub_ini or sub_xml or sub_jpg:
                        print(f"      🔍 {subdir.name}: ini={len(sub_ini)}, xml={len(sub_xml)}, jpg={len(sub_jpg)}")
            
            print()
    
    print(f"📊 Summary:")
    print(f"  Level 1 directories: {level1_count}")
    print(f"  Level 2 directories: {level2_count}")

if __name__ == "__main__":
    # Test with your actual structure format
    test_structures = [
        # Simulated structure based on your data
        "X:/Cetamura",  # This won't work, but shows the concept
        # Local test structure
        "test_data/scenario_1_standard",
    ]
    
    for structure in test_structures:
        if Path(structure).exists():
            analyze_structure(structure)
            print()

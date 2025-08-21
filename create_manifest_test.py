#!/usr/bin/env python3
"""
Create a test case that matches the user's issue - directories without MANIFEST.ini files
"""

import os
import shutil
from pathlib import Path

def create_manifest_missing_scenario():
    """Create test directories that match the user's issue"""
    
    base_path = Path("test_data/manifest_missing_test")
    
    # Clean up if exists
    if base_path.exists():
        shutil.rmtree(base_path)
        
    # Create directory structure matching user's data
    test_dirs = [
        base_path / "1991-07-01" / "15N-21W",
        base_path / "1991-07-01" / "15N-30W", 
        base_path / "1991-07-01" / "18N-24W"
    ]
    
    for test_dir in test_dirs:
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample XML and JPG files but NO MANIFEST.ini
        for i in range(1, 3):
            xml_file = test_dir / f"metadata_{i}.xml"
            jpg_file = test_dir / f"photo_{i}.jpg"
            
            # Create sample XML content
            xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
    <mods:identifier type="IID">TEST_{test_dir.name}_{i:02d}</mods:identifier>
    <mods:titleInfo>
        <mods:title>Test Photo {i}</mods:title>
    </mods:titleInfo>
</mods:mods>'''
            xml_file.write_text(xml_content)
            
            # Create sample JPG (just a small placeholder file)
            jpg_file.write_bytes(b'fake_jpg_content')
            
    print(f"✅ Created test scenario at: {base_path}")
    print("📁 Directory structure:")
    for test_dir in test_dirs:
        print(f"   {test_dir}")
        files = list(test_dir.iterdir())
        for file in files:
            print(f"      {file.name}")
        print(f"      ❌ NO MANIFEST.ini (this should cause validation errors)")
        print()
        
    return base_path

if __name__ == "__main__":
    create_manifest_missing_scenario()

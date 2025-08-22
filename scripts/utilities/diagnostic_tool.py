#!/usr/bin/env python3
"""
Diagnostic script to understand the dry run vs staging discrepancy
"""

import os
import sys
from pathlib import Path
import csv

def analyze_csv_reports():
    """Analyze existing CSV reports to understand the discrepancy"""
    
    print("🔍 CSV Report Analysis")
    print("=" * 50)
    
    # Look for recent CSV files
    csv_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.csv') and 'batch_report' in file:
                csv_files.append(Path(root) / file)
    
    # Sort by modification time (newest first)
    csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"Found {len(csv_files)} CSV report files:")
    print()
    
    for i, csv_file in enumerate(csv_files[:10]):  # Show last 10
        print(f"{i+1}. {csv_file}")
        print(f"   Modified: {csv_file.stat().st_mtime}")
        
        # Read and analyze the CSV
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
            if not rows:
                print("   📄 Empty file")
                continue
                
            # Find summary row
            summary_row = None
            manifest_errors = 0
            total_errors = 0
            
            for row in rows:
                if len(row) >= 4:
                    if row[0] == 'SUMMARY':
                        summary_row = row
                    elif row[3] == 'MANIFEST_ERROR':
                        manifest_errors += 1
                    elif 'ERROR' in row[3]:
                        total_errors += 1
            
            if summary_row:
                print(f"   📊 {' | '.join(summary_row)}")
            
            print(f"   📋 Manifest Errors: {manifest_errors}")
            print(f"   ❌ Total Errors: {total_errors}")
            
            # Check for dry run indicator
            dry_run_mentioned = any('dry run' in ' '.join(row).lower() for row in rows)
            staging_mentioned = any('staging' in ' '.join(row).lower() for row in rows)
            
            if dry_run_mentioned:
                print("   🔍 DRY RUN detected")
            elif staging_mentioned:
                print("   📋 STAGING detected")
            else:
                print("   ⚡ PRODUCTION mode")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
            
        print()

def check_directory_structure(path_str):
    """Check what directories and files exist"""
    
    print(f"📁 Directory Analysis: {path_str}")
    print("=" * 50)
    
    try:
        base_path = Path(path_str)
        if not base_path.exists():
            print(f"❌ Path does not exist: {base_path}")
            return
            
        # Walk through structure
        for year_dir in base_path.iterdir():
            if not year_dir.is_dir():
                continue
                
            print(f"📅 {year_dir.name}/")
            
            for subfolder in year_dir.iterdir():
                if not subfolder.is_dir():
                    continue
                    
                print(f"   📁 {subfolder.name}/")
                
                # Check for manifest files
                manifest_files = list(subfolder.glob("*.ini"))
                xml_files = list(subfolder.glob("*.xml"))
                jpg_files = list(subfolder.glob("*.jpg"))
                
                print(f"      📋 Manifest files: {len(manifest_files)} {[f.name for f in manifest_files]}")
                print(f"      📄 XML files: {len(xml_files)}")
                print(f"      🖼️ JPG files: {len(jpg_files)}")
                
                if len(manifest_files) == 0:
                    print("      🚨 NO MANIFEST.ini FOUND - This should cause MANIFEST_ERROR")
                elif len(manifest_files) > 1:
                    print("      🚨 MULTIPLE MANIFEST FILES - This should cause MANIFEST_ERROR")
                else:
                    print("      ✅ Single manifest file found")
                    
                print()
    
    except Exception as e:
        print(f"❌ Error analyzing directory: {e}")

if __name__ == "__main__":
    print("🔧 Cetamura Batch Tool - Validation Discrepancy Diagnostic")
    print("=" * 60)
    print()
    
    # Analyze CSV reports
    analyze_csv_reports()
    print()
    
    # Check specific directory if provided
    if len(sys.argv) > 1:
        check_directory_structure(sys.argv[1])
    else:
        # Check test data
        test_paths = [
            "test_data/scenario_1_standard",
            "test_data/manifest_missing_test"
        ]
        
        for test_path in test_paths:
            if Path(test_path).exists():
                check_directory_structure(test_path)
                print()

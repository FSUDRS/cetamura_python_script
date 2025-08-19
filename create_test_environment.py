#!/usr/bin/env python3
"""
Test Environment Generator for Cetamura Batch Ingest Tool
Creates various folder structures and test scenarios
"""

import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
import configparser
import random
import string

class TestEnvironmentBuilder:
    def __init__(self, base_path: str = "test_data"):
        self.base_path = Path(base_path)
        self.test_scenarios = []
        
    def clean_environment(self):
        """Remove existing test environment"""
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
        print(f"Cleaned test environment: {self.base_path}")
    
    def create_test_image(self, path: Path, size: tuple = (800, 600), format: str = "JPEG"):
        """Create a test image file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new('RGB', size, color=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
        img.save(path, format)
        
    def create_test_xml(self, path: Path, iid: str, with_namespace: bool = True):
        """Create a test XML metadata file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if with_namespace:
            root = ET.Element("mods:mods")
            root.set("xmlns:mods", "http://www.loc.gov/mods/v3")
            identifier = ET.SubElement(root, "mods:identifier")
            identifier.set("type", "IID")
            identifier.text = iid
        else:
            root = ET.Element("metadata")
            identifier = ET.SubElement(root, "identifier")
            identifier.set("type", "IID")
            identifier.text = iid
        
        tree = ET.ElementTree(root)
        tree.write(path, encoding='utf-8', xml_declaration=True)
    
    def create_manifest(self, path: Path, collection: str = "2006", trench: str = "46N-3W"):
        """Create a MANIFEST.ini file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        config = configparser.ConfigParser()
        config['package'] = {
            'submitter_email': 'test@fsu.edu',
            'content_model': 'test_model',
            'parent_collection': 'test_collection'
        }
        
        with open(path, 'w') as f:
            config.write(f)

    def create_standard_structure(self):
        """Test Case 1: Standard flat structure"""
        scenario_path = self.base_path / "scenario_1_standard"
        
        # Create 2006/46N-3W structure
        year_path = scenario_path / "2006" / "46N-3W"
        
        # Create 5 image/xml pairs
        for i in range(1, 6):
            iid = f"FSU_Cetamura_photos_20060523_46N3W_00{i}"
            self.create_test_image(year_path / f"photo_{i}.jpg")
            self.create_test_xml(year_path / f"metadata_{i}.xml", iid)
        
        self.create_manifest(year_path / "MANIFEST.ini")
        
        self.test_scenarios.append({
            "name": "Standard Structure",
            "path": scenario_path,
            "expected_sets": 1,
            "expected_files": 5
        })
        print(f"Created standard structure test: {scenario_path}")

    def create_hierarchical_structure(self):
        """Test Case 2: Hierarchical structure"""
        scenario_path = self.base_path / "scenario_2_hierarchical"
        
        # MANIFEST.ini at year level
        year_path = scenario_path / "2007"
        self.create_manifest(year_path / "MANIFEST.ini")
        
        # Multiple trench subdirectories
        trenches = ["46N-3W", "47N-2W", "48N-1W"]
        for trench in trenches:
            trench_path = year_path / trench
            for i in range(1, 4):
                iid = f"FSU_Cetamura_photos_20070615_{trench.replace('-', '')}_00{i}"
                self.create_test_image(trench_path / f"image_{i}.jpg")
                self.create_test_xml(trench_path / f"meta_{i}.xml", iid)
        
        self.test_scenarios.append({
            "name": "Hierarchical Structure",
            "path": scenario_path,
            "expected_sets": 3,
            "expected_files": 9
        })
        print(f"Created hierarchical structure test: {scenario_path}")

    def create_mixed_structure(self):
        """Test Case 3: Mixed structures"""
        scenario_path = self.base_path / "scenario_3_mixed"
        
        # Standard structure in 2005
        std_path = scenario_path / "2005" / "45N-4W"
        for i in range(1, 3):
            iid = f"FSU_Cetamura_photos_20050810_45N4W_00{i}"
            self.create_test_image(std_path / f"pic_{i}.jpg")
            self.create_test_xml(std_path / f"data_{i}.xml", iid)
        self.create_manifest(std_path / "MANIFEST.ini")
        
        # Hierarchical structure in 2008
        hier_year = scenario_path / "2008"
        self.create_manifest(hier_year / "MANIFEST.ini")
        
        for trench in ["50N-1E", "51N-2E"]:
            trench_path = hier_year / trench
            for i in range(1, 3):
                iid = f"FSU_Cetamura_photos_20080720_{trench.replace('-', '').replace('N', 'N')}_00{i}"
                self.create_test_image(trench_path / f"shot_{i}.jpg")
                self.create_test_xml(trench_path / f"record_{i}.xml", iid)
        
        self.test_scenarios.append({
            "name": "Mixed Structures",
            "path": scenario_path,
            "expected_sets": 3,
            "expected_files": 6
        })
        print(f"Created mixed structure test: {scenario_path}")

    def create_edge_cases(self):
        """Test Case 4: Edge cases and error scenarios"""
        scenario_path = self.base_path / "scenario_4_edge_cases"
        
        # Missing XML files
        missing_xml_path = scenario_path / "2009" / "missing_xml"
        self.create_test_image(missing_xml_path / "orphan.jpg")
        self.create_manifest(missing_xml_path / "MANIFEST.ini")
        
        # Missing JPG files
        missing_jpg_path = scenario_path / "2009" / "missing_jpg"
        self.create_test_xml(missing_jpg_path / "orphan.xml", "FSU_Cetamura_photos_20090101_TEST_001")
        self.create_manifest(missing_jpg_path / "MANIFEST.ini")
        
        # Invalid XML (no IID)
        invalid_xml_path = scenario_path / "2009" / "invalid_xml"
        self.create_test_image(invalid_xml_path / "test.jpg")
        # Create XML without IID
        xml_path = invalid_xml_path / "test.xml"
        xml_path.parent.mkdir(parents=True, exist_ok=True)
        root = ET.Element("metadata")
        ET.SubElement(root, "title").text = "No IID here"
        tree = ET.ElementTree(root)
        tree.write(xml_path)
        self.create_manifest(invalid_xml_path / "MANIFEST.ini")
        
        # Special characters in filenames
        special_path = scenario_path / "2009" / "special_chars"
        iid = "FSU_Cetamura_photos_20090615_SPECIAL_001"
        self.create_test_image(special_path / "file with spaces & symbols!.jpg")
        self.create_test_xml(special_path / "metadata-file_name.xml", iid)
        self.create_manifest(special_path / "MANIFEST.ini")
        
        self.test_scenarios.append({
            "name": "Edge Cases",
            "path": scenario_path,
            "expected_sets": 1,  # Only the special chars should work
            "expected_files": 1
        })
        print(f"Created edge cases test: {scenario_path}")

    def create_large_scale_test(self):
        """Test Case 5: Large scale test"""
        scenario_path = self.base_path / "scenario_5_large_scale"
        
        # Create multiple years with multiple trenches
        years = ["2010", "2011", "2012"]
        for year in years:
            year_path = scenario_path / year
            self.create_manifest(year_path / "MANIFEST.ini")
            
            # 5 trenches per year, 10 files per trench
            for t in range(1, 6):
                trench = f"5{t}N-{t}W"
                trench_path = year_path / trench
                
                for i in range(1, 11):
                    iid = f"FSU_Cetamura_photos_{year}0801_{trench.replace('-', '')}_0{i:02d}"
                    self.create_test_image(trench_path / f"image_{i:03d}.jpg")
                    self.create_test_xml(trench_path / f"meta_{i:03d}.xml", iid)
        
        self.test_scenarios.append({
            "name": "Large Scale Test",
            "path": scenario_path,
            "expected_sets": 15,  # 3 years × 5 trenches
            "expected_files": 150  # 15 sets × 10 files
        })
        print(f"Created large scale test: {scenario_path}")

    def create_deep_nested_structure(self):
        """Test Case 6: Deep nested directories"""
        scenario_path = self.base_path / "scenario_6_deep_nested"
        
        # Create deeply nested structure
        deep_path = scenario_path / "2013" / "excavation" / "area_a" / "sector_1" / "46N-3W"
        
        for i in range(1, 4):
            iid = f"FSU_Cetamura_photos_20130901_46N3W_00{i}"
            self.create_test_image(deep_path / f"deep_{i}.jpg")
            self.create_test_xml(deep_path / f"deep_{i}.xml", iid)
        
        # Place manifest at different levels to test hierarchical detection
        self.create_manifest(scenario_path / "2013" / "excavation" / "MANIFEST.ini")
        
        self.test_scenarios.append({
            "name": "Deep Nested Structure",
            "path": scenario_path,
            "expected_sets": 1,
            "expected_files": 3
        })
        print(f"Created deep nested structure test: {scenario_path}")

    def create_corrupted_files_test(self):
        """Test Case 7: Corrupted files"""
        scenario_path = self.base_path / "scenario_7_corrupted"
        
        test_path = scenario_path / "2014" / "corrupted_test"
        
        # Create normal files
        for i in range(1, 3):
            iid = f"FSU_Cetamura_photos_20140701_CORRUPT_00{i}"
            self.create_test_image(test_path / f"normal_{i}.jpg")
            self.create_test_xml(test_path / f"normal_{i}.xml", iid)
        
        # Create a "corrupted" file (empty file)
        corrupted_file = test_path / "corrupted.jpg"
        corrupted_file.parent.mkdir(parents=True, exist_ok=True)
        corrupted_file.write_bytes(b"Not a real image")
        
        self.create_test_xml(test_path / "corrupted.xml", "FSU_Cetamura_photos_20140701_CORRUPT_003")
        self.create_manifest(test_path / "MANIFEST.ini")
        
        self.test_scenarios.append({
            "name": "Corrupted Files Test",
            "path": scenario_path,
            "expected_sets": 1,
            "expected_files": 2  # Only normal files should process
        })
        print(f"Created corrupted files test: {scenario_path}")

    def create_performance_test(self):
        """Test Case 8: Performance benchmark test"""
        scenario_path = self.base_path / "scenario_8_performance"
        
        # Create a single large photo set
        year_path = scenario_path / "2015"
        self.create_manifest(year_path / "MANIFEST.ini")
        
        # Single trench with many files
        trench_path = year_path / "PERF-TEST"
        
        print("Creating performance test files (this may take a moment)...")
        for i in range(1, 101):  # 100 files
            iid = f"FSU_Cetamura_photos_20150901_PERFTEST_{i:03d}"
            self.create_test_image(trench_path / f"perf_{i:03d}.jpg", size=(400, 300))
            self.create_test_xml(trench_path / f"perf_{i:03d}.xml", iid)
        
        self.test_scenarios.append({
            "name": "Performance Test",
            "path": scenario_path,
            "expected_sets": 1,
            "expected_files": 100
        })
        print(f"Created performance test: {scenario_path}")

    def build_all_scenarios(self):
        """Build complete test environment"""
        print("Building comprehensive test environment...")
        self.clean_environment()
        
        self.create_standard_structure()
        self.create_hierarchical_structure()
        self.create_mixed_structure()
        self.create_edge_cases()
        self.create_large_scale_test()
        self.create_deep_nested_structure()
        self.create_corrupted_files_test()
        self.create_performance_test()
        
        print(f"\nTest environment created successfully!")
        print(f"Base path: {self.base_path.absolute()}")
        print(f"Total scenarios: {len(self.test_scenarios)}")
        
        return self.test_scenarios

    def print_scenario_summary(self):
        """Print summary of all test scenarios"""
        print("\n" + "="*60)
        print("TEST SCENARIO SUMMARY")
        print("="*60)
        
        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"{i}. {scenario['name']}")
            print(f"   Path: {scenario['path']}")
            print(f"   Expected Sets: {scenario['expected_sets']}")
            print(f"   Expected Files: {scenario['expected_files']}")
            print()

if __name__ == "__main__":
    builder = TestEnvironmentBuilder()
    scenarios = builder.build_all_scenarios()
    builder.print_scenario_summary()

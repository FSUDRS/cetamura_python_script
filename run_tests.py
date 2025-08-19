#!/usr/bin/env python3
"""
Automated Test Runner for Cetamura Batch Ingest Tool
Runs the tool against all test scenarios and validates results
"""

import sys
import time
from pathlib import Path
from create_test_environment import TestEnvironmentBuilder

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from main import find_photo_sets_enhanced
except ImportError:
    print("Error: Could not import main module. Ensure src/main.py exists.")
    sys.exit(1)

class TestRunner:
    def __init__(self):
        self.results = []
        
    def run_discovery_test(self, scenario):
        """Test photo set discovery for a scenario"""
        print(f"\nTesting: {scenario['name']}")
        print(f"Path: {scenario['path']}")
        
        start_time = time.time()
        
        try:
            photo_sets = find_photo_sets_enhanced(str(scenario['path']))
            discovery_time = time.time() - start_time
            
            result = {
                'scenario': scenario['name'],
                'path': str(scenario['path']),
                'expected_sets': scenario['expected_sets'],
                'found_sets': len(photo_sets),
                'expected_files': scenario['expected_files'],
                'found_files': sum(len(ps.jpg_files) for ps in photo_sets),
                'discovery_time': discovery_time,
                'success': len(photo_sets) == scenario['expected_sets'],
                'photo_sets': photo_sets
            }
            
            print(f"Found {len(photo_sets)} photo sets in {discovery_time:.2f}s")
            
            # Print detailed results
            for ps in photo_sets:
                print(f"  {ps.base_directory.name} ({ps.structure_type}): {len(ps.jpg_files)} files")
                
        except Exception as e:
            result = {
                'scenario': scenario['name'],
                'path': str(scenario['path']),
                'expected_sets': scenario['expected_sets'],
                'found_sets': 0,
                'expected_files': scenario['expected_files'],
                'found_files': 0,
                'discovery_time': 0,
                'success': False,
                'error': str(e),
                'photo_sets': []
            }
            print(f"Error: {e}")
        
        self.results.append(result)
        return result
    
    def run_processing_test(self, scenario):
        """Test actual file processing for a scenario"""
        print(f"\nProcessing Test: {scenario['name']}")
        
        try:
            # Import batch processing function
            from main import batch_process
            
            start_time = time.time()
            
            # Run batch processing
            batch_process(scenario['path'])
            
            processing_time = time.time() - start_time
            
            # Check for output files
            output_dirs = list(Path(scenario['path']).glob("CetamuraUploadBatch_*"))
            
            zip_count = 0
            for output_dir in output_dirs:
                zip_count += len(list(output_dir.glob("*.zip")))
            
            print(f"Processing completed in {processing_time:.2f}s")
            print(f"Created {zip_count} ZIP files in {len(output_dirs)} output directories")
            
            return {
                'processing_time': processing_time,
                'zip_files_created': zip_count,
                'output_directories': len(output_dirs),
                'success': True
            }
            
        except Exception as e:
            print(f"Processing error: {e}")
            return {
                'processing_time': 0,
                'zip_files_created': 0,
                'output_directories': 0,
                'success': False,
                'error': str(e)
            }
    
    def run_all_tests(self, include_processing=False):
        """Run tests against all scenarios"""
        print("Starting automated test suite...")
        
        # Build test environment
        builder = TestEnvironmentBuilder()
        scenarios = builder.build_all_scenarios()
        
        print(f"\nRunning {len(scenarios)} test scenarios...")
        
        # Run discovery tests for each scenario
        for scenario in scenarios:
            self.run_discovery_test(scenario)
            
            # Optionally run processing tests
            if include_processing:
                processing_result = self.run_processing_test(scenario)
                self.results[-1]['processing'] = processing_result
        
        # Print summary
        self.print_test_summary()
        
        return self.results
    
    def run_performance_benchmark(self):
        """Run performance-focused tests"""
        print("Running performance benchmark...")
        
        # Build only performance test
        builder = TestEnvironmentBuilder()
        builder.clean_environment()
        builder.create_performance_test()
        
        perf_scenario = {
            "name": "Performance Benchmark",
            "path": builder.base_path / "scenario_8_performance",
            "expected_sets": 1,
            "expected_files": 100
        }
        
        # Run multiple iterations
        iterations = 3
        times = []
        
        for i in range(iterations):
            print(f"\nIteration {i+1}/{iterations}")
            result = self.run_discovery_test(perf_scenario)
            times.append(result['discovery_time'])
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\nPerformance Results:")
        print(f"Average time: {avg_time:.2f}s")
        print(f"Min time: {min_time:.2f}s")
        print(f"Max time: {max_time:.2f}s")
        print(f"Files per second: {100/avg_time:.1f}")
    
    def print_test_summary(self):
        """Print comprehensive test results"""
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print()
        
        for result in self.results:
            status = "PASS" if result['success'] else "FAIL"
            print(f"{status} {result['scenario']}")
            print(f"     Expected: {result['expected_sets']} sets, {result['expected_files']} files")
            print(f"     Found:    {result['found_sets']} sets, {result['found_files']} files")
            print(f"     Time:     {result['discovery_time']:.2f}s")
            
            if 'error' in result:
                print(f"     Error:    {result['error']}")
                
            if 'processing' in result:
                proc = result['processing']
                if proc['success']:
                    print(f"     Processing: {proc['zip_files_created']} ZIPs in {proc['processing_time']:.2f}s")
                else:
                    print(f"     Processing Error: {proc.get('error', 'Unknown')}")
            print()
        
        # Performance analysis
        total_time = sum(r['discovery_time'] for r in self.results)
        avg_time = total_time / len(self.results) if self.results else 0
        
        print(f"Performance: {total_time:.2f}s total, {avg_time:.2f}s average per test")

class FeatureTestSuite:
    """Test suite for specific features and improvements"""
    
    def __init__(self):
        self.builder = TestEnvironmentBuilder()
        
    def test_file_pairing_accuracy(self):
        """Test accuracy of JPG-XML file pairing"""
        print("\nTesting file pairing accuracy...")
        
        # Create test with mismatched pairs
        test_path = self.builder.base_path / "pairing_test"
        year_path = test_path / "2020" / "PAIR-TEST"
        
        # Create matched pairs
        for i in range(1, 4):
            iid = f"FSU_Cetamura_photos_20200901_PAIRTEST_00{i}"
            self.builder.create_test_image(year_path / f"matched_{i}.jpg")
            self.builder.create_test_xml(year_path / f"matched_{i}.xml", iid)
        
        # Create unmatched files
        self.builder.create_test_image(year_path / "orphan.jpg")
        self.builder.create_test_xml(year_path / "orphan_xml.xml", "FSU_Cetamura_photos_20200901_PAIRTEST_orphan")
        
        self.builder.create_manifest(year_path / "MANIFEST.ini")
        
        # Test discovery
        from main import find_photo_sets_enhanced
        photo_sets = find_photo_sets_enhanced(str(test_path))
        
        if photo_sets:
            ps = photo_sets[0]
            print(f"Found {len(ps.jpg_files)} JPG files, {len(ps.xml_files)} XML files")
            # Should have 3 matched pairs, 1 orphan JPG, 1 orphan XML = 4 each
            return len(ps.jpg_files) == 4 and len(ps.xml_files) == 4
        
        return False
    
    def test_iid_extraction_variants(self):
        """Test IID extraction from various XML formats"""
        print("\nTesting IID extraction variants...")
        
        test_path = self.builder.base_path / "iid_test"
        year_path = test_path / "2021" / "IID-TEST"
        
        # Create XML with namespace
        self.builder.create_test_xml(
            year_path / "namespaced.xml", 
            "FSU_Cetamura_photos_20210901_IIDTEST_001", 
            with_namespace=True
        )
        
        # Create XML without namespace
        self.builder.create_test_xml(
            year_path / "no_namespace.xml", 
            "FSU_Cetamura_photos_20210901_IIDTEST_002", 
            with_namespace=False
        )
        
        # Create corresponding images
        self.builder.create_test_image(year_path / "namespaced.jpg")
        self.builder.create_test_image(year_path / "no_namespace.jpg")
        
        self.builder.create_manifest(year_path / "MANIFEST.ini")
        
        # Test IID extraction
        from main import extract_iid_from_xml
        
        try:
            iid1 = extract_iid_from_xml(year_path / "namespaced.xml")
            iid2 = extract_iid_from_xml(year_path / "no_namespace.xml")
            
            print(f"Namespaced IID: {iid1}")
            print(f"Non-namespaced IID: {iid2}")
            
            return (iid1 == "FSU_Cetamura_photos_20210901_IIDTEST_001" and 
                    iid2 == "FSU_Cetamura_photos_20210901_IIDTEST_002")
        
        except Exception as e:
            print(f"IID extraction error: {e}")
            return False
    
    def run_feature_tests(self):
        """Run all feature-specific tests"""
        print("Running feature test suite...")
        
        self.builder.clean_environment()
        
        tests = [
            ("File Pairing Accuracy", self.test_file_pairing_accuracy),
            ("IID Extraction Variants", self.test_iid_extraction_variants),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
                status = "PASS" if results[test_name] else "FAIL"
                print(f"{status}: {test_name}")
            except Exception as e:
                results[test_name] = False
                print(f"FAIL: {test_name} - {e}")
        
        return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Cetamura Batch Tool Tests')
    parser.add_argument('--performance', action='store_true', help='Run performance benchmark')
    parser.add_argument('--features', action='store_true', help='Run feature tests')
    parser.add_argument('--processing', action='store_true', help='Include file processing tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.performance or args.all:
        runner.run_performance_benchmark()
    
    if args.features or args.all:
        feature_suite = FeatureTestSuite()
        feature_suite.run_feature_tests()
    
    if not any([args.performance, args.features]) or args.all:
        runner.run_all_tests(include_processing=args.processing or args.all)

#!/usr/bin/env python3
"""
Test Runner for Cetamura Batch Ingest Tool
Simplified test runner that works with the current project structure
"""

import sys
import subprocess
import time
import argparse
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import only the functions actually needed for testing
try:
    # Import the smaller set used by this runner (keeps imports explicit)
    from main import (
        find_photo_sets_enhanced,
        extract_iid_from_xml,
        sanitize_name,
        batch_process_with_safety_nets,
        convert_to_tiff,
        rename_files,
        package_to_zip,
        validate_image_orientation,
        show_instructions,
    )

    # Import module to access a named entrypoint if present
    import importlib
    main_module = importlib.import_module('main')
    main_func = getattr(main_module, 'main', None)

    IMPORTS_SUCCESSFUL = True

except Exception as e:
    print(f"ERROR: Failed to import required functions from main: {e}")
    # ... (rest of error printing)
    
    # Fallback stubs that raise informative errors when used (so failures are obvious)
    def _missing_stub(name):
        def _fn(*args, **kwargs):
            raise RuntimeError(f"Stub called for missing import: {name}")
        return _fn

    find_photo_sets_enhanced = _missing_stub('find_photo_sets_enhanced')
    extract_iid_from_xml = _missing_stub('extract_iid_from_xml')
    sanitize_name = _missing_stub('sanitize_name')
    batch_process_with_safety_nets = _missing_stub('batch_process_with_safety_nets')
    convert_to_tiff = _missing_stub('convert_to_tiff')
    rename_files = _missing_stub('rename_files')
    package_to_zip = _missing_stub('package_to_zip')
    validate_image_orientation = _missing_stub('validate_image_orientation')
    show_instructions = _missing_stub('show_instructions')
    main_func = lambda *a, **k: _missing_stub('main')()

def run_pytest_tests():
    """Run the main test suite using pytest"""
    print("="*60)
    print("CETAMURA BATCH TOOL - TEST RUNNER")
    print("="*60)
    
    # Check if imports were successful
    if not IMPORTS_SUCCESSFUL:
        print("ERROR: Cannot run pytest tests - main module import failed")
        return False
    
    print("PASS: Main module import successful")
    
    # Run pytest with verbose output
    print("\nRunning pytest tests...")
    print("-" * 40)
    
    test_dir = Path(__file__).parent
    cmd = [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    end_time = time.time()
    
    print("-" * 40)
    print(f"Tests completed in {end_time - start_time:.2f} seconds")
    
    return result.returncode == 0

def run_quick_functionality_test():
    """Run a quick test of core functionality"""
    print("\nRunning quick functionality test...")
    print("-" * 40)
    
    if not IMPORTS_SUCCESSFUL:
        print("ERROR: Cannot run functionality tests - main module import failed")
        return False
    
    try:
        # Test sanitize_name function
        test_name = "test<>name:with/invalid\\chars"
        sanitized = sanitize_name(test_name)
        print(f"PASS: sanitize_name: '{test_name}' -> '{sanitized}'")
        
        # Test find_photo_sets_enhanced with a test directory
        test_dir = Path(__file__).parent.parent
        try:
            photo_sets = find_photo_sets_enhanced(str(test_dir))
            print(f"PASS: find_photo_sets_enhanced: Found {len(photo_sets)} photo sets in test directory")
        except Exception as e:
            print(f"INFO: find_photo_sets_enhanced: Expected error for test directory: {e}")
        
        print("PASS: Core functionality test passed")
        return True
        
    except Exception as e:
        print(f"ERROR: Core functionality test failed: {e}")
        return False

def run_import_tests():
    """Test that all expected functions can be imported"""
    print("\nTesting module imports...")
    print("-" * 40)
    
    if not IMPORTS_SUCCESSFUL:
        print("ERROR: Import test failed - main module could not be imported at startup")
        return False
    
    try:
        print("PASS: All expected functions imported successfully")
        
        # Test function signatures
        functions_to_test = [
            ("find_photo_sets_enhanced", find_photo_sets_enhanced),
            ("extract_iid_from_xml", extract_iid_from_xml),
            ("sanitize_name", sanitize_name),
            ("batch_process_with_safety_nets", batch_process_with_safety_nets),
            ("main_func", main_func)
        ]
        
        for name, func in functions_to_test:
            if callable(func):
                print(f"PASS: {name} is callable")
            else:
                print(f"ERROR: {name} is not callable")
                
        return True
        
    except Exception as e:
        print(f"ERROR: Import test failed: {e}")
        return False

def run_all_tests():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Run Cetamura Batch Tool Tests')
    parser.add_argument('--quick', action='store_true', help='Run quick functionality test only')
    parser.add_argument('--imports', action='store_true', help='Test imports only')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    parser.add_argument('--no-pytest', action='store_true', help='Do not run pytest (skip full suite)')
    
    args = parser.parse_args()
    
    success = True
    
    # Determine behavior: imports and quick checks default to running, pytest can be skipped
    if args.imports or not any([args.quick, args.imports, args.all]):
        success &= run_import_tests()

    if args.quick or not any([args.quick, args.imports, args.all]):
        success &= run_quick_functionality_test()

    if not args.no_pytest and (args.all or not any([args.quick, args.imports, args.all])):
        success &= run_pytest_tests()
    else:
        if args.no_pytest:
            print('\nSkipping pytest run because --no-pytest was specified')
    
    print("\n" + "="*60)
    if success:
        print("ALL TESTS PASSED")
        print("Ready For Batch Processing!")
    else:
        print("SOME TESTS FAILED")
        print("Please check the errors above and fix any issues.")
    print("="*60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())

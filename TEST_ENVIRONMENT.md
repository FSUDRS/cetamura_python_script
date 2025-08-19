# Test Environment Documentation

## Overview
This test environment provides comprehensive testing capabilities for the Cetamura Batch Ingest Tool. It creates various folder structures and file scenarios to validate tool functionality across different use cases.

## Files

### create_test_environment.py
Generates test data with multiple scenarios:
- Standard flat folder structures
- Hierarchical folder structures  
- Mixed structure combinations
- Edge cases and error scenarios
- Large scale performance tests
- Deep nested directories
- Corrupted file handling

### run_tests.py
Automated test runner that:
- Validates photo set discovery
- Tests file processing capabilities
- Runs performance benchmarks
- Executes feature-specific tests

## Test Scenarios

### 1. Standard Structure
```
scenario_1_standard/
└── 2006/
    └── 46N-3W/
        ├── photo_1.jpg
        ├── metadata_1.xml
        ├── ... (5 pairs)
        └── MANIFEST.ini
```

### 2. Hierarchical Structure
```
scenario_2_hierarchical/
└── 2007/
    ├── MANIFEST.ini
    ├── 46N-3W/
    │   ├── image_1.jpg
    │   ├── meta_1.xml
    │   └── ... (3 pairs each)
    ├── 47N-2W/
    └── 48N-1W/
```

### 3. Mixed Structures
Combines both standard and hierarchical structures in the same parent directory.

### 4. Edge Cases
- Missing XML files
- Missing JPG files  
- Invalid XML (no IID)
- Special characters in filenames

### 5. Large Scale Test
- 3 years × 5 trenches = 15 photo sets
- 10 files per trench = 150 total files
- Tests performance with realistic data volumes

### 6. Deep Nested Structure
Tests deeply nested directory hierarchies (5+ levels).

### 7. Corrupted Files Test
Includes intentionally corrupted image files to test error handling.

### 8. Performance Test
Single photo set with 100 files for performance benchmarking.

## Usage

### Basic Test Run
```bash
python run_tests.py
```

### Performance Benchmark
```bash
python run_tests.py --performance
```

### Feature Tests Only
```bash
python run_tests.py --features
```

### Complete Test Suite (including file processing)
```bash
python run_tests.py --all
```

### Generate Test Data Only
```bash
python create_test_environment.py
```

## Test Output

The test runner provides:
- Pass/fail status for each scenario
- Discovery performance metrics
- File pairing accuracy validation
- Processing time measurements
- Error reporting with detailed messages

## Expected Results

### Discovery Tests
- Standard Structure: 1 photo set, 5 files
- Hierarchical Structure: 3 photo sets, 9 files
- Mixed Structures: 3 photo sets, 6 files
- Edge Cases: 1 photo set, 1 file (only valid pair)
- Large Scale: 15 photo sets, 150 files
- Deep Nested: 1 photo set, 3 files
- Corrupted Files: 1 photo set, 2 files (excluding corrupted)
- Performance: 1 photo set, 100 files

### Performance Expectations
- Discovery should complete in under 1 second for most scenarios
- Large scale test should complete in under 5 seconds
- Performance test should process 100 files in under 2 seconds

## Customization

### Adding New Test Scenarios
1. Add a new method to `TestEnvironmentBuilder`
2. Create the folder structure and files
3. Append to `self.test_scenarios`
4. Call from `build_all_scenarios()`

### Modifying Test Parameters
- Change file counts in existing scenarios
- Adjust image sizes for performance testing
- Add new file formats or XML structures
- Modify expected results in test assertions

## Integration with CI/CD

This test environment can be integrated into continuous integration pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Test Suite
  run: |
    python run_tests.py --all
    if [ $? -ne 0 ]; then exit 1; fi
```

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure `src/main.py` exists and is importable
2. **Permission Errors**: Run with appropriate file system permissions
3. **Disk Space**: Large scale tests require ~50MB of disk space
4. **PIL Dependencies**: Ensure Pillow is installed for image creation

### Debug Mode
Add debug logging to see detailed test execution:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This comprehensive test environment ensures robust validation of the Cetamura Batch Ingest Tool across all expected use cases and edge conditions.

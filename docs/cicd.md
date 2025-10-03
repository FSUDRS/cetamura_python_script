# CI/CD Pipeline Documentation

**Last Updated:** October 3, 2025  
**CI Provider:** GitHub Actions  
**Configuration:** `.github/workflows/ci.yml`

---

## Overview

The Cetamura Batch Ingest Tool uses GitHub Actions for automated testing and validation. The pipeline runs on every push and pull request to ensure code quality and prevent regressions.

---

## Pipeline Jobs

### Job 1: Test Matrix (Python 3.9 & 3.11)

Runs comprehensive test suite across multiple Python versions:

**Key Steps:**
- Installs dependencies from requirements files
- Runs all 25 tests with `pytest -v`
- Verifies test count (ensures no tests deleted)
- Runs critical multi-file processing regression test
- Validates PhotoSet structure tests
- Tests custom test runner in multiple modes

**Success Criteria:** All 25 tests pass on both Python versions

### Job 2: Verify Script

Validates module imports and data structures:

**Key Steps:**
- Imports all core functions (sanitize_name, convert_jpg_to_tiff, etc.)
- Imports enhanced functions (find_photo_sets_enhanced, batch_process_with_safety_nets)
- Imports data structures (PhotoSet, FilePair, BatchContext)
- Runtime validation that jpg_files/xml_files are LISTS
- Lists all available functions (diagnostic)

**Success Criteria:** All imports succeed, structures validate

### Job 3: Regression Tests (NEW)

Explicitly prevents critical bug regressions:

**Protected Against:**
- "Only first file processed" bug (v2025.09.19)
- PhotoSet structure changes
- Batch processing failures

**Key Tests:**
- `test_no_files_skipped_in_multi_file_set` - Verifies ALL files processed
- `test_batch_process_multi_file_dry_run` - Tests dry-run with 3 files
- `test_batch_process_multi_file_staging` - Tests staging with 3 files

**Success Criteria:** All regression tests pass

---

## Critical Bug Protection

### The "Only First File" Bug

**What was broken (v2025.09.19):**
```python
files = FilePair(xml=photo_set.xml_files[0], jpg=photo_set.jpg_files[0], iid=iid)
# Only processed index [0] - first file only!
```

**Current fix (v2025.10.03):**
```python
for xml_file in photo_set.xml_files:  # Loop through ALL
    # Process each file...
```

**CI Protection:**
If anyone reverts to the bug, these tests FAIL:
- `test_no_files_skipped_in_multi_file_set`
- `test_batch_process_multi_file_dry_run` 
- `test_batch_process_multi_file_staging`

**Error you'll see:** "Expected 3 files processed, got 1"

---

## Test Coverage

**Total Tests:** 25  
**Critical Tests:** 5 (regression prevention)  
**Required Pass Rate:** 100%

**Test Categories:**
- Data Structures: 3 tests
- Multi-file Processing: 5 tests  
- Photo Set Detection: 4 tests
- IID Extraction: 4 tests
- Image Processing: 2 tests
- Integration Tests: 2 tests
- Backward Compatibility: 1 test
- Other Core Functions: 4 tests

See `docs/TEST_COVERAGE.md` for complete details.

---

## Trigger Events

**Automatic:**
- Push to: main, master, ci-cd-development
- Pull requests to: main, master

**Manual:**
- workflow_dispatch (click "Run workflow" in Actions tab)

---

## Local Testing

Before pushing, run locally:

```bash
# All tests
python -m pytest tests/test_main.py -v

# Critical regression test
python -m pytest tests/test_main.py::test_no_files_skipped_in_multi_file_set -v

# Verify test count
python -m pytest tests/ --collect-only -q
```

Expected: "25 tests collected"

---

## When CI Fails

**Common failures and fixes:**

1. **"Expected 3 files, got 1"**
   - Multi-file bug returned
   - Check batch_process_with_safety_nets loop
   - Ensure it iterates through ALL xml_files

2. **"jpg_files must be a list"**
   - PhotoSet structure changed
   - Check PhotoSet NamedTuple definition
   - Ensure `jpg_files: List[Path]` not `Path`

3. **"Test count mismatch"**
   - Tests were deleted
   - Restore from git or justify deletion

**Remember:** Fix the code, don't skip the test. CI is correct, code is wrong (per SYSTEM_FLOW.md).

---

## Performance

**Typical Runtime:** 6-10 minutes total
- Test Matrix: 3-5 min (parallel)
- Verify Script: 1-2 min
- Regression Tests: 2-3 min

---

## Future Enhancements

Potential additions:
- Code coverage reporting
- Performance benchmarking  
- Multi-OS testing (when supported)
- Nightly builds
- Auto-release on tag push

---

**CI Status:** All jobs passing  
**Next Review:** Before v2025.10.04 release

## Manual Build
```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed src/main.py --name Cetamura_Batch_Tool

# Find your .exe in dist/ folder
```

## Troubleshooting
- **Build fails**: Check Python version matches (3.11)
- **Missing modules**: Add to `requirements.txt`
- **Large file size**: Normal for bundled executable (~50MB)
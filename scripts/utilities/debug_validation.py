#!/usr/bin/env python3
"""
Debug script to reproduce the dry run vs staging validation discrepancy
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import batch_process_with_safety_nets


def test_validation_discrepancy():
    """Test both dry run and staging mode on the same directory"""

    # Use our test data directory
    test_dir = Path("test_data/scenario_1_standard")
    if not test_dir.exists():
        print(f"❌ Test directory {test_dir} does not exist")
        return

    print("🔍 Testing Validation Discrepancy")
    print(f"📁 Test Directory: {test_dir}")
    print()

    # Test 1: Dry Run Mode
    print("=== DRY RUN MODE ===")
    try:
        success_dry, error_dry, csv_dry = batch_process_with_safety_nets(
            str(test_dir), dry_run=True, staging=False
        )
        print(f"✅ Dry Run Complete - Success: {success_dry}, Errors: {error_dry}")
        print(f"📊 CSV Report: {csv_dry}")

        # Read CSV content
        if Path(csv_dry).exists():
            with open(csv_dry, "r") as f:
                dry_content = f.read()
                print("📋 Dry Run Results:")
                print(dry_content)
                print()

    except Exception as e:
        print(f"❌ Dry Run Failed: {e}")

    # Test 2: Staging Mode
    print("=== STAGING MODE ===")
    try:
        success_staging, error_staging, csv_staging = batch_process_with_safety_nets(
            str(test_dir), dry_run=False, staging=True
        )
        print(
            f"✅ Staging Complete - Success: {success_staging}, Errors: {error_staging}"
        )
        print(f"📊 CSV Report: {csv_staging}")

        # Read CSV content
        if Path(csv_staging).exists():
            with open(csv_staging, "r") as f:
                staging_content = f.read()
                print("📋 Staging Results:")
                print(staging_content)
                print()

    except Exception as e:
        print(f"❌ Staging Failed: {e}")

    # Compare results
    print("=== COMPARISON ===")
    dry_status = success_dry if "success_dry" in locals() else "ERROR"
    dry_errors = error_dry if "error_dry" in locals() else "ERROR"
    staging_status = success_staging if "success_staging" in locals() else "ERROR"
    staging_errors = error_staging if "error_staging" in locals() else "ERROR"

    print(f"Dry Run - Success: {dry_status}, Errors: {dry_errors}")
    print(f"Staging - Success: {staging_status}, Errors: {staging_errors}")

    if "error_dry" in locals() and "error_staging" in locals():
        if error_dry != error_staging:
            print("🚨 DISCREPANCY FOUND!")
            print(f"   Dry Run reports {error_dry} errors")
            print(f"   Staging reports {error_staging} errors")
        else:
            print("✅ Both modes report same error count")


if __name__ == "__main__":
    test_validation_discrepancy()

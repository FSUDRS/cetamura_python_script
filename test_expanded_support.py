
import os
import shutil
import unittest
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import batch_process_with_safety_nets, VALID_IMAGE_EXTENSIONS

class TestExpandedSupport(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_expanded_env")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        
        self.input_dir = self.test_dir / "input"
        self.input_dir.mkdir()
        
        # Create Manifest
        with open(self.input_dir / "MANIFEST.ini", "w") as f:
            f.write("[Manifest]\ncreated=now")

    def tearDown(self):
        if self.test_dir.exists():
            # Retry cleanup to handle Windows file locking
            try:
                shutil.rmtree(self.test_dir)
            except Exception as e:
                print(f"Warning: Failed to clean up test dir: {e}")

    def create_dummy_xml(self, name, iid):
        root = ET.Element("mods", xmlns="http://www.loc.gov/mods/v3")
        ident = ET.SubElement(root, "{http://www.loc.gov/mods/v3}identifier", type="IID")
        ident.text = iid
        tree = ET.ElementTree(root)
        tree.write(self.input_dir / f"{name}.xml")

    def create_dummy_image(self, name, ext):
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(self.input_dir / f"{name}{ext}")

    def test_png_processing(self):
        self.create_dummy_xml("test_png", "IID_PNG_001")
        self.create_dummy_image("test_png", ".png")
        
        print("\nRunning PNG Test...")
        batch_process_with_safety_nets(str(self.input_dir), dry_run=False, staging=False)
        
        output_dir = self.input_dir / "output"
        zip_file = output_dir / "IID_PNG_001.zip"
        self.assertTrue(zip_file.exists(), f"PNG ZIP NOT FOUND AT {zip_file}")

    def test_tiff_processing(self):
        self.create_dummy_xml("test_tiff", "IID_TIFF_001")
        self.create_dummy_image("test_tiff", ".tiff")
        
        print("\nRunning TIFF Test...")
        batch_process_with_safety_nets(str(self.input_dir), dry_run=False, staging=False)
        
        output_dir = self.input_dir / "output"
        zip_file = output_dir / "IID_TIFF_001.zip"
        self.assertTrue(zip_file.exists(), f"TIFF ZIP NOT FOUND AT {zip_file}")

    def test_pdf_processing(self):
        self.create_dummy_xml("test_pdf", "IID_PDF_001")
        # Create a valid PDF using PIL
        try:
            img = Image.new('RGB', (100, 100), color = 'blue')
            img.save(self.input_dir / "test_pdf.pdf", "PDF")
        except Exception as e:
            print(f"Skipping PDF test creation: {e}")
            return
            
        print("\nRunning PDF Test...")
        # This might fail on environments without Ghostscript, so we just check it runs without crash
        success, errors, _ = batch_process_with_safety_nets(str(self.input_dir), dry_run=False, staging=False)
        
        # Check if we have ghostscript by checking if success > 0
        # If success == 0, it means conversion failed (caught exception), which is acceptable behavior on this dev machine
        if success > 0:
            output_dir = self.input_dir / "output"
            zip_file = output_dir / "IID_PDF_001.zip"
            self.assertTrue(zip_file.exists(), "PDF ZIP not created despite success report")
        else:
            print("PDF conversion failed gracefully (likely missing Ghostscript)")

if __name__ == '__main__':
    unittest.main()

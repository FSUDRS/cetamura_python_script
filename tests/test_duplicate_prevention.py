"""
Regression tests for duplicate-package prevention.

Covers two real-world failure modes found in the July 2026 trench photo batch:
1. A stray manifest.ini at the batch root caused every photo to be claimed by
   two photo sets and packaged twice (once with the wrong manifest).
2. MODS collection master files (root element <modsCollection>) were misread
   as per-photo metadata, generating a bogus extra package for the first
   record's IID.
"""

import zipfile

import pytest
from PIL import Image

from src.main import (
    batch_process_with_safety_nets,
    find_photo_sets_enhanced,
    is_mods_collection_xml,
)

MODS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<mods xmlns="http://www.loc.gov/mods/v3" version="3.6">
    <identifier type="IID">{iid}</identifier>
    <titleInfo><title>Test {iid}</title></titleInfo>
</mods>"""

COLLECTION_XML = """<?xml version="1.0" encoding="UTF-8"?>
<modsCollection xmlns="http://www.loc.gov/mods/v3">
    <mods version="3.6">
        <identifier type="IID">TEST_DUP_001</identifier>
        <titleInfo><title>Master record for TEST_DUP_001</title></titleInfo>
    </mods>
</modsCollection>"""


def make_manifest(path, parent_collection):
    path.write_text(
        "[package]\n"
        "submitter_email = test@fsu.edu\n"
        "content_model = islandora:sp_large_image_cmodel\n"
        f"parent_collection = {parent_collection}\n"
    )


@pytest.fixture
def nested_manifest_batch(tmp_path):
    """
    Batch replicating the problematic layout:
    - root/
        - manifest.ini            (stray, wrong parent_collection)
        - 1990/
            - collection.xml      (modsCollection master file)
            - trenchA/
                - manifest.ini    (correct)
                - TEST_DUP_001.xml / .jpg
                - TEST_DUP_002.xml / .jpg
    """
    root = tmp_path / "batch"
    trench = root / "1990" / "trenchA"
    trench.mkdir(parents=True)

    make_manifest(root / "manifest.ini", "fsu:wrong_truncated")
    make_manifest(trench / "manifest.ini", "fsu:correct_trenchA")
    (root / "1990" / "collection.xml").write_text(COLLECTION_XML)

    for iid in ("TEST_DUP_001", "TEST_DUP_002"):
        (trench / f"{iid}.xml").write_text(MODS_TEMPLATE.format(iid=iid))
        Image.new("RGB", (64, 64), color="blue").save(trench / f"{iid}.jpg")

    return root


def test_is_mods_collection_xml(tmp_path):
    collection = tmp_path / "collection.xml"
    collection.write_text(COLLECTION_XML)
    assert is_mods_collection_xml(collection) is True

    single = tmp_path / "single.xml"
    single.write_text(MODS_TEMPLATE.format(iid="TEST_SINGLE_001"))
    assert is_mods_collection_xml(single) is False

    malformed = tmp_path / "malformed.xml"
    malformed.write_text("<mods>broken & unclosed")
    assert is_mods_collection_xml(malformed) is False


def test_collection_xml_excluded_from_photo_sets(nested_manifest_batch):
    photo_sets = find_photo_sets_enhanced(str(nested_manifest_batch))

    all_xml = [x for ps in photo_sets for x in ps.xml_files]
    assert not any(x.name == "collection.xml" for x in all_xml)


def test_closest_manifest_wins_no_duplicate_claims(nested_manifest_batch):
    photo_sets = find_photo_sets_enhanced(str(nested_manifest_batch))

    all_xml = [x for ps in photo_sets for x in ps.xml_files]
    assert len(all_xml) == len(set(all_xml)), "an XML was claimed by multiple sets"

    # Both photos must be claimed by the trench manifest, not the stray root one
    for ps in photo_sets:
        if ps.xml_files:
            assert ps.manifest_file.parent.name == "trenchA"


def test_batch_run_packages_each_photo_once(nested_manifest_batch):
    success, errors, _csv = batch_process_with_safety_nets(
        str(nested_manifest_batch), dry_run=False, staging=True, workflow="photo"
    )

    assert success == 2
    assert errors == 0

    output = nested_manifest_batch / "staging_output"
    zips = sorted(output.glob("*.zip"))
    assert [z.name for z in zips] == ["TEST_DUP_001.zip", "TEST_DUP_002.zip"]

    # Every package must carry the trench manifest, not the stray root one
    for zip_path in zips:
        with zipfile.ZipFile(zip_path) as zf:
            manifest = zf.read("manifest.ini").decode()
        assert "fsu:correct_trenchA" in manifest
        assert "fsu:wrong_truncated" not in manifest

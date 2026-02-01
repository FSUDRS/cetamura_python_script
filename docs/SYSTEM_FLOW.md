# CETAMURA BATCH INGEST TOOL - SYSTEM REQUIREMENTS & ARCHITECTURE

**Version:** v2025.10.03  
**Last Updated:** October 3, 2025  
**Status:** AUTHORITATIVE SOURCE OF TRUTH

## Purpose of This Document

This is the **definitive requirements and architecture specification** for the Cetamura Batch Ingest Tool. Use this document to:

-  Understand the complete system behavior
-  Verify implementation correctness
-  Prevent assumptions and hallucinations about functionality
-  Reference exact data structures and algorithms
-  Debug issues by comparing actual vs. documented behavior
-  Onboard new developers

**IMPORTANT:** If code behavior differs from this document, the code is wrong (not this document).



## System Overview

### What This Tool Does
Automates the creation of AIS-compatible ZIP packages for the Cetamura Digital Collections by:
1. Discovering photo sets in complex directory structures
2. Extracting metadata from XML files
3. Converting JPG images to TIFF with EXIF orientation correction
4. Packaging files into individual ZIP archives
5. Generating detailed CSV processing reports

### What This Tool Does NOT Do
- Does not batch multiple images into one ZIP (one image = one ZIP)
- Does not modify original files in dry-run or staging modes
- Does not process files without matching XML metadata
- Does not handle video, PDF, or other non-JPG image formats
- Does not connect to external systems or databases

---

---

## Critical Data Structures (AUTHORITATIVE)

These are the EXACT data structures used in the system. Do not assume different structures exist.

### 1. PhotoSet (NamedTuple) - Lines 48-55 in src/main.py
```python
class PhotoSet(NamedTuple):
    """Data structure for a complete photo set"""
    base_directory: Path        # Folder containing the files
    jpg_files: List[Path]       # ALL JPG files in this directory
    xml_files: List[Path]       # ALL XML files in this directory
    manifest_file: Path         # Single manifest.ini file
    structure_type: str         # Either 'standard' or 'hierarchical'
```

**Key Facts:**
- PhotoSet contains **lists** of ALL files, not single files
- One PhotoSet = One directory with all its files
- `jpg_files` and `xml_files` are **always lists**, even if only one file
- `manifest_file` is a **single Path**, not a list
- PhotoSets are **immutable** (NamedTuple)

### 2. FilePair (NamedTuple) - Lines 42-46 in src/main.py
```python
class FilePair(NamedTuple):
    xml: Optional[Path]         # Single XML file (can be None)
    jpg: Optional[Path]         # Single JPG file (can be None)
    iid: str                    # Identifier extracted from XML
```

**Key Facts:**
- FilePair represents **ONE** JPG/XML pair to be processed
- `xml` and `jpg` are **Optional** - can be None
- `iid` is **always a string**, never None (uses "UNKNOWN" as fallback)
- Created **per file**, not per PhotoSet
- Used as input to `process_file_set_with_context()`

### 3. BatchContext (NamedTuple) - Lines 48-55 in src/main.py
```python
class BatchContext(NamedTuple):
    """Context object to pass configuration flags and resources"""
    output_dir: Path            # Where to save output ZIPs
    dry_run: bool              # True = preview only, False = actual processing
    staging: bool              # True = output to staging_output/, False = output/
    csv_path: Path             # Path to CSV report file
    csv_writer: Optional[Any]  # CSV writer object (None if file closed)
    logger: logging.Logger     # Logger instance for this batch
```

**Key Facts:**
- Passed to all processing functions for configuration
- Immutable - cannot change mid-processing
- `dry_run=True` means NO files are modified
- `csv_writer` can be None (check before using)

---

## Processing Rules (AUTHORITATIVE)

### Rule 1: Photo Set Discovery Criteria

A directory is considered a valid photo set if **ALL** of these are true:
1. Contains **at least one** `.jpg` or `.jpeg` file
2. Contains **at least one** `.xml` file
3. At least one XML file contains a valid `<identifier type="IID">` tag
4. Contains **exactly one** `manifest.ini` file (case-insensitive)

**Implementation:** `validate_photo_set()` function at line 410

### Rule 2: File Matching Algorithm

JPG and XML files are matched by **filename stem** (name without extension):
```
FSU_Cetamura_photos_19900711_15.5N18W_001.jpg
FSU_Cetamura_photos_19900711_15.5N18W_001.xml
                                           ↑
                    Same stem = MATCH
```

**Implementation:** Lines 1029-1034 in `batch_process_with_safety_nets()`

```python
for jpg_file in photo_set.jpg_files:
    if jpg_file.stem == xml_file.stem:
        matching_jpg = jpg_file
        break
```

**Matching Behavior:**
- Case-sensitive stem comparison
- First match wins (if duplicates exist)
- Unmatched XML files generate WARNING in CSV
- Unmatched JPG files are logged but not processed

### Rule 3: ALL Files Must Be Processed

**CRITICAL REQUIREMENT:** The system MUST process **every** JPG/XML pair in each PhotoSet.

**Correct Implementation (Current):**
```python
for photo_set in photo_sets:
    for xml_file in photo_set.xml_files:  # ← Loop through ALL
        # Extract IID, find matching JPG, create FilePair
        # Process this specific pair
```

**Incorrect Implementation (Bug from v2025.10.03):**
```python
for photo_set in photo_sets:
    # Process only photo_set.xml_files[0]  # ← WRONG! Only first file
```

**Verification:**
- If a directory has 6 JPG + 6 XML files, exactly 6 FilePairs must be created
- CSV report should have 6 SUCCESS rows (or 6 ERROR rows, or mix)
- Never skip files silently

### Rule 4: IID Extraction

IID is extracted from XML using this **exact** XPath query:

**With namespace:**
```python
namespaces = {'mods': 'http://www.loc.gov/mods/v3'}
identifier = root.find(".//mods:identifier[@type='IID']", namespaces)
```

**Without namespace (fallback):**
```python
identifier = root.find(".//identifier[@type='IID']")
```

**Rules:**
- Try namespaced version first, then non-namespaced
- IID text is `.strip()`-ped to remove whitespace
- If both fail, return `None`
- Empty IID text is treated as invalid (return `None`)

**Implementation:** `extract_iid_from_xml()` at line 756

### Rule 5: Dry Run vs. Production Behavior

**Dry Run (`dry_run=True`):**
- NO files are created, converted, renamed, or deleted
- CSV report is created showing what WOULD happen
- Logs say "DRY RUN: Would convert..." etc.
- All validation still occurs
- CSV path: `{folder_path}/batch_report_{timestamp}.csv`

**Production (`dry_run=False`):**
- Files ARE created, converted, renamed, and deleted
- Original JPG is DELETED after successful TIFF conversion
- CSV report shows actual results
- CSV path: `{output_dir}/batch_report_{timestamp}.csv`

**Staging (`staging=True`):**
- Output goes to `{folder_path}/staging_output/` instead of `{folder_path}/output/`
- Original files remain untouched
- Can review output before production run

---

---

## System Architecture (Layer by Layer)

### Layer 1: GUI (Tkinter Interface)

**Location:** Lines 1290-1445 in `src/main.py`

**Components:**
- Main window with folder selection
- Processing options dialog (dry-run, staging, advanced logs)
- Progress bar and status labels
- Menu bar (File, Help)

**User Flow:**
1. Launch: `python src/main.py` → `main()` executes
2. GUI window opens
3. User clicks "Select Folder" → `select_folder()` called
4. User selects directory via `filedialog.askdirectory()`
5. System calls `find_photo_sets()` for preview
6. GUI shows: "Found X photo sets in selected folder"
7. User clicks "Start Batch Process" → `start_batch_process()` called
8. Options dialog appears → `show_processing_options_dialog()`
9. User selects dry-run/staging/advanced-logs
10. Processing starts in background thread

**Key Functions:**
- `main()` - Initialize GUI
- `select_folder()` - Folder picker
- `start_batch_process()` - Start processing
- `show_processing_options_dialog()` - Mode selection

### Layer 2: Discovery & Grouping

**Purpose:** Find all relevant files and organize into PhotoSets

#### Step 2.1: Recursive File Discovery

**Function:** `find_all_files_recursive(parent_folder, max_depth=5)`  
**Location:** Lines 267-299

**Algorithm:**
```python
def find_all_files_recursive(parent_folder: Path, max_depth: int = 5):
    files = {'jpg': [], 'xml': [], 'manifest': []}
    
    def search_directory(directory: Path, current_depth: int):
        if current_depth > max_depth:
            return  # Stop at depth limit
        
        for item in directory.iterdir():
            if item.is_file():
                if item.suffix.lower() in ['.jpg', '.jpeg']:
                    files['jpg'].append(item)
                elif item.suffix.lower() == '.xml':
                    files['xml'].append(item)
                elif item.name.lower() == 'manifest.ini':
                    files['manifest'].append(item)
            elif item.is_dir():
                search_directory(item, current_depth + 1)
    
    search_directory(parent_folder, 0)
    return files
```

**Behavior:**
- Searches up to 5 levels deep (prevents infinite recursion)
- Collects ALL `.jpg`, `.jpeg`, `.xml`, `manifest.ini` files
- Case-insensitive extension matching
- Skips permission-denied directories (logs warning)
- Returns dictionary with lists of Path objects

**Example Output:**
```python
{
    'jpg': [Path('X:/Cetamura/1990/1990/15.5N-18W/file1.jpg'), ...],  # 19 files
    'xml': [Path('X:/Cetamura/1990/1990/15.5N-18W/file1.xml'), ...],  # 19 files
    'manifest': [Path('X:/Cetamura/1990/1990/15.5N-18W/manifest.ini'), ...]  # 6 files
}
```

#### Step 2.2: Group Files by Directory

**Function:** `group_files_by_directory(files)`  
**Location:** Lines 302-327

**Algorithm:**
```python
def group_files_by_directory(files: Dict[str, List[Path]]):
    directory_groups = defaultdict(lambda: {'jpg': [], 'xml': [], 'manifest': []})
    
    # Group by parent directory
    for file_type, file_list in files.items():
        for file_path in file_list:
            parent_dir = file_path.parent
            directory_groups[parent_dir][file_type].append(file_path)
    
    # Convert to list of dicts
    file_groups = []
    for directory, grouped_files in directory_groups.items():
        file_group = {
            'directory': directory,
            'jpg_files': grouped_files['jpg'],
            'xml_files': grouped_files['xml'],
            'manifest_files': grouped_files['manifest']
        }
        file_groups.append(file_group)
    
    return file_groups
```

**Behavior:**
- Groups files by their immediate parent directory
- One group per unique directory
- Preserves all files in each directory

**Example Output:**
```python
[
    {
        'directory': Path('X:/Cetamura/1990/1990/15.5N-18W'),
        'jpg_files': [Path('...001.jpg'), Path('...002.jpg'), ...],  # 6 files
        'xml_files': [Path('...001.xml'), Path('...002.xml'), ...],  # 6 files
        'manifest_files': [Path('manifest.ini')]
    },
    {
        'directory': Path('X:/Cetamura/1990/1990/18N-18W'),
        'jpg_files': [...],  # 5 files
        'xml_files': [...],  # 5 files
        'manifest_files': [Path('manifest.ini')]
    },
    # ... 4 more groups
]
```

#### Step 2.3: Create and Validate PhotoSets

**Function:** `find_photo_sets_enhanced(parent_folder, flexible_structure=True)`  
**Location:** Lines 471-530

**Algorithm:**
```python
def find_photo_sets_enhanced(parent_folder: str, flexible_structure: bool = True):
    parent_path = Path(parent_folder).resolve()
    all_files = find_all_files_recursive(parent_path)
    photo_sets = []
    
    # Try hierarchical detection (manifest in parent, files in subdirs)
    if flexible_structure:
        hierarchical_sets = find_hierarchical_sets(all_files, parent_path)
        for photo_set in hierarchical_sets:
            if validate_photo_set(photo_set):
                photo_sets.append(photo_set)
    
    # Try standard grouping (all files in same directory)
    file_groups = group_files_by_directory(all_files)
    for group in file_groups:
        # Skip if already found as hierarchical set
        if any(ps.base_directory == group['directory'] for ps in photo_sets):
            continue
        
        if group['jpg_files'] and group['xml_files'] and group['manifest_files']:
            photo_set = PhotoSet(
                base_directory=group['directory'],
                jpg_files=group['jpg_files'],
                xml_files=group['xml_files'],
                manifest_file=group['manifest_files'][0],
                structure_type='standard'
            )
            if validate_photo_set(photo_set):
                photo_sets.append(photo_set)
    
    return photo_sets
```

**Validation Logic:**
```python
def validate_photo_set(photo_set: PhotoSet) -> bool:
    # Must have at least one JPG
    if len(photo_set.jpg_files) == 0:
        return False
    
    # Must have at least one XML
    if len(photo_set.xml_files) == 0:
        return False
    
    # At least one XML must have valid IID
    valid_xml_count = 0
    for xml_file in photo_set.xml_files:
        if extract_iid_from_xml_enhanced(xml_file):
            valid_xml_count += 1
    
    if valid_xml_count == 0:
        return False
    
    return True
```

**Example Output:**
```python
[
    PhotoSet(
        base_directory=Path('X:/Cetamura/1990/1990/15.5N-18W'),
        jpg_files=[Path('...'), ...],  # 6 files
        xml_files=[Path('...'), ...],  # 6 files
        manifest_file=Path('manifest.ini'),
        structure_type='standard'
    ),
    # ... 5 more PhotoSets
]
```

### Layer 3: Batch Processing Loop

**Function:** `batch_process_with_safety_nets(folder_path, dry_run, staging)`  
**Location:** Lines 952-1081

**CRITICAL ALGORITHM (Lines 1020-1069):**

```python
# Create context
context = BatchContext(...)

# Global Recovery Index: Map all image files in project by stem
global_image_index = {}
for file in find_all_files_recursive(folder_path):
    if is_image(file):
        global_image_index[file.stem] = file

# Find photo sets
photo_sets = find_photo_sets_enhanced(folder_path)

# Process EVERY file in EVERY photo set
for photo_set in photo_sets:
    # Loop through ALL XML files in this photo set
    for xml_file in photo_set.xml_files:
        try:
            # Extract IID from this specific XML
            iid = extract_iid_from_xml(xml_file)
            
            # Find matching JPG
            matching_jpg = None
            
            # Strategy 1: Strict Filename Match (Local)
            for jpg_file in photo_set.jpg_files:
                if jpg_file.stem == xml_file.stem:
                    matching_jpg = jpg_file
                    break
            
            # Strategy 2: Smart IID Match (Local)
            if not matching_jpg:
                 # Check if IID appears in any local filename
                 ...

            # Strategy 3: Lone Survivor (Local)
            if not matching_jpg and len(jpgs)==1 and len(xmls)==1:
                 matching_jpg = photo_set.jpg_files[0]

            # Strategy 4: Global Recovery (Cross-Directory Link) [NEW v2026.01.30]
            if not matching_jpg:
                if xml_file.stem in global_image_index:
                    matching_jpg = global_image_index[xml_file.stem]
                    logger.warning(f"Strategy 4: Recovered image from {matching_jpg.parent}")

            # Warn if still no match
            if matching_jpg is None:
                logger.warning(f"No matching JPG for {xml_file.name}")
                csv_writer.writerow([iid, str(xml_file), 'N/A', 'WARNING', 'MISSING_JPG', '...'])
                continue
            
            # Create FilePair for THIS pair
            files = FilePair(
                xml=xml_file,
                jpg=matching_jpg,
                iid=iid
            )
            
            # Process this specific pair
            success = process_file_set_with_context(files, iid, photo_set.base_directory, context)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            logger.error(...)
```

**Key Behaviors:**
1. **Outer loop:** Iterate through PhotoSets
2. **Inner loop:** Iterate through ALL xml_files in each PhotoSet
3. **Matching Strategies:** 
    - 1. Precise local filename match
    - 2. Local IID substring match
    - 3. Single-pair assumption
    - 4. **Global Recovery:** Finds images even if moved to wrong folder
4. **Error handling:** File-level errors don't stop batch
5. **Counting:** Track success/error per file

**Example Execution:**
```
PhotoSet 1: 15.5N-18W (6 JPG, 6 XML)
  Process XML 1 → Find JPG 1 → Create FilePair 1 → Process → Success
  Process XML 2 → Find JPG 2 → Create FilePair 2 → Process → Success
  Process XML 3 → Find JPG 3 → Create FilePair 3 → Process → Success
  Process XML 4 → Find JPG 4 → Create FilePair 4 → Process → Success
  Process XML 5 → Find JPG 5 → Create FilePair 5 → Process → Success
  Process XML 6 → Find JPG 6 → Create FilePair 6 → Process → Success

PhotoSet 2: 18N-18W (5 JPG, 5 XML)
  Process XML 1 → Find JPG 1 → Create FilePair 1 → Process → Success
  ... (4 more)

... (4 more PhotoSets)

Result: 19 files processed (not 6!)
```

### Layer 4: Individual File Processing

**Function:** `process_file_set_with_context(files, iid, subfolder, context)`  
**Location:** Lines 878-948

**Algorithm:**
```python
def process_file_set_with_context(files: FilePair, iid: str, subfolder: Path, context: BatchContext):
    jpg_file = files.jpg
    xml_file = files.xml
    
    # Check for missing JPG
    if jpg_file is None:
        csv_writer.writerow([iid, str(xml_file), 'N/A', 'WARNING', 'ORPHANED_XML', '...'])
        return False
    
    # Validate orientation
    orientation_info = validate_image_orientation(jpg_file)
    
    if context.dry_run:
        # DRY RUN: Log what would happen
        logger.info(f"DRY RUN: Would convert {jpg_file.name} to TIFF...")
        logger.info(f"DRY RUN: Would extract IID {iid} from {xml_file.name}")
        logger.info(f"DRY RUN: Would create ZIP package for {iid}")
        csv_writer.writerow([iid, str(xml_file), str(jpg_file), 'SUCCESS', 'DRY_RUN', '...'])
        return True
    
    # PRODUCTION: Actually process
    # Step 1: Convert JPG to TIFF
    tiff_path = convert_jpg_to_tiff(jpg_file)
    if tiff_path is None:
        csv_writer.writerow([iid, str(xml_file), str(jpg_file), 'ERROR', 'CONVERT_FAILED', '...'])
        return False
    
    # Step 2: Check for missing XML
    if xml_file is None:
        csv_writer.writerow([iid, 'N/A', str(jpg_file), 'ERROR', 'MISSING_XML', '...'])
        return False
    
    # Step 3: Rename files based on IID
    new_tiff, new_xml = rename_files(subfolder, tiff_path, xml_file, iid)
    
    # Step 4: Find manifest
    manifest_files = list(subfolder.glob("*.ini")) + list(subfolder.glob("MANIFEST.ini"))
    manifest_path = manifest_files[0] if manifest_files else None
    
    if not manifest_path:
        csv_writer.writerow([iid, str(xml_file), str(jpg_file), 'ERROR', 'NO_MANIFEST', '...'])
        return False
    
    # Step 5: Package into ZIP
    package_to_zip(new_tiff, new_xml, manifest_path, context.output_dir)
    
    # Success
    csv_writer.writerow([iid, str(xml_file), str(jpg_file), 'SUCCESS', 'PACKAGED', '...'])
    return True
```

**Processing Steps (Production):**
1. **Orientation Check:** Read EXIF data
2. **Convert:** JPG → TIFF with orientation correction
3. **Rename:** Files renamed using sanitized IID
4. **Package:** Create ZIP with TIFF + XML + manifest.ini
5. **Cleanup:** Original JPG deleted after successful conversion

**Processing Steps (Dry Run):**
1. **Orientation Check:** Read EXIF data
2. **Log:** What would be done
3. **CSV:** Record simulated results
4. **No Changes:** No files created/modified/deleted

### Layer 5: File Conversion & Packaging

#### JPG to TIFF Conversion

**Function:** `convert_jpg_to_tiff(jpg_path)`  
**Location:** Lines 699-735

```python
def convert_jpg_to_tiff(jpg_path: Path):
    tiff_path = jpg_path.with_suffix('.tiff')
    
    # Open and apply EXIF orientation
    with Image.open(jpg_path) as img:
        img = apply_exif_orientation(img, jpg_path)
    
    # Save as TIFF
    with Image.open(jpg_path) as img:
        img = apply_exif_orientation(img, jpg_path)
        img.save(tiff_path, 'TIFF', compression='tiff_deflate')
    
    # Delete original JPG
    jpg_path.unlink()
    
    return tiff_path
```

**Behavior:**
- Reads JPG file with PIL
- Applies EXIF orientation correction (auto-rotate)
- Saves as TIFF with deflate compression
- Deletes original JPG after successful save
- Returns Path to new TIFF file

#### File Renaming

**Function:** `rename_files(path, tiff_file, xml_file, iid)`  
**Location:** Lines 769-801

```python
def rename_files(path: Path, tiff_file: Path, xml_file: Path, iid: str):
    base_name = sanitize_name(iid)
    new_tiff_path = path / f"{base_name}.tiff"
    new_xml_path = path / f"{base_name}.xml"
    
    # Check for conflicts
    conflict = False
    if new_tiff_path.exists() and new_tiff_path != tiff_file:
        conflict = True
    if new_xml_path.exists() and new_xml_path != xml_file:
        conflict = True
    
    # Add suffix if conflict
    if conflict:
        suffix = 0
        while True:
            suffix += 1
            new_tiff_path = path / f"{base_name}_{suffix}.tiff"
            new_xml_path = path / f"{base_name}_{suffix}.xml"
            if not new_tiff_path.exists() and not new_xml_path.exists():
                break
    
    # Rename
    tiff_file.rename(new_tiff_path)
    xml_file.rename(new_xml_path)
    
    return new_tiff_path, new_xml_path
```

**Sanitization Rules:**
- Spaces → underscores
- Invalid chars (`<>:"/\|?*`) → underscores
- Dots removed
- Non-ASCII characters removed
- Multiple underscores collapsed to one

#### ZIP Packaging

**Function:** `package_to_zip(tiff_path, xml_path, manifest_path, output_folder)`  
**Location:** Lines 854-875

```python
def package_to_zip(tiff_path, xml_path, manifest_path, output_folder):
    output_folder.mkdir(parents=True, exist_ok=True)
    base_name = tiff_path.stem
    zip_path = output_folder / f"{sanitize_name(base_name)}.zip"
    
    # Check for existing ZIP
    if zip_path.exists():
        zip_path = output_folder / f"{sanitize_name(base_name)}_{timestamp}.zip"
    
    # Create ZIP
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(tiff_path, tiff_path.name)
        zipf.write(xml_path, xml_path.name)
        zipf.write(manifest_path, manifest_path.name)
    
    return zip_path
```

**Behavior:**
- Creates output folder if needed
- ZIP name = IID (sanitized)
- Contains exactly 3 files: TIFF, XML, manifest.ini
- Adds timestamp suffix if ZIP already exists

---

## CSV Report Format

### Columns (Exact Order):
1. **IID** - Identifier from XML
2. **XML_Path** - Full path to XML file
3. **JPG_Path** - Full path to JPG file (or 'N/A')
4. **Status** - SUCCESS, ERROR, WARNING, INFO
5. **Action** - What was done (DRY_RUN, PACKAGED, CONVERT_FAILED, etc.)
6. **Notes** - Additional details

### Example CSV:
```csv
IID,XML_Path,JPG_Path,Status,Action,Notes
FSU_Cetamura_photos_19900711_15.5N18W_001,X:\...\001.xml,X:\...\001.jpg,SUCCESS,DRY_RUN,Would process successfully
FSU_Cetamura_photos_19900724_15.5N18W_001,X:\...\002.xml,X:\...\002.jpg,SUCCESS,DRY_RUN,Would process successfully
FSU_Cetamura_photos_orphan,X:\...\orphan.xml,N/A,WARNING,MISSING_JPG,No matching JPG file found
SUMMARY,,,Success: 18,Errors: 1,Dry run: True
```

---
```
python src/main.py
    ↓
main() function runs
    ↓
Creates Tkinter GUI window
```

### User Selects Folder
```
User clicks "Select Folder"
    ↓
select_folder() executes
    ↓
filedialog.askdirectory() opens
    ↓
User selects: X:\Cetamura\1990\1990
    ↓
find_photo_sets(folder) called for preview
    ↓
GUI shows: "Found 6 photo sets in selected folder"
```

---

## 2. Photo Set Detection (Discovery Layer)

### Step 1: Recursive File Discovery
```python
find_photo_sets_enhanced(parent_folder)
    ↓
find_all_files_recursive(parent_path, max_depth=5)
    ↓
Recursively searches directories up to 5 levels deep
    ↓
Collects ALL files by type:
    - files['jpg']: [file1.jpg, file2.jpg, ...]
    - files['xml']: [file1.xml, file2.xml, ...]
    - files['manifest']: [manifest.ini, ...]
```

**Example Discovery:**
```
X:\Cetamura\1990\1990\
 15.5N-18W/
    FSU_Cetamura_photos_19900711_15.5N18W_001.jpg  ← Found
    FSU_Cetamura_photos_19900711_15.5N18W_001.xml  ← Found
    FSU_Cetamura_photos_19900724_15.5N18W_001.jpg  ← Found
    FSU_Cetamura_photos_19900724_15.5N18W_001.xml  ← Found
    ... (4 more JPG/XML pairs)
    manifest.ini  ← Found
 18N-18W/
    5 JPG files  ← All found
    5 XML files  ← All found
    manifest.ini  ← Found
 ... (4 more photo sets)

Total: 19 JPG, 19 XML, 6 manifests
```

### Step 2: Group by Directory
```python
group_files_by_directory(files)
    ↓
Groups files by parent directory
    ↓
Creates PhotoSet for each directory with:
    - base_directory: Path to folder
    - jpg_files: [all JPG files in folder]
    - xml_files: [all XML files in folder]
    - manifest_file: manifest.ini path
    - structure_type: 'standard' or 'hierarchical'
```

**Example PhotoSet:**
```python
PhotoSet(
    base_directory=Path('X:/Cetamura/1990/1990/15.5N-18W'),
    jpg_files=[
        Path('.../FSU_Cetamura_photos_19900711_15.5N18W_001.jpg'),
        Path('.../FSU_Cetamura_photos_19900724_15.5N18W_001.jpg'),
        Path('.../FSU_Cetamura_photos_19900725_15.5N18W_001.jpg'),
        Path('.../FSU_Cetamura_photos_19900726_15.5N18W_001.jpg'),
        Path('.../FSU_Cetamura_photos_19900726_15.5N18W_002.jpg'),
        Path('.../FSU_Cetamura_photos_19900727_15.5N18W_001.jpg')
    ],  # 6 JPG files
    xml_files=[
        Path('.../FSU_Cetamura_photos_19900711_15.5N18W_001.xml'),
        Path('.../FSU_Cetamura_photos_19900724_15.5N18W_001.xml'),
        Path('.../FSU_Cetamura_photos_19900725_15.5N18W_001.xml'),
        Path('.../FSU_Cetamura_photos_19900726_15.5N18W_001.xml'),
        Path('.../FSU_Cetamura_photos_19900726_15.5N18W_002.xml'),
        Path('.../FSU_Cetamura_photos_19900727_15.5N18W_001.xml')
    ],  # 6 XML files
    manifest_file=Path('.../manifest.ini'),
    structure_type='standard'
)
```

### Step 3: Validation
```python
validate_photo_set(photo_set)
    ↓
Checks:
    - Has at least 1 JPG file? 
    - Has at least 1 XML file? 
    - Can extract IID from XML files? 
    ↓
Returns: True (photo set is valid)
```

**Result:** 6 valid PhotoSets found

---

## 3. Batch Processing Start (Processing Layer)

### User Clicks "Start Batch Process"
```
start_batch_process() executes
    ↓
show_processing_options_dialog()
    ↓
User selects:
    - Dry Run: True
    - Staging: False
    - Advanced Logs: True
    ↓
batch_process_with_safety_nets(folder_path, dry_run=True, staging=False)
```

### Initialize Processing Context
```python
BatchContext created:
    - output_dir: X:\Cetamura\1990\1990\output
    - dry_run: True
    - staging: False
    - csv_path: X:\Cetamura\1990\1990\batch_report_20251003_120000.csv
    - csv_writer: CSV writer object
    - logger: logging.Logger
```

---

## 4. **NEW: Multi-File Processing Loop** 

### OLD BEHAVIOR (Before Fix):
```python
#  OLD: Only processed FIRST file
for photo_set in photo_sets:
    files = FilePair(
        xml=photo_set.xml_files[0],  # Only first!
        jpg=photo_set.jpg_files[0],  # Only first!
        iid=iid
    )
    process_file_set_with_context(files, iid, ...)

# Result: 6 photo sets → 6 files processed (1 per set)
```

### NEW BEHAVIOR (After Fix):
```python
#  NEW: Processes ALL files
for photo_set in photo_sets:
    # Loop through EVERY XML file
    for xml_file in photo_set.xml_files:
        
        # Extract IID from THIS xml
        iid = extract_iid_from_xml(xml_file)
        # e.g., "FSU_Cetamura_photos_19900711_15.5N18W_001"
        
        # Find matching JPG by filename stem
        matching_jpg = None
        for jpg_file in photo_set.jpg_files:
            if jpg_file.stem == xml_file.stem:
                # FSU_Cetamura_photos_19900711_15.5N18W_001.jpg
                # matches FSU_Cetamura_photos_19900711_15.5N18W_001.xml
                matching_jpg = jpg_file
                break
        
        # Create FilePair for THIS specific pair
        files = FilePair(
            xml=xml_file,
            jpg=matching_jpg,
            iid=iid
        )
        
        # Process THIS pair
        process_file_set_with_context(files, iid, photo_set.base_directory, context)

# Result: 6 photo sets → 19 files processed (all pairs!)
```

### Processing Example for One Photo Set:
```
Photo Set: 15.5N-18W (6 JPG + 6 XML files)

Iteration 1:
    xml_file: FSU_Cetamura_photos_19900711_15.5N18W_001.xml
    iid: FSU_Cetamura_photos_19900711_15.5N18W_001
    matching_jpg: FSU_Cetamura_photos_19900711_15.5N18W_001.jpg 
    → Process pair 1

Iteration 2:
    xml_file: FSU_Cetamura_photos_19900724_15.5N18W_001.xml
    iid: FSU_Cetamura_photos_19900724_15.5N18W_001
    matching_jpg: FSU_Cetamura_photos_19900724_15.5N18W_001.jpg 
    → Process pair 2

... (4 more iterations)

Iteration 6:
    xml_file: FSU_Cetamura_photos_19900727_15.5N18W_001.xml
    iid: FSU_Cetamura_photos_19900727_15.5N18W_001
    matching_jpg: FSU_Cetamura_photos_19900727_15.5N18W_001.jpg 
    → Process pair 6

Total for this photo set: 6 files processed
```

---

## 5. Individual File Processing

### For Each JPG/XML Pair:
```python
process_file_set_with_context(files, iid, subfolder, context)
    ↓
Step 1: Extract IID from XML
    extract_iid_from_xml(xml_file)
    → "FSU_Cetamura_photos_19900711_15.5N18W_001"
    
Step 2: Check Image Orientation
    validate_image_orientation(jpg_file)
    → Detects EXIF orientation (e.g., Rotate 90 CW)
    
Step 3a: If Dry Run
    Log: "DRY RUN: Would convert X to TIFF with orientation correction"
    Log: "DRY RUN: Would extract IID Y from Z"
    Log: "DRY RUN: Would create ZIP package for Y"
    Write to CSV: [IID, xml_path, jpg_path, 'SUCCESS', 'DRY_RUN', 'Would process...']
    ↓
    Return True
    
Step 3b: If Production
    convert_jpg_to_tiff(jpg_file)
        ↓
        Open JPG with PIL
        ↓
        Apply EXIF orientation correction
        ↓
        Save as TIFF
        ↓
        Delete original JPG
        ↓
        Return tiff_path
    
    rename_files(subfolder, tiff_path, xml_file, iid)
        ↓
        Sanitize IID for filename
        ↓
        Rename: FSU_Cetamura_photos_19900711_155N18W_001.tiff
        Rename: FSU_Cetamura_photos_19900711_155N18W_001.xml
    
    package_to_zip(tiff_path, xml_path, manifest_path, output_dir)
        ↓
        Create ZIP: FSU_Cetamura_photos_19900711_155N18W_001.zip
        ↓
        Add to ZIP:
            - .tiff file
            - .xml file
            - manifest.ini
        ↓
        Save to output directory
    
    Write to CSV: [IID, xml_path, jpg_path, 'SUCCESS', 'PACKAGED', 'Created ZIP']
    ↓
    Return True
```

---

## 6. Results and Reporting

### CSV Report Structure:
```csv
IID,XML_Path,JPG_Path,Status,Action,Notes
FSU_Cetamura_photos_19900711_15.5N18W_001,X:\...\001.xml,X:\...\001.jpg,SUCCESS,DRY_RUN,Would process successfully
FSU_Cetamura_photos_19900724_15.5N18W_001,X:\...\001.xml,X:\...\001.jpg,SUCCESS,DRY_RUN,Would process successfully
... (17 more rows)
SUMMARY,,,Success: 19,Errors: 0,Dry run: True
```

### Final Output:
```
Before Fix:
 6 photo sets found
 6 files processed (only first file from each set)
 13 files ignored

After Fix:
 6 photo sets found
 19 files processed (all files from all sets)
 0 files ignored
```

---

## 7. Output Directory Structure

### Dry Run:
```
X:\Cetamura\1990\1990\
 batch_report_20251003_120000.csv  (report only, no files changed)
```

### Production Run:
```
X:\Cetamura\1990\1990\
 output/
    FSU_Cetamura_photos_19900711_15.5N18W_001.zip
    FSU_Cetamura_photos_19900724_15.5N18W_001.zip
    FSU_Cetamura_photos_19900725_15.5N18W_001.zip
    ... (16 more ZIP files)
    batch_report_20251003_120000.csv
 15.5N-18W/
     FSU_Cetamura_photos_19900711_155N18W_001.tiff  (converted)
     FSU_Cetamura_photos_19900711_155N18W_001.xml   (renamed)
     ... (original JPGs deleted after conversion)
```

---

## Key Improvements from Fix

### Before:
-  Only 1 file per photo set processed
-  Multiple files silently ignored
-  Incomplete output
-  Users confused why files missing

### After:
-  ALL files in each photo set processed
-  Files matched by filename stem
-  Complete output with all files
-  Clear warnings if JPG/XML mismatch
-  Better logging showing file counts

---

---

## File System Interactions

### Input Requirements

**Directory Structure Example:**
```
X:\Cetamura\1990\1990\
 15.5N-18W/
    FSU_Cetamura_photos_19900711_15.5N18W_001.jpg
    FSU_Cetamura_photos_19900711_15.5N18W_001.xml
    FSU_Cetamura_photos_19900724_15.5N18W_001.jpg
    FSU_Cetamura_photos_19900724_15.5N18W_001.xml
    FSU_Cetamura_photos_19900725_15.5N18W_001.jpg
    FSU_Cetamura_photos_19900725_15.5N18W_001.xml
    manifest.ini
 18N-18W/
    (5 JPG/XML pairs)
    manifest.ini
 ... (more photo sets)
```

**File Naming Requirements:**
- JPG and XML must have **identical stems** to be matched
- Manifest must be named `manifest.ini` (case-insensitive)
- No strict naming format required, just matching stems

### Output Structure

**Dry Run:**
```
X:\Cetamura\1990\1990\
 batch_report_20251003_120000.csv  (report only)
```

**Production:**
```
X:\Cetamura\1990\1990\
 output/
    FSU_Cetamura_photos_19900711_155N18W_001.zip
    FSU_Cetamura_photos_19900724_155N18W_001.zip
    ... (one ZIP per processed file)
    batch_report_20251003_120000.csv
 15.5N-18W/
     FSU_Cetamura_photos_19900711_155N18W_001.tiff  (converted)
     FSU_Cetamura_photos_19900711_155N18W_001.xml   (renamed)
     ... (JPGs deleted after conversion)
     manifest.ini  (unchanged)
```

**Staging:**
```
X:\Cetamura\1990\1990\
 staging_output/
    (ZIPs here instead of output/)
    batch_report_20251003_120000.csv
 15.5N-18W/
     (original files unchanged)
```

---

## Error Handling & Recovery

### File-Level Errors (Non-Fatal)

These errors affect one file but don't stop the batch:

| Error Type | Cause | Behavior | CSV Entry |
|------------|-------|----------|-----------|
| MISSING_JPG | XML has no matching JPG | Log warning, skip file | WARNING, MISSING_JPG |
| MISSING_XML | JPG has no matching XML | Log warning, skip file | WARNING, MISSING_XML |
| ORPHANED_XML | XML processed but JPG is None | Skip file | WARNING, ORPHANED_XML |
| CONVERT_FAILED | JPG→TIFF conversion failed | Skip file | ERROR, CONVERT_FAILED |
| NO_MANIFEST | manifest.ini not found | Skip file | ERROR, NO_MANIFEST |
| INVALID_XML | XML parse error | Skip file | ERROR, INVALID_XML |

**Behavior:** Log error, write CSV row, increment error_count, continue to next file

### Photo Set-Level Errors (Non-Fatal)

These errors affect entire PhotoSet but don't stop the batch:

| Error Type | Cause | Behavior |
|------------|-------|----------|
| No JPG files | Directory has no .jpg files | Skip PhotoSet, log warning |
| No XML files | Directory has no .xml files | Skip PhotoSet, log warning |
| No valid IIDs | No XML files have `<identifier type="IID">` | Skip PhotoSet, log warning |
| Multiple manifests | More than one manifest.ini | Skip PhotoSet, log error |

### System-Level Errors (Fatal)

These errors stop the entire batch:

| Error Type | Cause | Behavior |
|------------|-------|----------|
| Permission denied | Can't read/write files | Catch exception, log traceback, return (0, 1, csv_path) |
| Disk full | No space for output | Catch exception, log traceback, return (0, 1, csv_path) |
| Invalid folder path | User selected non-existent folder | Show error dialog, don't start |

**Behavior:** Log full traceback, write ERROR row to CSV, return early

### Logging

**Two log files:**
1. **batch_tool.log** - Technical debug log (all messages)
2. **batch_process_summary.log** - User-friendly log (INFO and above)

**Log levels:**
- DEBUG: File discovery, validation details
- INFO: Processing steps, successful operations
- WARNING: Skipped files, missing matches
- ERROR: Failed operations, exceptions

---

## Performance Characteristics

### Typical Workload

**Small batch:**
- 3-5 photo sets
- 10-15 file pairs
- Processing time: 15-30 seconds (production)

**Medium batch:**
- 5-10 photo sets
- 15-30 file pairs
- Processing time: 30-60 seconds (production)

**Large batch:**
- 10+ photo sets
- 50+ file pairs
- Processing time: 2-5 minutes (production)

### Resource Usage

**Memory:**
- Base: ~50 MB (Python + GUI)
- Per file: ~5-10 MB (image processing)
- Peak: ~100-150 MB typical

**Disk I/O:**
- Read: Original JPG (full file)
- Write: TIFF (typically 2-3x JPG size)
- Write: ZIP (TIFF + XML + manifest)
- Delete: Original JPG after conversion

**CPU:**
- Light load during discovery
- Heavy load during JPG→TIFF conversion (PIL image processing)
- Light load during ZIP creation

### Optimization Notes

- Files processed sequentially (one at a time)
- No parallelization (Python GIL, simple implementation)
- Network drives slower than local (copy to local recommended)
- Dry-run is very fast (~1-2 seconds for 50 files)

---

## Testing & Validation

### Unit Tests

**Location:** `tests/test_main.py`

**Test Coverage:**
1. `test_find_photo_sets` - PhotoSet discovery
2. `test_convert_jpg_to_tiff` - Image conversion
3. `test_extract_iid_from_xml_namespaced` - IID extraction with namespace
4. `test_extract_iid_from_xml_non_namespaced` - IID extraction without namespace
5. `test_sanitize_name` - Name sanitization
6. `test_sanitize_name_cases` - Edge cases for sanitization
7. `test_rename_files` - File renaming logic
8. `test_package_to_zip` - ZIP creation
9. `test_full_workflow` - End-to-end integration

**Run tests:**
```bash
python -m pytest tests/ -v
```

**Expected result:** All 11 tests passing

### Manual Testing Checklist

**Before release:**
- [ ] Dry run with real data (verify CSV correct)
- [ ] Staging run (verify output folder correct)
- [ ] Production run (verify files converted/packaged)
- [ ] Test with missing JPG (verify warning logged)
- [ ] Test with missing XML (verify warning logged)
- [ ] Test with invalid XML (verify error handled)
- [ ] Test with multiple photo sets (verify all processed)
- [ ] Test with photo set containing multiple files (verify all processed)
- [ ] Check orientation correction on rotated images
- [ ] Verify ZIP contents match requirements

---


### DO NOT Make these Assumptions

1. **"FilePair contains multiple files"**
   - WRONG: FilePair has exactly ONE xml and ONE jpg
   - PhotoSet contains multiple files

2. **"Only one file per photo set gets processed"**
   - WRONG: ALL files in each photo set are processed (as of v2025.10.03)
   - Previous bug only processed first file, now fixed

3. **"PhotoSet and FilePair are the same thing"**
   - WRONG: PhotoSet = directory with ALL files, FilePair = single pair

4. **"manifest_file is a list"**
   - WRONG: PhotoSet.manifest_file is a single Path object
   - PhotoSet.jpg_files and xml_files are lists

5. **"Dry run creates output files"**
   - WRONG: Dry run creates ONLY CSV report, no other files

6. **"Files are processed in parallel"**
   - WRONG: Sequential processing only

7. **"ZIP contains multiple images"**
   - WRONG: One ZIP per image (1:1 ratio)

8. **"System connects to a database"**
   - WRONG: Purely filesystem-based, no database

### CORRECT Facts

1. PhotoSet contains **lists** of ALL files in directory
2. FilePair represents **one** JPG/XML pair
3. **Every** xml_file in PhotoSet creates a FilePair
4. Matching is by **filename stem** (case-sensitive)
5. Dry run changes **nothing** except creating CSV
6. Original JPG is **deleted** after TIFF conversion (production only)
7. One **ZIP per file**, not per PhotoSet
8. CSV has one row **per file processed**, plus summary row

---

## Version History & Known Issues

### v2025.10.03 (Current)
- Fixed: Process ALL files in each photo set (not just first)
- Fixed: 'tuple' object has no attribute 'iid' error
- Enhanced: Better error logging with tracebacks
- Added: XML file validation
- Updated: FilePair xml field now Optional[Path]

### v2025.09.19
- Bug: Only processed first file from each photo set
- Bug: AttributeError with tuple objects

### Known Limitations

1. **No parallel processing** - Sequential only
2. **Memory usage** - Large images require more RAM
3. **Network drives** - Slower than local drives
4. **Windows path lengths** - Deep nesting can cause issues
5. **No undo** - Production changes are permanent
6. **Case-sensitive matching** - Filename stems must match exactly

---

## Post-Processing Validation Architecture

### Overview
The validation system provides comprehensive post-processing verification to ensure outputs match expectations. It addresses critical gaps in output verification while maintaining backward compatibility.

### Validation Invariants
```python
# These conditions MUST hold after successful batch processing:
input_xml_count == csv_success_rows  # All files attempted were logged
csv_success_rows == actual_zip_count  # All successes created ZIPs
actual_zip_count == valid_zip_count   # All ZIPs are structurally valid
```

### Data Structures (src/validation.py)

#### ValidationResult (NamedTuple)
```python
class ValidationResult(NamedTuple):
    passed: bool                # True if validation succeeded
    expected_count: int         # Number of ZIPs expected (success_count)
    actual_count: int           # Number of ZIPs found on disk
    valid_zips: int             # Number of structurally valid ZIPs
    invalid_zips: List[str]     # List of invalid ZIP descriptions
    missing_count: int          # Difference: expected - valid
    errors: List[str]           # List of validation error messages
    warnings: List[str]         # List of validation warnings
```

#### ReconciliationReport (NamedTuple)
```python
class ReconciliationReport(NamedTuple):
    input_xml_count: int        # Total XML files in photo_sets
    csv_success_rows: int       # Number of CSV rows with status=SUCCESS
    actual_zip_count: int       # Number of .zip files found
    valid_zip_count: int        # Number of valid ZIPs (3 files each)
    discrepancies: List[str]    # List of count mismatches
    orphaned_files: List[str]   # _PROC files without corresponding ZIPs
```

#### PreFlightResult (NamedTuple)
```python
class PreFlightResult(NamedTuple):
    passed: bool                # True if no blockers found
    disk_space_gb: float        # Available disk space in GB
    required_space_gb: float    # Estimated space required
    orphaned_tiff_count: int    # Number of *_PROC.tif files
    orphaned_xml_count: int     # Number of *_PROC.xml files
    warnings: List[str]         # Non-blocking warnings
    blockers: List[str]         # Critical issues preventing processing
```

### Validation Functions

#### 1. verify_zip_contents(zip_path: Path) -> tuple[bool, list[str]]
**Purpose:** Validate individual ZIP file structure  
**Rules:**
- ZIP MUST contain exactly 3 files
- ZIP MUST contain one .tif or .tiff file
- ZIP MUST contain one .xml file
- ZIP MUST contain one manifest.ini file

**Returns:** `(is_valid, error_list)`

**Example:**
```python
is_valid, errors = verify_zip_contents(Path("output.zip"))
if not is_valid:
    for error in errors:
        logger.error(f"ZIP validation error: {error}")
```

#### 2. validate_batch_output(...) -> ValidationResult
**Purpose:** Post-processing validation of batch output  
**When:** After batch processing completes  
**Runs:** Non-blocking (logs warnings, doesn't raise exceptions)

**Logic:**
- Dry run: Verify NO ZIPs created
- Production: Verify expected_count == actual_count
- Validate each ZIP's contents
- Report discrepancies

**Integration Point:** End of `batch_process_with_safety_nets()` (src/main.py lines ~1120)

#### 3. generate_reconciliation_report(...) -> ReconciliationReport
**Purpose:** Reconcile input vs output counts  
**When:** After batch processing completes (non-dry-run only)  
**Checks:**
- Input XML count vs CSV SUCCESS rows
- CSV SUCCESS rows vs actual ZIP count
- Actual ZIP count vs valid ZIP count
- Orphaned *_PROC files without corresponding ZIPs

**Output:**
```
=== Reconciliation Report ===
Input XML files: 25
CSV SUCCESS rows: 25
Actual ZIP files: 25
Valid ZIP files: 25
No discrepancies found.
```

#### 4. pre_flight_checks(...) -> PreFlightResult
**Purpose:** Environment validation before processing starts  
**When:** Beginning of `batch_process_with_safety_nets()`  
**Runs:** BLOCKING (raises RuntimeError if critical issues found)

**Checks:**
- Disk space availability (blocks if insufficient)
- Write permissions to output directory (blocks if denied)
- Orphaned files from previous runs (warns)

**Integration Point:** Beginning of `batch_process_with_safety_nets()` (src/main.py lines ~992)

### Integration into Main Script

#### Pre-Flight Checks (Lines ~992-1007, src/main.py)
```python
from .validation import pre_flight_checks

prelim_photo_sets = find_photo_sets_enhanced(folder_path)
preflight = pre_flight_checks(prelim_photo_sets, output_dir)

if not preflight.passed:
    for blocker in preflight.blockers:
        logger.error(f"Pre-flight check failed: {blocker}")
    raise RuntimeError("Pre-flight checks failed. Aborting batch processing.")

for warning in preflight.warnings:
    logger.warning(f"Pre-flight warning: {warning}")
```

#### Post-Processing Validation (Lines ~1120-1180, src/main.py)
```python
from .validation import validate_batch_output, generate_reconciliation_report

validation_result = validate_batch_output(
    photo_sets=photo_sets,
    output_dir=output_dir,
    success_count=success_count,
    dry_run=dry_run
)

if not validation_result.passed:
    for error in validation_result.errors:
        logger.error(f"Validation error: {error}")
else:
    logger.info(f"[PASS] {validation_result.valid_zips} valid ZIPs")

if not dry_run:
    reconciliation = generate_reconciliation_report(
        photo_sets=photo_sets,
        csv_path=csv_path,
        output_dir=output_dir
    )
    # Log reconciliation results...
```

### Validation Guardrails

#### Non-Breaking Design
- Pre-flight checks CAN block processing (safety feature)
- Post-processing validation NEVER blocks (informational only)
- Validation runs in try/except blocks (failures logged, not raised)
- Dry run validation ensures NO ZIPs created
- Backward compatible (existing scripts work unchanged)

#### Failure Scenarios Detected
1. **Missing ZIPs:** success_count=25 but only 20 ZIPs found → ERROR logged
2. **Corrupted ZIPs:** ZIP file doesn't contain 3 required files → ERROR logged
3. **Disk full:** Pre-flight detects insufficient space → BLOCKS processing
4. **Orphaned files:** _PROC files without ZIPs → WARNING logged
5. **Dry run violation:** ZIPs created during dry run → ERROR logged

#### Expected Behavior
- **Normal operation:** All validation passes, no errors logged
- **Missing JPG:** XML skipped with WARNING, validation accepts discrepancy
- **Processing error:** Error logged, validation reports missing ZIP
- **Pre-flight failure:** Processing blocked before starting

### Validation Contracts

#### Contract 1: ZIP Structure
```python
# Every valid ZIP MUST satisfy:
len(zip.namelist()) == 3
any(f.endswith(('.tif', '.tiff')) for f in zip.namelist())
any(f.endswith('.xml') for f in zip.namelist())
'manifest.ini' in zip.namelist()
```

#### Contract 2: Count Reconciliation
```python
# After successful batch processing:
if success_count > 0:
    assert actual_zip_count == success_count, "ZIP count mismatch"
    assert valid_zip_count == actual_zip_count, "Invalid ZIPs found"
```

#### Contract 3: Dry Run Guarantee
```python
# Dry run MUST NOT create any files:
if dry_run:
    assert len(list(output_dir.glob("*.zip"))) == 0, "Dry run created ZIPs"
```

### Testing Coverage
See `tests/test_validation.py` for comprehensive test suite (27 tests):
- ZIP content verification (9 tests)
- Batch output validation (7 tests)
- Reconciliation reporting (5 tests)
- Pre-flight checks (6 tests)

---

## Glossary

**Photo Set:** A directory containing JPG images, XML metadata files, and a manifest.ini file. Represented by PhotoSet NamedTuple.

**FilePair:** A single JPG/XML pair to be processed. Represented by FilePair NamedTuple with xml, jpg, and iid fields.

**IID:** Identifier extracted from XML `<identifier type="IID">` tag. Used for file naming.

**Batch Context:** Configuration object passed to processing functions containing dry_run, staging, logger, etc.

**Dry Run:** Preview mode where no files are created/modified. Only CSV report generated.

**Staging:** Output to staging_output/ folder instead of output/, leaving originals unchanged.

**Production:** Actual processing mode where files are converted, renamed, and packaged.

**Stem:** Filename without extension (e.g., "file.jpg" → "file")

**PhotoSet Discovery:** Process of finding and validating photo sets in directory tree.

**File Matching:** Algorithm to pair JPG and XML files by filename stem.

---

## Quick Reference

### Key File Locations

| Component | File | Lines |
|-----------|------|-------|
| FilePair definition | src/main.py | 42-46 |
| PhotoSet definition | src/main.py | 48-55 |
| BatchContext definition | src/main.py | 57-63 |
| File discovery | src/main.py | 267-299 |
| Photo set validation | src/main.py | 410-438 |
| Photo set finder | src/main.py | 471-530 |
| Batch processing loop | src/main.py | 1020-1069 |
| File processing | src/main.py | 878-948 |
| JPG→TIFF conversion | src/main.py | 699-735 |
| ZIP packaging | src/main.py | 854-875 |
| GUI main | src/main.py | 1290-1445 |

### Key Constants

```python
MAX_SEARCH_DEPTH = 5  # Recursive search limit
VALID_IMAGE_EXTENSIONS = ['.jpg', '.jpeg']  # Case-insensitive
MANIFEST_FILENAME = 'manifest.ini'  # Case-insensitive
MODS_NAMESPACE = 'http://www.loc.gov/mods/v3'
```

---
## Documentation Style Guidelines

**NO EMOJIS RULE:** All documentation in this project must be written without emojis. This ensures:
- Professional appearance
- Better accessibility (screen readers)
- Consistent rendering across all platforms
- Clear, distraction-free technical documentation
- Long-term readability and maintainability

Use clear headings, bullet points, and formatting instead of decorative symbols.

---

**END OF REQUIREMENTS DOCUMENT**

*This document is the authoritative source of truth for the Cetamura Batch Ingest Tool. When in doubt, refer to this document first, then verify against actual code.*

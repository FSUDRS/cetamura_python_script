# PRODUCTION RELEASE - SAFETY NET VERSION
## Cetamura Batch Ingest Tool v2024.08.19

This release includes comprehensive safety net improvements that make the Cetamura Batch Ingest Tool production-ready with enhanced safety, reliability, and user experience.
## **Cetamura Batch Ingest Tool — v2025.08.25-c9fe170**
**Safe Batch Processing — Dry‑Run, Staging & CSV Reporting**

This release delivers production-focused safety and reliability improvements for the Cetamura Batch Ingest Tool. It introduces non-destructive processing modes, detailed CSV reporting, a user-friendly Processing Options dialog, and improvements to error handling and file-pairing/configuration management.

---

## **IMPROVEMENTS**

### **UX and Usability**
- Improved folder selection with photo-set validation
- Status feedback for folder validation results
- **"View Log File"** menu option for convenient log access
- Cross-platform log viewing
- Clear success messages showing output directory and results

### **Manifest and Validation**
- Single-manifest enforcement with **validate_single_manifest()** and clear error messages
- Graceful handling and reporting for missing or multiple manifests
- Tight integration with batch processing workflow to prevent invalid runs

### **Safety and Processing Features**
- **Dry-Run Mode:** preview processing without making file changes
- **Staging Mode:** write outputs to staging directories to preserve originals
- **CSV Reporting:** detailed processing logs with timestamps and audit information
- **Processing Options Dialog:** user-friendly mode selection and configuration interface
- **Enhanced Error Handling:** graceful failures with clear error messages and logs
- **FilePair & BatchContext:** robust file pairing and centralized processing configuration

---

## **KEY PRODUCTION BENEFITS**

### **Safety and Reliability**
- Risk-free validation using **Dry‑Run mode** before any file modification
- Non-destructive workflows via **Staging mode**
- Pre-processing validation reduces failed runs and data risk
- Clear failure reporting and recovery guidance

### **Operational & Auditing**
- **CSV reports** provide an audit trail for processing steps and timestamps
- Status feedback and logs improve troubleshooting and operator confidence
- Cross-platform compatibility for Windows, macOS, and Linux

### **User Experience**
- Intuitive **Processing Options dialog** reduces setup errors
- Clear UI messages and direct log access improve operator efficiency
- Minimal training required for safe operation

---

## **DEPLOYMENT OPTIONS**

**Option 1  Pre-built Executable (recommended)**
- Use a pre-built executable if you have created one via the build scripts or CI artifacts (example name: `Cetamura_Batch_Tool_Windows.exe`).
- Copy to target systems and run without Python installed. Note: pre-built executables are not stored in the repository HEAD; build them locally or obtain them from CI release artifacts.

**Option 2  Python Source**
- Use: `src/main.py`
- Install dependencies: `pip install -r requirements/requirements.txt`
- Run: `python src/main.py`

**Option 3 — Custom Build**
- Run the provided build scripts:
	- Windows: `scripts/build/build_exe.ps1`
	- macOS: `scripts/build/build_exe_macos.sh`
	- Cross-platform helper: `scripts/build/build_cross_platform.sh`
- Produces a self-contained executable (example: `Cetamura_Batch_Tool_SafetyNet.exe`)

---

## **DEPLOYMENT INSTRUCTIONS**

### **Windows (Quick Deployment)**
- If you have a pre-built executable, copy it to the target system and run it. Otherwise run the tool from source:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements/requirements.txt; python src/main.py
```
- Use **Dry Run** mode to test with sample data
- Deploy to production once validated

### **macOS / Linux (Source Deployment)**
1. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run the application:
```bash
python src/main.py
```
Notes:
- Building native executables for macOS or Linux generally requires running the packaging tools on the target OS or in a compatible CI runner.
- Use `scripts/build/build_exe_macos.sh` on macOS or `scripts/build/build_cross_platform.sh` in CI to produce native artifacts.

### **Custom Build and Packaging Notes**
- For macOS distributed binaries, codesigning and notarization may be required for wide distribution.
- For Linux, package using the preferred format for your environment (AppImage, snap, deb, rpm) or distribute the source.
- Continuous Integration (GitHub Actions) is recommended to build and publish platform-specific artifacts automatically.

---

## **DEPLOYMENT INSTRUCTIONS (Network / Admin)**
- Place the executable or source on a shared location and create shortcuts for users.
- Provide quick training on safety features (Dry-Run, Staging).
- Monitor CSV reports centrally for analytics and audit.

---

## **PRODUCTION VALIDATION CHECKLIST**

- Dry-Run mode implemented and tested
- Staging mode implemented and tested
- CSV reporting implemented for audit trails
- Manifest and file structure validation added
- Processing Options dialog implemented
- Enhanced error handling and logging in place
- Cross-platform behavior validated
- Backward compatibility preserved

---

## **SUPPORT & TROUBLESHOOTING**

**For users:**
- Start with **Dry-Run mode** to validate datasets
- Check **CSV reports** for detailed process logs
- Review `batch_tool.log` for system-level diagnostics
- Contact IT support for file access or environment issues

**For administrators:**
- CSV logs are stored in the application output directory
- Staging mode provides a safe workflow for review prior to finalizing outputs
- No external database required; the tool is self-contained

---

**Version**: v2025.08.25-c9fe170
**Build Date**: August 25, 2025


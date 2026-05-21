---
name: manage-updates
description: Playbook for release preparation, version bumping, compiling standalone Windows packages with PyInstaller, generating SHA256 release checksums, and testing update/rollback client simulations. Use when preparing a new version release or when modifying update pipeline code.
---

# Manage Updates and Release Playbook

This playbook provides a detailed technical guide for versioning, compiling, and testing releases for the Gas Flow Calc desktop application.

---

## Step 1 — Semantic Versioning & Pre-release Auditing

A strict release procedure ensures that releases are clean, traceable, and fully tested.

### 1. Pre-release Checklists
Before changing version numbers:
- **Test Gate**: Ensure the complete QA test suite passes:
  ```powershell
  python -m pytest tests/ -v
  ```
- **Uncommitted Files**: Confirm `git status` shows a clean workspace. Do not build with uncommitted or untested debug changes.
- **Physical Validation**: Manually run at least one reference `Sm³/h` scenario and one `kg/s` scenario on the current codebase, checking that the output matches known standard thermodynamic calculations.

### 2. Version Bump Action
- Update version strings in `release_metadata.py`:
  - `APP_VERSION = "MAJOR.MINOR.PATCH"`
  - `BUILD_DATE = "YYYY-MM-DD"`
- Document all fixes, new features, and changes in `CHANGELOG.md` using standard Keep a Changelog conventions.

---

## Step 2 — PyInstaller Standalone Windows Compilation

Packaging a desktop app requires ensuring all binary dependencies are self-contained.

### 1. Bundling Windows SSL Libraries
Standalone execution environments on Windows might lack standard Python or SSL runtimes.
Verify that `Gas Flow Calc V6.1.spec` bundles the following:
- **DLLs**: `_ssl.pyd`, `libssl-3.dll`, `libcrypto-3.dll` (usually located in Python's DLL directory).
- **Hidden Imports**: Ensure `CoolProp`, `Pillow`, `win32crypt`, `app_paths`, and `constants` are listed under `hiddenimports` if they are imported dynamically or through custom modules.
- **Data Files**: Check that translations or config assets are bundled correctly.

### 2. Executable Packaging Execution
Run the compiler from the project directory:
```powershell
pyinstaller "Gas Flow Calc V6.1.spec" --clean
```
Confirm the build succeeds and generates a standalone executable under `dist/`.

---

## Step 3 — SHA256 Checksum Signature Generation

To prevent man-in-the-middle attacks or corrupt downloads, every update requires a verified hash.

### 1. Hash Calculation
Calculate the SHA256 checksum of the compiled executable or ZIP package:
- **Windows**: `CertUtil -hashfile dist/GasFlowCalc.exe SHA256`
- **macOS / Linux**: `shasum -a 256 dist/GasFlowCalc.exe`

### 2. Release Signature Injecting
Add the computed checksum inside the GitHub Release body using the exact required regex format:
```
SHA256: <64-character-hex-checksum>
```
The updater's parsing method (`_parse_sha256_from_body` inside `updater.py`) looks for this line to verify download integrity.

---

## Step 4 — Client Simulation & Rollback Verification

The updater must fail gracefully and protect the user's local files in case of network disruptions.

### 1. Fake Update Verification
- Configure a local mock JSON release source or set `private_repo: False` in `config.json` with temporary repo targets to test the client's update detection.
- Simulate an update check while keeping SSL disabled or uninstalled, verifying that `updater.py` transitions smoothly to standard OS-level fallback commands.

### 2. Backup and Rollback Testing
- Initiate a fake update process.
- **Interruption Injection**: Simulate a power/network failure or inject a corrupt zip archive.
- **Expected Behavior**: Verify that the updater detects the checksum mismatch or file extraction error, halts execution, preserves the created backup, and restores the original system state without losing local user settings or `config.json`.

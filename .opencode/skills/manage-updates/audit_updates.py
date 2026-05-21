#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Release & Updates Compliance Auditor
Verifies application version metadata matches release docs, and checks PyInstaller spec for essential configurations.
"""

import os
import re
import sys

def get_app_version():
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    metadata_path = os.path.join(workspace_dir, "release_metadata.py")
    
    if not os.path.exists(metadata_path):
        print(f"[!] release_metadata.py not found at: {metadata_path}")
        return None

    # Add to path to load or use regex
    with open(metadata_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.search(r"APP_VERSION\s*=\s*['\"]([^'\"]+)['\"]", content)
    if match:
        return match.group(1)
    return None

def audit_version_docs(app_version):
    if not app_version:
        print("[FAIL] Could not resolve app version from release_metadata.py")
        return False

    print(f"[*] Auditing documentation alignment for Version {app_version}...")
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    
    docs_to_check = ["CHANGELOG.md", "RELEASE.md"]
    success = True
    
    for doc in docs_to_check:
        doc_path = os.path.join(workspace_dir, doc)
        if not os.path.exists(doc_path):
            print(f"[WARN] Optional release document '{doc}' is missing.")
            continue
            
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if app_version in content:
            print(f"[PASS] Version {app_version} is mentioned in '{doc}'.")
        else:
            print(f"[FAIL] Version {app_version} is NOT mentioned in the latest entries of '{doc}'.")
            success = False
            
    return success

def audit_pyinstaller_spec():
    print("\n[*] Auditing PyInstaller .spec file configurations...")
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    
    spec_files = [f for f in os.listdir(workspace_dir) if f.endswith(".spec")]
    if not spec_files:
        print("[WARN] No PyInstaller .spec file found in root workspace directory.")
        return True

    spec_path = os.path.join(workspace_dir, spec_files[0])
    print(f"[*] Inspecting spec file: {spec_files[0]}")
    
    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for critical imports/files
    critical_terms = ["libssl", "libcrypto", "CoolProp", "hiddenimports"]
    found = [t for t in critical_terms if t in content]
    
    print(f"[INFO] Found configured compilation dependencies: {found}")
    
    if "CoolProp" not in content:
        print("[WARN] CoolProp is not explicitly referenced in spec. Ensure it is resolved implicitly or add to hiddenimports.")
    else:
        print("[PASS] CoolProp configuration confirmed in spec.")
        
    if "libssl" not in content and "_ssl" not in content:
        print("[WARN] SSL DLLs (libssl / _ssl) are not explicitly bundled in spec. This may cause updater issues on standalone PCs.")
    else:
        print("[PASS] SSL configuration confirmed in spec.")
        
    return True

if __name__ == "__main__":
    v = get_app_version()
    docs_ok = audit_version_docs(v)
    spec_ok = audit_pyinstaller_spec()
    
    if docs_ok and spec_ok:
        print("\n[SUCCESS] Release & Updates audit completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAILED] Release & Updates alignment checks failed.")
        sys.exit(1)

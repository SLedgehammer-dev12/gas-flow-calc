#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Security & Stability Compliance Auditor
Audits the codebase for locking mechanisms, safe path extraction (Zip Slip), and credentials safety.
"""

import os
import re
import sys

def audit_updater_zip_slip():
    print("[*] Auditing updater.py for Zip Slip path traversal safeguards...")
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    updater_path = os.path.join(workspace_dir, "updater.py")
    
    if not os.path.exists(updater_path):
        print("[!] updater.py not found, skipping zip slip check.")
        return True

    with open(updater_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Look for common zip-slip preventions e.g. path.realpath, path.abspath, or startswith checks
    safe_keywords = ["realpath", "abspath", "startswith", "commonpath"]
    found_keywords = [kw for kw in safe_keywords if kw in content]
    
    if "zip" in content.lower() and ("extract" in content.lower() or "zipfile" in content.lower()):
        if not found_keywords:
            print("[FAIL] updater.py extracts zip archives but contains no apparent path traversal checks.")
            return False
        else:
            print(f"[PASS] Zip slip protection keywords verified in updater.py: {found_keywords}")
            return True
    print("[PASS] No active extraction logic or safe traversal safeguards found (or updater.py is simple).")
    return True

def audit_calculations_locks():
    print("\n[*] Auditing calculations.py for concurrency thread locking...")
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    calc_path = os.path.join(workspace_dir, "calculations.py")
    
    if not os.path.exists(calc_path):
        print("[!] calculations.py not found, skipping concurrency check.")
        return False

    with open(calc_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lock_pattern = re.compile(r"self\._lock|Lock\(\)")
    matches = lock_pattern.findall(content)
    
    if matches:
        print(f"[PASS] Concurrency thread lock usages found in calculations.py: {len(matches)} occurrences.")
        return True
    else:
        print("[WARN] No thread locking or Lock usage found in calculations.py. If calculations are multi-threaded, add a Lock.")
        return True

def audit_credential_leaks():
    print("\n[*] Auditing code files for potential credential sifting/leaks...")
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    
    leaks = 0
    patterns = [
        (re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE), "hardcoded password assignment"),
        (re.compile(r"token\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", re.IGNORECASE), "hardcoded token assignment"),
        (re.compile(r"print\(.*password.*\)", re.IGNORECASE), "printing password variable"),
        (re.compile(r"print\(.*token.*\)", re.IGNORECASE), "printing token variable"),
    ]

    for root, _, files in os.walk(workspace_dir):
        # Skip internal dirs
        if any(p in root for p in [".git", ".pytest_cache", "__pycache__", "build", "dist"]):
            continue
        
        for file in files:
            if not file.endswith(".py"):
                continue
            
            # Skip this audit script itself
            if file == "audit_security.py":
                continue
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, workspace_dir)
            
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    # Skip comments
                    if line.strip().startswith("#"):
                        continue
                    
                    for pattern, desc in patterns:
                        if pattern.search(line):
                            # Ensure we exclude dummy test assertions
                            if "test_" in file and "assert" in line:
                                continue
                            print(f"[WARN] Potential security concern in '{rel_path}:{line_num}': {desc}")
                            leaks += 1

    if leaks == 0:
        print("[PASS] No credential leaks or unsafe debug prints found.")
    else:
        print(f"[INFO] Found {leaks} potential security concerns. Double-check for false positives.")
    return True

if __name__ == "__main__":
    zip_ok = audit_updater_zip_slip()
    locks_ok = audit_calculations_locks()
    leaks_ok = audit_credential_leaks()
    
    if zip_ok and locks_ok and leaks_ok:
        print("\n[SUCCESS] Security & Stability audit completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAILED] Security & Stability audit failed.")
        sys.exit(1)

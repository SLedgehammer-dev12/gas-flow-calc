#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UX & Guidance Compliance Auditor
Verifies translation keys match perfectly between languages and checks for hardcoded user-facing strings in UI code.
"""

import os
import re
import sys

def audit_translations():
    print("[*] Auditing translations.py...")
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
    try:
        from translations import TRANSLATIONS
    except ImportError as e:
        print(f"[!] Failed to import translations.py: {e}")
        return False

    tr_keys = set(TRANSLATIONS.get("tr", {}).keys())
    en_keys = set(TRANSLATIONS.get("en", {}).keys())

    missing_in_en = tr_keys - en_keys
    missing_in_tr = en_keys - tr_keys

    success = True
    if missing_in_en:
        print(f"[FAIL] Keys in 'tr' but missing in 'en': {sorted(list(missing_in_en))}")
        success = False
    if missing_in_tr:
        print(f"[FAIL] Keys in 'en' but missing in 'tr': {sorted(list(missing_in_tr))}")
        success = False

    if success:
        print(f"[PASS] Translations are fully synchronized! Count: {len(tr_keys)} keys per language.")
    return success

def audit_ui_hardcoded_strings():
    print("\n[*] Auditing UI panels for hardcoded user-facing strings...")
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    ui_dir = os.path.join(workspace_dir, "ui")
    
    if not os.path.exists(ui_dir):
        print(f"[!] UI directory not found at: {ui_dir}")
        return True

    # Pattern to look for potential hardcoded strings in labels or titles
    # e.g., text="Basınç" or text='Pressure' instead of t('key')
    hardcoded_pattern = re.compile(r'text\s*=\s*["\']([^"\'{}]+)["\']')
    
    exclusions = {"", " ", "x", "y", "w", "h", "+", "-", "*", "/", "=", "NPS", "Schedule"}
    found_issues = 0

    for root, _, files in os.walk(ui_dir):
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, workspace_dir)
            
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    # Skip comments
                    if line.strip().startswith("#"):
                        continue
                    
                    matches = hardcoded_pattern.findall(line)
                    for match in matches:
                        match_clean = match.strip()
                        # Simple heuristics to exclude formatting, empty strings, variable references
                        if match_clean not in exclusions and not match_clean.isnumeric() and len(match_clean) > 2:
                            # Skip if it is obviously not user-facing (like grid parameters or internal flags)
                            if "t(" in line or "translations.t(" in line:
                                continue
                            print(f"[WARN] Potential hardcoded string in '{rel_path}:{line_num}': text=\"{match_clean}\"")
                            found_issues += 1

    if found_issues == 0:
        print("[PASS] No hardcoded user-facing strings detected in UI panel files.")
    else:
        print(f"[INFO] Found {found_issues} potential hardcoded string occurrences. Consider using translations.t().")
    return True

if __name__ == "__main__":
    t_ok = audit_translations()
    ui_ok = audit_ui_hardcoded_strings()
    
    if t_ok and ui_ok:
        print("\n[SUCCESS] UX & Translation Compliance audit passed!")
        sys.exit(0)
    else:
        print("\n[FAILED] Compliance checks failed. Please fix key mismatches.")
        sys.exit(1)

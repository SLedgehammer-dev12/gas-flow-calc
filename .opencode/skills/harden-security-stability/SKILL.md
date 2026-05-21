---
name: harden-security-stability
description: Playbook for auditing, enforcing, and resolving issues related to application security (DPAPI, password hashes, credentials storage, zip slip path traversals, TLS/HTTPS, OS sandboxes) and stability (Tkinter exception boundaries, threading locks, cache races, CoolProp overflows, and division-by-zero). Use during security audits or when resolving application crash bugs.
---

# Harden Security and Stability Playbook

This playbook provides a detailed technical guide for auditing, securing, and stabilizing the Gas Flow Calc application.

---

## Step 1 — Cryptographic Credentials & Local Storage Security

Passwords and network tokens must never be stored in plain text or exposed in logs.

### 1. Verification of DPAPI & XOR Fallback
Check `updater.py` and `auth.py` for token/password persistence:
- **DPAPI Enforcement**: Ensure Windows DPAPI (`win32crypt`) is utilized for local machine encryption of sensitive keys (such as `github_token` or saved session tokens).
- **Secure Fallback**: If DPAPI is not available (e.g. non-Windows OS or missing libraries), verify that the credentials are not saved in plaintext. Use a cryptographically secure key or dynamic salt combined with safe obfuscation (like dynamic XOR bytes) to prevent raw disk inspection.
- **Password Strength**: Passwords must be hashed using PBKDF2-SHA256 with a minimum of $200,000$ iterations. Never store plain text passwords in variables or database entries. Use `StringVar` carefully and wipe them from memory when no longer needed.

---

## Step 2 — Zip Slip & Path Traversal Mitigation

During update extraction, malicious zip files could try to overwrite system directories.

### 1. Extract Verification Rules
Verify the zip extraction logic in `updater.py` (specifically inside `apply_update_from_zip`):
- **Path Resolution**: Resolve all zip entry paths using `os.path.abspath` and `os.path.realpath`.
- **Sandbox Boundary Check**: Ensure every target extraction path starts with the absolute directory path of the extraction folder. Block execution and raise an exception if a zip entry points outside the temporary extraction directory.
```python
tmp_root_abs = os.path.abspath(tmp_root)
target_path = os.path.abspath(os.path.join(tmp_root, entry.filename))
if not target_path.startswith(tmp_root_abs + os.sep) and target_path != tmp_root_abs:
    raise RuntimeError("Path Traversal attack blocked!")
```

---

## Step 3 — TLS/HTTPS Certification & Connection Fallback

Network updates must use secure protocols while maintaining resilience against enterprise proxy networks.

### 1. Verification of SSL/TLS Enforceability
- All URLs must explicitly specify `https://`.
- Under no circumstance should `verify=False` or SSL certificate validation be deactivated.

### 2. Standard OS-level Fallbacks (Windows PowerShell Hook)
If Python's internal OpenSSL runtime is missing or fails due to corporate proxy certificate chains:
- **Secure Fallback**: Transition the request to use the OS's native TLS layer (via `powershell Invoke-WebRequest`). Native OS layers automatically validate certificates against the Windows Certificate Store, which often contains corporate CA root certificates that Python's bundled certs lack.
- **Log warning**: Output a clear warning in the log panel explaining that a system fall-back was executed to bypass Python's cert store limitations while maintaining secure OS verification.

---

## Step 4 — Thread Concurrency & Cache Safety

High-intensity calculations running in parallel threads must be synchronized.

### 1. Composition-Aware Cache Lock
Check the thermodynamic cache in `calculations.py`:
- **Cache Thread Safety**: Ensure all cache lookup and cache insert operations utilize a robust `threading.Lock()` or `threading.RLock()`.
- **Hash Stability**: Verify that the cache keys are based on stable gas compositions (composition lists must be sorted or converted to immutable sorted tuples before hashing) to avoid race conditions or mismatched retrieval.
- **LRU Eviction Bounds**: Enforce maximum cache bounds to prevent memory leaks during long-running sessions.

---

## Step 5 — Exception boundaries & Tkinter Crash Prevention

Unhandled exceptions in background threads must never crash the desktop application.

### 1. Global Thread Exception Hook
Implement a global hook to capture unhandled background thread exceptions and report them gracefully in the UI instead of silently exiting:
```python
import sys
import threading

def custom_excepthook(args):
    # Log the thread crash
    print(f"Thread error: {args.exc_type} - {args.exc_value}", file=sys.stderr)
    # Notify UI thread safely via thread-safe queue

threading.excepthook = custom_excepthook
```

### 2. Numerical Calculation Safeguards
Ensure `calculations.py` executes defensive numerical checks before entering CoolProp equations:
- **Division-by-Zero Checks**: Confirm that variables like density, viscosity, or diameter ($D_m$) are greater than zero before performing division.
- **Convergence Guardrails**: Set strict iteration limits on friction factor formulas (Colebrook-White) and binary length searches to prevent infinite loops or CPU exhaustion.
- **Phase Continuity Catch**: Gracefully catch CoolProp-specific exceptions (e.g. out of boundary errors) and fall back to Peng-Robinson or Soave-Redlich-Kwong equations rather than crashing the calculation thread.

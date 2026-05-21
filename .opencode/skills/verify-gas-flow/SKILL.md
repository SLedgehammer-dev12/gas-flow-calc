---
name: verify-gas-flow
description: Run all Gas Flow Calc tests, validate fixes, and verify code quality. Use after making changes to verify nothing broke. Use when the user says test, verify, validate, check, run tests, or after any code modification. Gate: all 37 tests must pass before any change is considered complete.
---

# Verify Gas Flow Calc

Run tests and validate the Gas Flow Calc project health at `D:\İş\Çalışan programlar\@Güncelleme\Gas Flow Calc\gas-flow-calc-main`.

## Step 1 — Run All Tests

```powershell
Set-Location -LiteralPath "D:\İş\Çalışan programlar\@Güncelleme\Gas Flow Calc\gas-flow-calc-main"
python -m pytest tests/ -v --tb=short
```

**Requirements:** CoolProp must be installed. Tkinter must be available (Windows default).

**Expected:** 37 tests collected, ALL passed.

## Step 2 — Analyze Failures

If any test fails, identify the root cause:

| Test file | Responsible agent |
|-----------|-------------------|
| `test_calculations.py` | Calculation Agent |
| `test_coolprop_compat.py` | Calculation Agent |
| `test_flow_unit_regression.py` | Calculation Agent |
| `test_reporting.py` | UI Agent |
| `test_reporting_helpers.py` | UI Agent |
| `test_ui_defaults.py` | UI Agent |
| `test_auth.py` | Primary Agent |
| `test_updater_ssl.py` | Primary Agent |
| `test_updater_public_token_fallback.py` | Primary Agent |

**Common failure patterns:**
- `AttributeError: 'GasFlowCalculator' object has no attribute 'X'` → method was accidentally deleted during an edit. Read calculations.py and restore the missing method.
- `NameError: name 'X' is not defined` → module-level constant was deleted. Check for PHASE_LABEL_*, WARN_*, FORMULA_LABEL_*, `cp_propssi`, `cp_abstract_state`, `solve_cubic`.
- `AssertionError` → the code behavior changed; verify if change is intentional. If intentional, update the test. If unintentional, revert the change.
- Test skipped (`SKIP`) → Tk not available or test marked as skip.

## Step 3 — Quick Smoke Validation

After tests pass, verify these sanity checks:

```python
python -c "from calculations import GasFlowCalculator; c = GasFlowCalculator(); print(c.normalize_gas_name('METHANE'))"
# Expected: Propane (or whatever the canonical name is)

python -c "from calculations import solve_cubic; roots = solve_cubic(-6, 11, -6); print(sorted(roots))"
# Expected: [1.0, 2.0, 3.0] (cubic x³-6x²+11x-6=0)

python -c "import sys; sys.path.insert(0, '.'); from auth import is_first_run; print('auth OK')"
# Expected: auth OK

python -c "import sys; sys.path.insert(0, '.'); from constants import R_J_MOL_K, STD_PRESSURE_PA; print(R_J_MOL_K, STD_PRESSURE_PA)"
# Expected: 8.314462618 101325.0
```

## Step 4 — Report Status

Return exactly:
```
Tests: X/Y passed
Smoke checks: OK / FAILED (detail)
Gate: PASS (all tests + smoke) / BLOCKED (list failures)
```

## Rules

- NEVER proceed to next step if tests fail.
- NEVER change a test just to make it pass unless the test expectation is physically incorrect.
- If a method was accidentally deleted, reconstruct it from the file's method list and the call sites.
- The `.gitignore` contains `test_*.py` — new test files must be explicitly added with `git add -f`.
- Skip UI tests (`test_ui_defaults.py`) in CI/headless environments with `-k "not test_ui_defaults"`.

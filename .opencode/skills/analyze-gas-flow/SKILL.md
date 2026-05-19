---
name: analyze-gas-flow
description: Deeply analyze the Gas Flow Calc project across all dimensions: security, architecture, code quality, testing coverage, performance, error handling, dependencies, maintainability, type safety, concurrency. Returns prioritized findings with file:line references. Use when the user asks to analyze, review, audit, examine, or investigate the codebase. Use ONLY for this project (Gas Flow Calc at gas-flow-calc-main/). Produces a structured report with HIGH/MEDIUM/LOW severity ratings.
---

# Analyze Gas Flow Calc

Perform a comprehensive software engineering analysis of the Gas Flow Calc project at `D:\İş\Çalışan programlar\@Güncelleme\Gas Flow Calc\gas-flow-calc-main`.

## Analysis Dimensions

Run the following analyses in parallel. For each, return findings with file path, line numbers, severity (CRITICAL/HIGH/MEDIUM/LOW), and actionable description.

### 1. Security Analysis
- Read `auth.py` — check password hashing (PBKDF2-SHA256, 200k iterations), brute-force protection (both program AND admin prompts), `time.sleep()` GUI blocking, password in memory (StringVar), DPAPI token encryption
- Read `updater.py` — check TLS enforcement, hash verification (`_verify_file_hash` with `expected_sha256`), zip path traversal protection, DPAPI token storage, certificate validation
- Read `main.py` — check for `eval`/`exec`, process restart via `os.execl`, file dialog path safety, session file cleanup
- Read `app_paths.py` — config file permissions, legacy path handling, plaintext sensitive data
- Check all network URLs use `https://`

### 2. Architecture Analysis
- Read EVERY source file (skip tests/) — map the dependency graph, find circular imports
- Identify God classes (main.py >1750 lines, calculations.py >1600 lines)
- Check layer separation: UI strings in business logic? Calculation logic in UI?
- Verify `controllers.py` is actually wired in (it is now, as of Step 5)
- Check panel-to-app coupling (all panels receive full `app` object)
- Module-level mutable state (`_current_lang`, `_GAS_NAME_LOOKUP`)
- Error handling patterns: raise vs return error dict vs log+default — are they consistent?

### 3. Code Quality Analysis
- PEP 8 violations: line length, blank lines, import order
- Duplication: `validate_inputs`/`collect_inputs` (deprecated but still in main.py), pressure/temperature unit conversions, gas UI creation code
- Method complexity: >100 line methods, >3 level nesting, >5 parameters
- Dead code: `validate_inputs`, `collect_inputs`, `convert_pressure_to_pa` in main.py, unused imports
- Type safety: missing type hints, dict key access without `.get()`, potential KeyError
- String handling: hardcoded Turkish strings outside translations.py, magic strings vs constants/enums
- Error-prone patterns: bare `except Exception: pass`, mutable defaults, NoneType propagation risk

### 4. Testing Analysis
- Coverage gaps: which modules have NO tests? (format_utils, app_paths, controllers, constants, etc.)
- Edge cases tested: division by zero, negative values, empty inputs, missing dict keys?
- Test isolation: shared state in `test_ui_defaults.py`, `updater.ssl` mutation, mock over-engineering in `test_flow_unit_regression.py`
- Infrastructure: no `conftest.py`, no `pytest.ini`, mixed pytest/unittest styles, `.gitignore` hides `test_*.py`
- CI readiness: no GitHub Actions, no coverage config, `pytest` missing from `requirements.txt`

### 5. Performance Analysis
- CoolProp call count per calculation (pressure_drop: ~200-500, max_length: ~5000+)
- Cache effectiveness: composition-aware clearing (Step 2), key precision (100 Pa / 0.01 K)
- Redundant phase detection across segments (33% unnecessary)
- Binary search in `calculate_max_length` (40-50 outer iterations, each calling full pressure drop)
- `_triple_point_cache` effectiveness
- Startup time: CoolProp import (~100-300ms), numpy replaced with Cardano, UI initialization
- Thread safety: cache lock, queue communication, `_cache_put` LRU eviction

## Output Format

For each finding, produce a line with:
```
SEVERITY | File:line | Category | Finding description
```

Group findings by dimension. End with a summary table:

| Dimension | CRITICAL | HIGH | MEDIUM | LOW |
|-----------|----------|------|--------|-----|
| Security | - | - | - | - |
| Architecture | - | - | - | - |
| ... | | | | |

Then provide a **Top 10 Priority Actions** list ordered by severity and impact.

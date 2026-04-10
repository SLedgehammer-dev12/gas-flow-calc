# TASKS

## Active Tracks

### 1. Updater Network Hardening

Goal:

- GitHub update checks should work or fail clearly on corporate Windows networks.

Files:

- `updater.py`
- `main.py`
- `tests/`

### 2. UI Consistency Cleanup

Goal:

- Startup defaults, segmented buttons, and loaded project state should always match.

Files:

- `main.py`
- `ui/panels/process_panel.py`
- `tests/test_ui_defaults.py`

### 3. Test Coverage Expansion

Goal:

- Add regression safety around updater behavior and UI defaults.

Files:

- `tests/`

## Suggested Order

1. Updater diagnostics and fallback safety
2. UI-state consistency
3. More regression tests
4. `main.py` decomposition

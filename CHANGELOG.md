# Changelog

## 6.6.0

### Cross-Platform Support
- **First official macOS release**: Built with PyInstaller, packaged as DMG.
- **Separate PyInstaller specs**: `(Windows).spec` and `(macOS).spec` for platform-specific builds.
- **Dual CI pipeline**: GitHub Actions builds both Windows EXE and macOS DMG in parallel.

### Quality & Testing
- Test count expanded to **247 tests** (+74 from 6.5.0, +94 from 6.4.0).
- Code coverage increased to **65%** (was 58%).
- New test files: `test_coverage_phase1.py` (23 tests), `test_coverage_phase2.py` (17 tests), `test_services.py` (28 tests).
- Pure-logic modules brought to 100% coverage: `eos/solver`, `pipe/selector`, `theme_colors`, `flow/utils`, `flow_utils`, `target_utils`, `release_metadata`, `translations`, `services/project_io`, `services/report_service`, `ui/dialogs`.
- Service modules now tested: progress (98%), report_service (100%), project_io (100%).

### Backward Compatibility
- App data directory stabilized to `"Gas Flow Calc"` (no version number), with automatic one-time migration from legacy `"Gas Flow Calc V6.1"` directory.
- Token encryption fallback chain preserved (XOR → Fernet → DPAPI).
- HMAC lockout backward compatibility maintained.
- Old project JSON files load correctly via defensive `data.get()` patterns.

### Update Flow
- Release assets now include both standalone `.exe` and source `.zip` for in-app updates.
- `config.json` is preserved during zip-based updates via `exclude_on_apply`.

## 6.5.0

### Architecture
- **calculations.py split**: Extracted EOS solver, friction factor, viscosity, phase detection, pipe selection, and thermo helpers into dedicated modules (`eos/`, `flow/`, `pipe/`, `thermo/`, `phase/`). Reduced from 1901 to ~1017 lines.
- **main.py split**: Extracted progress rendering, update checking, report generation, and project I/O into `services/` modules. Reduced from ~1148 to ~870 lines.
- **Theme color centralization**: Created `theme_colors.py` as the single color palette source, eliminating scattered color references in graphs, schematic, and widgets.

### Code Quality
- **Hardcoded Turkish strings removed**: All validation messages, result labels, dialog titles, and log messages now use `t()` calls backed by translation dictionaries (controllers.py, reporting.py, gas_panel.py, main.py).
- **Duplicate logic merged**: `main.py:populate_results_table` now delegates to `controllers.py:get_results_table_data`, eliminating duplicate label/formatting logic.
- **Dialog deduplication**: `show_user_guide` and `show_program_details` refactored into `_show_scrolled_dialog` factory.

### Calculation Accuracy
- **fluids library cross-validation**: Added tests comparing Churchill friction factor against `fluids.friction_factor` (max 2% deviation across 56 Re/roughness combos).
- **thermo library cross-check**: Added MW, critical property, and density validation against the `thermo` Chemical database.
- **GERG-88/SGERG validation**: Added compressibility factor cross-validation against `pygerg` (GERG-88 standard) for typical natural gas compositions at various pressures.

### Testing & Infrastructure
- Test coverage expanded to **173 tests** (+41 new).
- Added tests for `state_manager.py` (26% → 69% coverage) and `ui/dialogs.py` (22% → 94% coverage).
- `.coveragerc` isolates coverage measurement (excludes test files).

## 6.4.0

### UI & UX
- **Premium Dynamic Themes**: Refactored the UI styling engine to offer fully integrated Light, Dark, and High Contrast themes with premium cohesive HSL color palettes and micro-animations.
- **Debounced Input Validation (`ValidatedEntry`)**: Implemented active input verification that provides real-time visual feedback (warning icons, border highlights) using a non-blocking debouncing algorithm to guarantee input correctness.
- **Dynamic Schematic Canvas**: Rebuilt the interactive flow schematic using TK canvas rendering that dynamically redraws on panel resizing and state changes.
- **Translated Matplotlib Visualizations**: Charts (Pressure Drop profile, Velocity profile, Phase profiles) now dynamically translate all labels, grids, and legend text when the language switches, styling chart palettes to match the current theme.
- **Minimum Diameter Selection Automation**: In Minimum Diameter target mode, pipe geometry inputs (NPS, Schedule, manual diameter, wall thickness) are automatically locked. Once calculations complete, the app automatically writes the recommended standard pipe information into these fields, improving synchronization.

### Testing & Infrastructure
- Expanded regression and component test coverage to **132 tests** (+37 new tests).
- Added test suites for dynamic theme persistence, real-time field validation colors, locked state UI behaviors, automatic input synchronization, and updater error rollbacks.

## 6.3.0

### Security
- Added brute-force protection to admin password verification (5 failed attempts → 30 s lockout).
- GitHub token now encrypted via Windows DPAPI; XOR obfuscation removed.
- Downloaded update files are verified via SHA-256 hash comparison.
- Release body SHA256: <hash> format is now supported.

### Performance
- Smart thermo cache: cleared only when gas composition changes, significantly improving cache hit ratio.
- Triple-point temperatures (TTRIPLE) are now cached, reducing redundant CoolProp calls during phase detection.
- Cache key precision optimized (100 Pa / 0.01 K).
- Iterative Colebrook friction factor replaced with explicit Churchill equation.
- numpy dependency completely removed; cubic EOS root-finding now uses a closed-form Cardano solver (~300ms faster startup).
- DAK Newton-Raphson iterations reduced 50→20 with early-exit.

### Architecture
- GasFlowController (controllers.py) activated; start_calculation now collects data through the controller.
- patch_main.py deleted; dead code removed.
- 10+ silent except Exception: pass blocks are now properly logged.
- Application login restored (root.withdraw/deiconify method).
- Min Diameter alternatives display bug fixed.

### Thermodynamics
- AGA-8 GERG-2008 and AGA-8 DETAIL models added (via pyaga8 Rust library).
- Viscosity computed via Lee-Gonzalez-Eakin correlation.
- 5-10x faster thermodynamic calculation than CoolProp.

### Testing & Ecosystem
- 95 tests (previously 37 + 50 new + 8 PYAGA8): format_utils, app_paths, controllers, auth brute-force, edge cases, PYAGA8.
- pytest.ini, conftest.py added; coverage infrastructure ready.
- .gitignore test_*.py pattern now limited to root directory (tests/ unaffected).
- 4 agents (calc, ui, qa, release) and 2 skills (analyze, verify) created; compatible with opencode.

## 6.2.1

- Executable version and publisher metadata were added to the packaging build to prevent false-positive detections by corporate antivirus software (e.g., Windows Defender).

## 6.2.0

- Added a phase-aware flow engine that tracks gas, liquid, and two-phase conditions along the pipe profile.
- Improved single-phase liquid calculations with Churchill friction-factor handling and a density-change acceleration term.
- Hardened CoolProp phase/property handling for cryogenic and metastable points using envelope-based fallbacks and safer formatting paths.
- Expanded detailed reports to include input composition and inlet/outlet thermophysical properties.
- Normalized flow-mode handling across Turkish and English labels and carried the phase-aware logic into max-length and minimum-diameter workflows.

## 6.1.13

- Fixed Length input visibility bug in Minimum Diameter mode that kept the field hidden on startup.
- Enhanced summary table for Minimum Diameter calculations to display Gas Velocity for alternative pipe options.

## 6.1.12

- Removed hardcoded UI layer manipulation from `main.py` and introduced `GasFlowController` for state processing.
- Resolved Unicode decoding artifacts ("Â°C") due to Latin-1 fallback string reading in Tkinter string vars.
- Restricted `Exception` catching in CoolProp properties to `ValueError` limiting silent thermodynamic calculation failures.
- Implemented Ideal Gas sonic velocity fallbacks for hydrogen-rich mixtures failing state equations.
- Removed duplicated derivative structures in `calculations.py` pseudo-critical function.
- Expanded backend module test suite providing unit tests for all GasFlowCalculator algorithms.

## 6.1.11

- Added a new View menu with light, dark, and high-contrast themes.
- Persisted the selected UI theme in local config so it is restored on the next launch.
- Increased the visible height of the gas-mixture list so at least six rows are comfortably visible.
- Tightened the process-conditions layout so labels, inputs, and unit selectors stay closer together on resize.
- Added UI regression coverage for theme switching and the taller gas-mixture list.

## 6.1.10

- Fixed the updater for public GitHub repos so an invalid stored token is cleared and the request is retried anonymously.
- Prevented stale tokens from older private-repo setups from blocking automatic update checks and asset downloads.
- Added regression coverage for the public-repo token fallback path.

## 6.1.9

- Added an automatic startup update check that offers the GitHub release download flow when a newer version is available.
- Enabled and disabled user input fields dynamically so each calculation target only leaves the required inputs active.
- Fixed maximum-length calculations so standard volumetric flow is normalized consistently and no longer collapses into incorrect `0.00 m` results.
- Added regression coverage for the updated max-length logic, startup update prompt, and target-based UI state handling.

## 6.1.8

- Added a startup password gate so the program opens only after a valid access password is entered.
- Added admin-only password management for both the admin password and the program access password.
- Set the initial default admin password and program access password to `123456`.
- Moved text-report formatting into a dedicated helper module to continue reducing `main.py` responsibility.

## 6.1.7

- Fixed the startup calculation-target mismatch so the active segmented button matches the default `Minimum Diameter` mode.
- Aligned project-load fallback behavior with the same `Minimum Diameter` default target.
- Clarified GitHub updater SSL certificate verification errors for corporate/intercepted network environments.
- Added a Windows PowerShell network-stack fallback for updater requests when Python rejects the TLS certificate chain.

## 6.1.6

- Fixed the Python 3.13 `CoolProp` string/bytes compatibility failure that caused `expected bytes, str found`.
- Normalized gas-name handling across internal IDs, CoolProp names, and display labels.
- Hardened flow-unit parsing so corrupted `Sm3/h` labels no longer get treated as `kg/s`.
- Added regression coverage for the updated CoolProp and unit-handling paths.

## 6.1.5

- Switched the updater default repo to the public `SLedgehammer-dev12/gas-flow-calc` repository.
- Added automatic migration for legacy local configs that still reference the older private repo.
- Removed the default private-repo update requirement so release checks can work without a token.

## 6.1.4

- Explicitly bundled `unicodedata` for PyInstaller builds to prevent packaged startup crashes.
- Lazy-loaded matplotlib Tk backend imports in the graph module.
- Switched the packaged executable name to a versioned format such as `Gas Flow Calc V6.1.4.exe`.

## 6.1.3

- Added a dedicated `Releases` folder for local packaged `.exe` outputs.
- Improved the private GitHub repo 404 message so the cause is clearer.
- Clarified the local-token-based update path for private repository usage.

## 6.1.2

- Added a save-location prompt before downloading update files.
- Split the update flow for `.exe` and `.zip` packages.
- Centralized version metadata and local release notes.
- Moved the default GitHub update source to `SLedgehammer-dev12/gas-flow-calc-v6-1`.

## 6.1.1

- Switched the updater defaults to GitHub Releases.
- Added modular UI source files and the PyInstaller spec file to the repository.
- Improved single-file `.exe` packaging.

## 6.1.0

- Prepared the app for standalone Windows `.exe` distribution.
- Moved config and session storage into the user profile.
- Added the first release-based update preparation work.

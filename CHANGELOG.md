# Changelog

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

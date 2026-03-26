# Changelog

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

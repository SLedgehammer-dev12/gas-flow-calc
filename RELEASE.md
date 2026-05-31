# RELEASE

## Release Checklist — v6.6.0

### Kapsam
- Cross-platform: Windows EXE + macOS DMG
- Code coverage: 58% → 65% (247 tests)
- Backward compatible config migration
- Python 3.13

### Versioning

- [ ] `release_metadata.py`: `APP_VERSION = "6.6.0"` ✅
- [ ] `version_info.txt`: `filevers=(6,6,0,0)`, `FileVersion=6.6.0` ✅
- [ ] `CHANGELOG.md`: 6.6.0 başlığı eklendi ✅
- [ ] `README.md`: versiyon güncellendi ✅
- [ ] `app_paths.py`: `APP_DIR_NAME = "Gas Flow Calc"` + migration ✅

### Validation

- [ ] `python3 -m pytest tests/ -q --tb=short` (247 test)
- [ ] `python3 main.py` (manuel başlatma)
- [ ] macOS local build: `pyinstaller "Gas Flow Calc V6.6 (macOS).spec" --clean`
- [ ] macOS DMG: `hdiutil create ... Gas_Flow_Calc_V6.6.0.dmg`
- [ ] Manuel senaryolar:
  - Sm³/h ve kg/s ile eşit fiziksel sonuçlar
  - Maksimum uzunlukta pozitif sonuç
  - Min çap seçimi + alternatifler
  - Tema geçişi (light/dark)
- [ ] Eski config migration: var olan `Gas Flow Calc V6.1\config.json` → yeni dizine taşınır

### Packaging

- [ ] `Gas Flow Calc V6.6 (Windows).spec` — PyInstaller
- [ ] `Gas Flow Calc V6.6 (macOS).spec` — PyInstaller
- [ ] CI workflow: `.github/workflows/build-release.yml`
- [ ] Source ZIP: `git archive --format=zip ...`

### Publishing

1. `git add -A && git commit -m "v6.6.0: cross-platform release"`
2. `git tag -a v6.6.0 -m "Gas Flow Calc v6.6.0"`
3. `gh release create v6.6.0 --title "Gas Flow Calc v6.6.0" --notes-file RELEASE_NOTES.md`
4. `git push origin main --tags`
5. CI çalışmasını bekle (Windows EXE + macOS DMG + source ZIP)
6. Release sayfasında SHA-256 checksum'larını doğrula

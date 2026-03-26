APP_NAME = "Gas Flow Calc"
APP_VERSION = "6.1.6"


RELEASE_NOTES = {
    "6.1.0": {
        "tr": """6.1.0 ile gelen baslica yenilikler:

- Uygulama tek dosya Windows .exe cikti ile dagitilacak sekilde duzenlendi.
- Ayar ve oturum dosyalari kullanici profilinde tutulmaya baslandi.
- GitHub uzerinden guncelleme altyapisi release tabanli calisacak sekilde hazirlandi.""",
        "en": """Highlights introduced in 6.1.0:

- The application was prepared for standalone Windows single-file .exe distribution.
- Configuration and session files were moved to the user profile directory.
- The GitHub update pipeline was prepared for release-based updates.""",
    },
    "6.1.1": {
        "tr": """6.1.1 ile gelen baslica yenilikler:

- Varsayilan guncelleme kaynagi GitHub Releases olacak sekilde guncellendi.
- Moduler UI dosyalari ve PyInstaller spec dosyasi repoya eklendi.
- Paketleme ayarlari tek dosya .exe uretimi icin iyilestirildi.""",
        "en": """Highlights introduced in 6.1.1:

- The default update source was switched to GitHub Releases.
- Modular UI files and the PyInstaller spec file were added to the repository.
- Packaging settings were improved for single-file .exe distribution.""",
    },
    "6.1.2": {
        "tr": """6.1.2 ile gelen baslica yenilikler:

- Yeni bir surum bulundugunda indirilecek dosyanin kayit konumu artik kullanici tarafindan seciliyor.
- Uygulama ici guncelleme akisinda .exe ve .zip dosyalari ayri sekilde ele aliniyor.
- Her surum icin release notlari merkezi bir metadata yapisinda tutuluyor.
- Surum numarasi tek noktadan yonetilecek sekilde duzenlendi.""",
        "en": """Highlights introduced in 6.1.2:

- When a new version is found, the user now chooses where the update file will be saved.
- The in-app update flow now handles .exe and .zip downloads separately.
- Release notes for each version are now stored in a centralized metadata structure.
- Version numbering was refactored to be managed from a single source of truth.""",
    },
    "6.1.3": {
        "tr": """6.1.3 ile gelen baslica yenilikler:

- Release derlemeleri artik program klasoru icindeki Releases klasorunde uretiliyor.
- Private GitHub repo kullanildiginda 404 hatasi daha acik bir mesaja donusturuldu.
- Private repo icin gerekirse GitHub token yerel ayarlara sorularak kaydedilebiliyor.""",
        "en": """Highlights introduced in 6.1.3:

- Release builds are now generated inside the Releases folder within the program directory.
- The 404 case for private GitHub repositories now produces a clearer message.
- For private repos, the app can now ask for a GitHub token and store it in local user settings.""",
    },
    "6.1.4": {
        "tr": """6.1.4 ile gelen baslica yenilikler:

- PyInstaller paketine eksik kalan unicodedata modulu acikca eklendi.
- Grafik modulu matplotlib bilesenlerini gec yukleyerek acilis kararliligi iyilestirildi.
- Uretilen .exe dosyasi artik surum numarasini adinda tasiyor.""",
        "en": """Highlights introduced in 6.1.4:

- The missing unicodedata module is now explicitly bundled in the PyInstaller package.
- The graph module now lazy-loads matplotlib components for more reliable startup behavior.
- Generated .exe files now include the version number in their file name.""",
    },
    "6.1.5": {
        "tr": """6.1.5 ile gelen baslica yenilikler:

- Varsayilan guncelleme kaynagi public GitHub repo olan SLedgehammer-dev12/gas-flow-calc olarak guncellendi.
- Eski private repo ayarlari olan yerel config dosyalari otomatik olarak yeni public repo ayarina tasiniyor.
- Guncelleme kontrolu artik token gerektirmeden GitHub release uzerinden calisiyor.""",
        "en": """Highlights introduced in 6.1.5:

- The default update source now points to the public GitHub repo SLedgehammer-dev12/gas-flow-calc.
- Existing local configs that still point to the older private repo are migrated automatically.
- Update checks now work through GitHub releases without requiring a token.""",
    },
    "6.1.6": {
        "tr": """6.1.6 ile gelen baslica yenilikler:

- CoolProp cagri katmani Python 3.13 ortami icin uyumlu hale getirildi ve expected bytes, str found hatasi giderildi.
- Gaz bilesimi anahtarlari artik hem ic ID hem CoolProp adi hem de gorunen etiketlerle guvenli sekilde esleniyor.
- Debi birimi yorumlamasi saglamlastirildi; Sm3/h etiket bozulmalarinda bile hesaplar artik kg/s ile karismiyor.
- CoolProp ve debi birimi icin regresyon testleri eklendi.""",
        "en": """Highlights introduced in 6.1.6:

- The CoolProp call layer was made compatible with Python 3.13, fixing the expected bytes, str found error.
- Gas composition keys are now resolved safely across internal IDs, CoolProp names, and display labels.
- Flow-unit parsing was hardened so Sm3/h label corruption no longer falls through as kg/s.
- Regression tests were added for CoolProp compatibility and flow-unit handling.""",
    },
}


def get_release_notes(version, language):
    notes = RELEASE_NOTES.get(version, {})
    return notes.get(language) or notes.get("en") or ""


def get_release_notes_title(version, language):
    if language == "tr":
        return f"Guncelleme Notlari (Versiyon {version})"
    return f"Update Notes (Version {version})"


def get_versioned_exe_stem(version=None):
    version = version or APP_VERSION
    return f"{APP_NAME} V{version}"


def get_versioned_exe_name(version=None):
    return f"{get_versioned_exe_stem(version)}.exe"

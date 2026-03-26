APP_VERSION = "6.1.2"


RELEASE_NOTES = {
    "6.1.0": {
        "tr": """6.1.0 ile gelen başlıca yenilikler:

- Uygulama tek dosya Windows .exe çıktısı ile dağıtılacak şekilde düzenlendi.
- Ayar ve oturum dosyaları kullanıcı profilinde tutulmaya başlandı.
- GitHub üzerinden güncelleme altyapısı release tabanlı çalışacak şekilde hazırlandı.""",
        "en": """Highlights introduced in 6.1.0:

- The application was prepared for standalone Windows single-file .exe distribution.
- Configuration and session files were moved to the user profile directory.
- The GitHub update pipeline was prepared for release-based updates.""",
    },
    "6.1.1": {
        "tr": """6.1.1 ile gelen başlıca yenilikler:

- Varsayılan güncelleme kaynağı GitHub Releases olacak şekilde güncellendi.
- Moduler UI dosyaları ve PyInstaller spec dosyası repoya eklendi.
- Paketleme ayarları tek dosya .exe üretimi için iyileştirildi.""",
        "en": """Highlights introduced in 6.1.1:

- The default update source was switched to GitHub Releases.
- Modular UI files and the PyInstaller spec file were added to the repository.
- Packaging settings were improved for single-file .exe distribution.""",
    },
    "6.1.2": {
        "tr": """6.1.2 ile gelen başlıca yenilikler:

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
}


def get_release_notes(version, language):
    notes = RELEASE_NOTES.get(version, {})
    return notes.get(language) or notes.get("en") or ""


def get_release_notes_title(version, language):
    if language == "tr":
        return f"Guncelleme Notlari (Versiyon {version})"
    return f"Update Notes (Version {version})"

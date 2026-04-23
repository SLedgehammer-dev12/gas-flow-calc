APP_NAME = "Gas Flow Calc"
APP_VERSION = "6.2.1"


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
    "6.1.7": {
        "tr": """6.1.7 ile gelen baslica yenilikler:

- Acilista varsayilan hesaplama hedefi ile aktif segmented buton gosterimi senkron hale getirildi.
- Proje yukleme ve ilk acilis akisi varsayilan hedef olarak Minimum Cap mantigi ile tutarli hale getirildi.
- GitHub guncelleyici icin SSL sertifika dogrulama hatalari daha acik mesajlanir hale getirildi.
- Windows ortaminda SSL zinciri Python tarafinda reddedilirse guncelleme istekleri PowerShell ag katmani ile yeniden deneniyor.""",
        "en": """Highlights introduced in 6.1.7:

- The startup default calculation target is now kept in sync with the active segmented-button state.
- Project loading and first-launch behavior now consistently default to Minimum Diameter.
- SSL certificate verification failures in the GitHub updater now produce clearer diagnostics.
- On Windows, update requests are retried through the PowerShell network stack when Python rejects the certificate chain.""",
    },
    "6.1.8": {
        "tr": """6.1.8 ile gelen baslica yenilikler:

- Program acilisina parola dogrulamasi eklendi; uygulama ancak dogru giris sifresi ile aciliyor.
- Admin rolu icin ayri parola yonetimi eklendi; admin hem kendi sifresini hem de program giris sifresini degistirebiliyor.
- Ilk kurulumda varsayilan admin sifresi ve program giris sifresi 123456 olarak baslatiliyor.
- Rapor olusturma yardimcilari ayrik bir module tasinarak ana pencere denetleyicisi sadelelestirildi.""",
        "en": """Highlights introduced in 6.1.8:

- Password verification was added to startup; the application now opens only after a valid access password is entered.
- A separate admin password-management flow was added; the admin can change both the admin password and the program access password.
- On first setup, both the default admin password and the default program access password start as 123456.
- Report formatting helpers were moved into a separate module to reduce controller complexity.""",
    },
    "6.1.9": {
        "tr": """6.1.9 ile gelen baslica yenilikler:

- Uygulama acilisinda otomatik GitHub release kontrolu yapiliyor ve yeni surum varsa indirme akisi teklif ediliyor.
- Hesaplama hedefi secimine gore sadece gerekli kullanici giris alanlari aktif kalacak sekilde arayuz davranisi duzenlendi.
- Maksimum uzunluk hesabinda standart hacimsel debi ile kutlesel debi yorumlamasi birlestirilerek 0.00 m gorunen hatali sonuclar giderildi.
- Hesap motoru ve UI davranislari icin yeni regresyon testleri eklendi.""",
        "en": """Highlights introduced in 6.1.9:

- The app now performs an automatic GitHub release check at startup and offers the download flow when a new version is available.
- The UI now enables only the user inputs required by the selected calculation target.
- Maximum-length calculations now normalize standard volumetric and mass-flow inputs consistently, fixing erroneous 0.00 m results.
- New regression tests were added for both calculation logic and UI behavior.""",
    },
    "6.1.10": {
        "tr": """6.1.10 ile gelen baslica yenilikler:

- Public GitHub repo kullanilirken yerelde sakli gecersiz token varsa updater artik bunu temizleyip kimliksiz olarak tekrar deniyor.
- Bu sayede eski private-repo gecisinden kalan tokenlar otomatik guncelleme akisini bozmaz hale getirildi.
- Public-repo token fallback davranisi icin regresyon testi eklendi.""",
        "en": """Highlights introduced in 6.1.10:

- When the app talks to a public GitHub repo and encounters a stale local token, the updater now clears it and retries anonymously.
- This prevents leftover tokens from older private-repo setups from breaking the automatic update flow.
- A regression test was added for the public-repo token fallback behavior.""",
    },
    "6.1.11": {
        "tr": """6.1.11 ile gelen baslica yenilikler:

- Arayuze yeni bir Gorunum menusu eklendi; acik, koyu ve yuksek kontrast tema secenekleri arasinda gecis yapilabiliyor.
- Secilen tema yerel ayarlara kaydediliyor ve uygulama yeniden acildiginda korunuyor.
- Gaz karisimi listesinin gorunen yuksekligi artirilarak ayni anda en az alti satirin izlenmesi kolaylastirildi.
- Proses kosullari bolumu daha kompakt bir grid duzeni ile yeniden yerlesitirildi; etiket, giris ve birim alanlari artik birbirinden fazla uzaklasmiyor.
- UI tarafina yeni regresyon testleri eklendi.""",
        "en": """Highlights introduced in 6.1.11:

- A new View menu was added with light, dark, and high-contrast theme options.
- The selected theme is now stored in local settings and restored on the next launch.
- The visible height of the gas-mixture list was increased so at least six rows can be viewed more comfortably.
- The process-conditions section was rearranged into a more compact grid so labels, inputs, and unit selectors stay visually closer together.
- Additional UI regression tests were added.""",
    },
    "6.1.12": {
        "tr": """6.1.12 ile gelen baslica yenilikler:

- Arayuz olay islemleri main.py'den ayrilarak yeni GasFlowController katmanina tasindi.
- Degisken okumalarindaki \"Â°C\" gibi encoding sorunlari giderildi.
- CoolProp exception yakalama kapsami daraltilarak sessiz termodinamik hatalarin onune gecildi.
- Sonik hiz hesaplamalarina ideal gaz fallback mantigi eklendi.
- Arka uca tum hesaplama operasyonlari (calculations.py) icin test kapsami eklendi.""",
        "en": """Highlights introduced in 6.1.12:

- UI event processing was decoupled from main.py and moved to a new GasFlowController layer.
- Unicode decoding issues like \"Â°C\" during variable reading were resolved.
- CoolProp exception catching was restricted to prevent silent thermodynamic calculation failures.
- Ideal gas fallback logic was added for sonic velocity calculations.
- Backend test coverage was expanded with new comprehensive test routines."""
    },
    "6.1.13": {
        "tr": """6.1.13 ile gelen baslica yenilikler:

- Minimum Cap hedef modunda uzunluk girisinin baslangicta gizli kalmasina neden olan UI mantik hatasi giderildi.
- Minimum Cap hedefi icin uretilen alternatif boru secenekleri ozet tablosuna artik gaz cikis hizlari da eklendi.""",
        "en": """Highlights introduced in 6.1.13:

- Fixed the UI logic bug that caused the length input to remain hidden at startup in Minimum Diameter mode.
- The summary table for alternative pipe options in the Minimum Diameter target now displays gas exit velocities."""
    },
    "6.2.0": {
        "tr": """6.2.0 ile gelen baslica yenilikler:

- Faz duyarlı akış motoru eklendi; segment bazında gaz, sivi ve iki faz bolgeleri izleniyor ve raporlanıyor.
- Sivi tek-faz hesabı Darcy-Weisbach tabanı uzerinde Churchill surtunme faktoru ve yogunluk degisimine bagli ivmelenme terimi ile iyilestirildi.
- Faz flash cozumunun zorlandigi kriyojenik ve metastabil noktalarda CoolProp envelope fallback mantigi eklendi; ham hata mesajlari yerine anlamli faz uyarlari uretiliyor.
- Detay rapora girilen kompozisyon ile giris/cikis PT noktalarindaki yogunluk, molekuler agirlik, Z, Cp, Cv, viskozite ve ses hizi gibi ozellikler eklendi.
- Akis tipi secimi Turkce/Ingilterce etiketlerden bagimsiz hale getirildi; guncelleyici ve paketleme zinciri SSL/runtime sorunlarina karsi sertlestirildi.""",
        "en": """Highlights introduced in 6.2.0:

- Added a phase-aware flow engine that tracks and reports gas, liquid, and two-phase regions segment by segment.
- Improved the single-phase liquid calculation with a Darcy-Weisbach base plus Churchill friction factor and a density-change acceleration term.
- Added CoolProp envelope fallbacks for cryogenic and metastable points so users get meaningful phase diagnostics instead of raw flash errors.
- Extended the detailed report with input composition plus inlet/outlet PT properties such as density, molecular weight, Z, Cp, Cv, viscosity, and speed of sound.
- Hardened flow-mode normalization across Turkish/English labels and improved updater/packaging resilience against SSL/runtime issues."""
    },
    "6.2.1": {
        "tr": """6.2.1 ile gelen baslica yenilikler:

- Kurumsal antivirüs (Windows Defender vb.) yazilimlarinin yanlis pozitif (false-positive) uyarilarini engellemek amaciyla paketleme ayarlarina exe versiyon ve yayinci bilgileri (metadata) eklendi.""",
        "en": """Highlights introduced in 6.2.1:

- Executable version and publisher metadata were added to the packaging build to prevent false-positive detections by corporate antivirus software (e.g., Windows Defender)."""
    }
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

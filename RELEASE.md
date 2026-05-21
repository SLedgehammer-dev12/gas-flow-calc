# RELEASE

## Patch Release Checklist

### Hedef patch

- Onerilen patch: `v6.3.0`
- Kapsam:
  - AGA-8 termodinamik modelleri (GERG-2008 ve DETAIL)
  - Admin bruteforce kilidi ve token DPAPI şifrelemesi
  - Sürtünme faktörü Colebrook -> Churchill explicit geçişi
  - UI-Hesaplama senkronizasyonu ve Minimum Çap / Maksimum Uzunluk iyileştirmeleri

### Versioning

- `release_metadata.py` icinde surumu guncelle
- `CHANGELOG.md` icine patch notlarini ekle
- Gerekirse paket adi ve splash/version metinlerini kontrol et

### Validation

- `python -m unittest discover -s tests -v`
- `python main.py`
- Asagidaki manuel senaryolari dogrula:
  - ayni fiziksel debi icin `Sm3/h` ve `kg/s` ile esit sonuclar
  - maksimum uzunlukta pozitif, mantikli bir sonuc
  - fitting kaybi cok yuksekse acik hata mesaji
  - varsayilan hedef ve segmented button durumu

### Packaging

- `pyinstaller "Gas Flow Calc V6.1.spec"`
- cikti `.exe` adini ve surum bilgisini dogrula
- paketli surumde hizli smoke test yap

### Publishing

- commit mesajinda patch kapsamini acik yaz
- release tag olustur
- release notlarinda bu hata icin kullaniciya etkisini belirt:
  - maksimum uzunluk artik volumetrik debiyi dogru yorumluyor

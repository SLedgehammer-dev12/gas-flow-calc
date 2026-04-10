# AGENTS

## Amac

Bu dosya, projede calisacak kisi veya ajanlarin sorumluluk sinirlarini netlestirir.

## Roller

### 1. Calculation Agent

- Sahiplik:
  - `calculations.py`
  - `data.py`
  - hesap motoru testleri
- Sorumluluk:
  - birim donusumleri
  - basinç kaybi, maksimum uzunluk, minimum cap
  - fiziksel tutarlilik kontrolleri

### 2. UI Agent

- Sahiplik:
  - `main.py`
  - `ui/`
  - `translations.py`
- Sorumluluk:
  - girdi toplama
  - sonuc sunumu
  - hata ve uyari metinleri
  - kullanici akisi

### 3. QA Agent

- Sahiplik:
  - `tests/`
  - release dogrulama akisi
- Sorumluluk:
  - regresyon testleri
  - edge-case senaryolari
  - paketleme oncesi smoke test

### 4. Release Agent

- Sahiplik:
  - `RELEASE.md`
  - `CHANGELOG.md`
  - `release_metadata.py`
- Sorumluluk:
  - surum notlari
  - cikis kontrol listesi
  - exe paket dogrulamasi

## Calisma Kurallari

1. Hesap degisikligi test olmadan merge edilmemeli.
2. UI metni degisiyorsa `translations.py` ve ilgili ekran birlikte kontrol edilmeli.
3. Birim donusumu gorulen her yerde ortak helper tercih edilmeli.
4. `main.py` icinde yeni hesap mantigi yazmak yerine `calculations.py` genisletilmeli.
5. Release oncesi en az bir `Sm3/h` ve bir `kg/s` senaryosu manuel dogrulanmali.

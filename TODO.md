# TODO

## Session Handoff - 2026-04-11

- Faz duyarlı altyapının ilk calisan versiyonu eklendi:
  - `flow_utils.py` ile `flow_mode` normalize edildi.
  - `target_utils.py` ile `calc_target_mode` normalize edildi.
  - `calculations.py` icine `detect_phase`, iki faz property split, basit Lockhart-Martinelli segment kaybi, `phase_profile`, `transition_to_two_phase_m` eklendi.
  - `controllers.py`, `reporting.py`, `main.py` faz bilgisi ve warning banner icin guncellendi.
- Test durumu:
  - `pytest -q` -> `28 passed`
- Calisma agaci:
  - degisen dosyalar: `calculations.py`, `controllers.py`, `main.py`, `reporting.py`
  - yeni dosyalar: `flow_utils.py`, `target_utils.py`
- Siradaki teknik adim:
  - `calculate_max_length()` icindeki binary-search solver'ini ayri ortak segment solver uzerine tasiyip iki faz davranisini ic iterasyon seviyesinde de tutarli hale getir.
  - Faz warning popup akisini ekle.
  - Gerekirse `phase_profile` verisini CSV/export ve sema tarafina tasiyip gorsellestir.

## High Priority

- `main.py` icindeki UI orkestrasyonunu daha kucuk modullere bol.
- `translations.py` icin encoding ve metin tutarliligi temizligi yap.
- Hesap hedefleri icin daha genis regresyon testi ekle:
  - `pressure_drop`
  - `max_length`
  - `min_diameter`
- UI tarafinda `error` ve `note` sonuc durumlarini daha belirgin goster.

## Medium Priority

- Hesap motorundaki tum birim donusumlerini ayri utility katmanina tasi.
- `main.py` rapor olusturma mantigini ayri modullere bol.
- Update/config diagnostik ekranini uygulama icine ekle.
- Fitting agirlikli maksimum uzunluk senaryolari icin yardim metni ekle.

## Low Priority

- `assets/` klasorundeki gorsellerin aktif kullanilip kullanilmadigini dogrula.
- README ve kullanici kilavuzunu daha kapsamli hale getir.
- Sonuc ekranina daha detayli fizibilite aciklamalari ekle.

# TASK

## Mevcut Odak

Maksimum uzunluk hedefinin guvenilirligini ve hesap hedefleri arasindaki birim tutarliligini kalici hale getirmek.

## Bu turda tamamlananlar

- `Sm3/h` -> `kg/s` donusumu tek helper fonksiyona toplandi.
- Maksimum uzunlukta 0.00 m kok nedeni tespit edildi.
- Sikistirilabilir akis icin "fitting kaybi tek basina hedefi bozuyor" durumu acik hata olarak ayrildi.
- Yeni regresyon testleri eklendi.
- Proje ici analiz ve operasyon markdown dosyalari olusturuldu ve guncellendi.

## Siradaki teknik isler

1. `main.py` icindeki `get_inputs`, `validate_inputs`, `populate_results_table` akislarini modullere ayir.
2. Maksimum uzunluk sonucundaki `error` ve `note` alanlarini UI'da daha gorunur hale getir.
3. `translations.py` encoding temizligi yap.
4. Parametrik hesap testleri ekle:
   - farkli gaz karisimlari
   - farkli basinç birimleri
   - farkli fitting kombinasyonlari

## Hazir kabul kriterleri

- `Sm3/h` ve `kg/s` esit fiziksel debi icin esit sonuca gitmeli.
- Imkansiz maksimum uzunluk vakasi 0.00 m gibi sessiz sonuc vermemeli.
- Test paketi temiz calismali.

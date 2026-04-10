# ANALYSIS

## 1. Codebase Haritasi

### Uygulama katmanlari

- `main.py`
  - Tkinter uygulama orkestrasyonu.
  - UI state toplama, validasyon, hesap thread baslatma ve sonuc gosterme.
  - Tek dosyada cok fazla sorumluluk var; gelecekte bolunmeli.

- `calculations.py`
  - Tum hesap motoru burada.
  - Termodinamik ozellikler, basinç kaybi, maksimum uzunluk ve minimum cap mantigi burada toplanmis.
  - Kritik hata bu dosyada bulundu.

- `data.py`
  - Gaz, roughness, fitting K ve boru tablolarini tasiyor.

- `reporting.py`
  - Rapor formatlama yardimcilari.

- `translations.py`
  - Metinler ve aciklama metinleri.
  - Dosyada encoding tutarsizliklari var; ileri asamada temizlenmeli.

- `ui/`
  - Paneller, sema ve widget katmani.
  - `ui/panels/process_panel.py` hedef secimini,
    `ui/panels/pipe_panel.py` boru ve hedef girdilerini,
    `ui/panels/results_panel.py` sonuc sunumunu yurutuyor.

- `tests/`
  - Auth, updater, UI varsayilanlari ve reporting icin test var.
  - Hesap motoru icin kapsam daha once yetersizdi.

## 2. Veri Akisi

1. Kullanici girdileri `main.py` icinde toplanir.
2. `get_inputs()` ile basinç, sicaklik, debi, geometri ve hedef tek dict haline gelir.
3. Hedefe gore `GasFlowCalculator` icindeki ilgili fonksiyon cagrilir.
4. Sonuc `reporting.py` ve `results_panel` ile tablo, rapor ve sema olarak gosterilir.

## 3. Maksimum Uzunlukta 0 m Sonucunun Kok Nedeni

### Tespit edilen hata

`calculations.py` icinde `flow_unit` degeri bazen su sekilde normalize ediliyordu:

- volumetrik giris icin: `"SmÂ³/h"`
- kontrol satiri ise: `"Sm³/h"`

Bu iki string ayni olmadigi icin, standart hacimsel debi girisi bazi hedeflerde dogrudan `kg/s` gibi ele aliniyordu.

### Neden 0.00 m gorunuyordu?

- `calculate_max_length()` fonksiyonunda `Sm3/h` degeri dogru sekilde kg/s'e cevrilmedigi zaman `m_dot` cok buyuyordu.
- Ornek:
  - Giris: `1,945,000 Sm3/h`
  - Dogru kutlesel debi: yaklasik `367.30 kg/s`
  - Hatali yorum: `1,945,000 kg/s`
- Bu hata basinç kaybini asiri buyuttugu icin binary search algoritmasi uzunlugu alt sinira itiyordu.
- Alt sinir `0.001 m` oldugu icin arayuzde formatlanirken `0.00 m` gorunuyordu.

### Ikincil davranis sorunu

Sikistirilabilir akis modunda, sadece fitting kayiplari bile hedef basinç farkini asiyorsa kod bunu acik hata olarak donmuyordu. Bu da yine sifira cok yakin bir uzunlugun normalmis gibi gorunmesine yol acabiliyordu.

## 4. Uygulanan Duzeltme

- Debi donusumu tek bir yardimci fonksiyona tasindi:
  - `calculate_mass_flow_rate()`
- Bu yardimci artik su hedeflerde ortak kullaniliyor:
  - `calculate_pressure_drop()`
  - `calculate_max_length()`
  - `calculate_min_diameter()`
- `calculate_max_length()` icine sifir uzunluk fizibilite kontrolu eklendi.
  - Fitting kayiplari tek basina hedefi bozuyorsa artik acik `error` donuyor.

## 5. Mimari Bulgular

### Guclu yonler

- Hesap motoru UI'dan temel olarak ayrilmis.
- Veri tablolari merkezi tutuluyor.
- Tkinter panelleri ayri dosyalara bolunmus.

### Zayif yonler

- `main.py` cok buyuk ve UI + state + workflow + reporting sorumluluklarini birlikte tasiyor.
- Hesap motorunda birim donusumleri birden fazla yerde tekrar ediyordu.
- Encoding kaynakli string tutarsizliklari regresyon riski olusturuyor.
- Hesap hedefleri icin test kapsami eksik kalmis.

## 6. Onerilen Sonraki Adimlar

1. `main.py` icindeki input-toplama ve sonuc-sunum mantigini servis katmanina bol.
2. Tum birim donusumlerini tek modulde veya tek helper katmaninda topla.
3. `translations.py` ve kaynak dosyalarda encoding temizligi yap.
4. Hesap hedefleri icin parametrik test seti ekle.
5. Maksimum uzunluk sonucunda hata ve not durumlarini UI banner ve raporda daha belirgin goster.

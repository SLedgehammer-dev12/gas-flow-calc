# translations.py - Multi-language support for Gas Flow Calculator V5

# Current language setting
_current_lang = "tr"

# Translation dictionaries
TRANSLATIONS = {
    "tr": {
        # App Title
        "app_title": "Doğal Gaz Hesaplayıcı",
        
        # Menu - File
        "menu_file": "Dosya",
        "menu_save_project": "Projeyi Kaydet (JSON)",
        "menu_load_project": "Proje Aç (JSON)",
        "menu_exit": "Çıkış",
        
        # Menu - Update
        "menu_update": "Güncelleme",
        "menu_check_updates": "Güncellemeleri Kontrol Et",
        "menu_download_latest": "Son Sürümü İndir",
        "menu_apply_update": "Zip'ten Güncellemeyi Uygula...",
        "menu_update_config": "Güncelleme Yapılandırması...",
        
        # Menu - Language
        "menu_language": "Dil",
        "lang_turkish": "Türkçe",
        "lang_english": "English",
        "menu_view": "Görünüm",
        "theme_light": "Açık Tema",
        "theme_dark": "Koyu Tema",
        "theme_contrast": "Yüksek Kontrast",
        
        # Tabs
        "tab_calculation": "Hesaplama",
        "tab_logs": "İşlem Günlüğü",
        
        # Sections
        "section_gas_mixture": "1. Gaz Karışımı",
        "section_process_conditions": "2. Proses Koşulları",
        "section_pipe_properties": "3. Boru ve Hat Özellikleri",
        "section_design_criteria": "Tasarım Kriterleri (Min. Çap Hesabı)",
        "section_fittings": "Boru Elemanları (Adet)",
        "toggle_fittings_show": "▶ Boru Elemanlarını Göster",
        "toggle_fittings_hide": "▼ Boru Elemanlarını Gizle",
        
        # Gas Section
        "gas_search": "Gaz Ara:",
        "btn_add_gas": "Ekle",
        "gas_total": "Toplam:",
        "composition_type": "Bileşim Türü:",
        "mol_percent": "Mol %",
        "mass_percent": "Kütle %",
        "gas_preset": "Hazır Karışım:",
        "gas_preset_select": "-- Seçiniz --",
        
        # Process Section
        "inlet_pressure": "Giriş Basıncı:",
        "temperature": "Sıcaklık:",
        "flow_rate": "Akış Miktarı:",
        "calc_target": "Hesaplama Hedefi:",
        "thermo_model": "Model:",
        "flow_type": "Akış Tipi:",
        
        # Calculation Targets
        "target_pressure_drop": "Çıkış Basıncı",
        "target_max_length": "Maksimum Uzunluk",
        "target_min_diameter": "Minimum Çap",
        
        # Flow Types
        "flow_incompressible": "Sıkıştırılamaz",
        "flow_compressible": "Sıkıştırılabilir",
        
        # Pipe Section
        "material": "Malzeme:",
        "length": "Uzunluk (m):",
        "outer_diameter": "Dış Çap (mm):",
        "wall_thickness": "Et Kalınlığı (mm):",
        "nps": "NPS:",
        "schedule": "Schedule:",
        "smys": "SMYS (MPa):",
        "manual_custom": "Manuel / Custom",
        "target_outlet_pressure": "Hedef Çıkış Basıncı:",
        "max_velocity": "Maks. Hız (m/s):",
        "design_pressure": "Tasarım Basıncı:",
        "factor_f": "Tasarım Faktörü (F):",
        "factor_e": "Boyuna Bağlantı Faktörü (E):",
        "factor_t": "Sıcaklık Derating Faktörü (T):",
        "unit_weight": "Birim Ağırlık (API 5L):",
        "opt_lowest_weight": "En Düşük Ağırlığa Göre Optimize Et",
        "fast_calc": "Hızlı Hesaplama (Büyükleri Atlama)",
        
        # Results Section
        "results_summary": "Özet Tablo",
        "results_schematic": "Sistem Şeması",
        "results_report": "Detaylı Rapor",
        
        # Buttons
        "btn_calculate": "HESAPLA",
        "btn_show_graphs": "Grafikler",
        "btn_save_report": "Raporu Kaydet",
        
        # Schematic Labels
        "schematic_inlet": "GİRİŞ",
        "schematic_outlet": "ÇIKIŞ",
        "schematic_pending": "Hesaplama Bekleniyor",
        "schematic_calculating": "Hesaplanıyor...",
        "schematic_completed": "Hesaplama Tamamlandı",
        "schematic_error": "Hesaplama Hatası",
        "schematic_results": "SON HESAPLAMA SONUÇLARI",
        "schematic_details": "HESAPLAMA DETAYLARI",
        "schematic_selection_details": "SEÇİM DETAYLARI",
        
        # Schematic Targets
        "schematic_target_pressure": "Çıkış Basıncı Hesaplama",
        "schematic_target_length": "Maksimum Hat Uzunluğu",
        "schematic_target_diameter": "Minimum Boru Çapı",
        
        # Schematic Values
        "schematic_p_inlet": "P_giriş",
        "schematic_p_outlet": "P_çıkış",
        "schematic_p_target": "P_hedef",
        "schematic_temp": "Sıcaklık",
        "schematic_flow": "Debi",
        "schematic_length": "Uzunluk",
        "schematic_diameter": "Çap",
        "schematic_velocity": "Hız",
        "schematic_fittings": "Fitting",
        "schematic_unknown": "???",
        
        # Detail Labels
        "detail_reynolds": "Re",
        "detail_friction": "f",
        "detail_laminar": "Laminer",
        "detail_transition": "Geçiş",
        "detail_turbulent": "Türbülanslı",
        "detail_pipe_loss": "Boru",
        "detail_fitting_loss": "Fitting",
        "detail_density": "ρ",
        "detail_min_theoretical": "Min. Teorik Çap",
        "detail_wall_thickness": "Et Kalınlığı",
        "detail_velocity_usage": "Hız Kullanımı",
        "detail_alternatives": "alternatif boru mevcut",
        
        # Log Section
        "log_filter": "Filtre:",
        "log_all": "Tümü",
        "log_info": "INFO",
        "log_warning": "WARNING",
        "log_error": "ERROR",
        "btn_clear_logs": "Temizle",
        
        # Messages
        "msg_program_started": "PROGRAM BAŞLATILDI",
        "msg_version": "Uygulama sürümü",
        "msg_calculation_started": "Hesaplama başlatıldı...",
        "msg_calculation_completed": "Hesaplama başarıyla tamamlandı.",
        "msg_calculation_error": "Hesaplama hatası",
        "msg_starting": "Başlatılıyor...",
        "msg_calculating": "Hesaplanıyor...",
        "msg_completed": "Tamamlandı",
        
        # Validation
        "validation_positive_pressure": "Giriş basıncı pozitif olmalıdır.",
        "validation_positive_temp": "Sıcaklık mutlak sıfırın üzerinde olmalıdır.",
        "validation_positive_flow": "Akış miktarı pozitif olmalıdır.",
        "validation_add_gas": "En az bir gaz bileşeni eklemelisiniz.",
        "validation_positive_length": "Uzunluk pozitif olmalıdır.",
        "validation_positive_diameter": "Dış çap sıfır veya negatif olamaz.",
        "validation_positive_thickness": "Et kalınlığı sıfır veya negatif olamaz.",
        "validation_invalid_geometry": "Geçersiz boru çapı/kalınlığı. İç çap sıfır veya negatif olamaz.",
        
        # Gas Composition
        "gas_composition_warning": "Gaz bileşimi toplamı",
        "gas_composition_normalize": "normalize edilsin mi?",
        "gas_composition_normalized": "Gaz bileşimi normalize edildi",
        
        # Updates
        "update_checking": "Güncellemeler kontrol ediliyor...",
        "update_config_error": "Güncelleme yapılandırması eksik veya bağlantı hatası.",
        "update_new_version": "Yeni sürüm bulundu",
        "update_changes": "Değişiklikler",
        "update_download_ask": "İndirmek ister misiniz?",
        "update_available": "Güncelleme Mevcut",
        "update_up_to_date": "Uygulamanız güncel.",
        "update_downloading": "Son sürüm indiriliyor...",
        "update_downloaded": "Dosya indirildi",
        "update_download_cancelled": "Güncelleme indirme işlemi iptal edildi.",
        "update_save_as": "Güncelleme dosyasını kaydet",
        "update_private_repo_skip": "Otomatik güncelleme kontrolü atlandı. Private repo için GitHub token gerekli.",
        "update_token_required": "Bu repo private durumda. Güncelleme kontrolü için GitHub token girmek ister misiniz?",
        "update_token_prompt": "GitHub Personal Access Token değerini girin. Bu bilgi sadece yerel kullanıcı ayarlarında saklanır.",
        "update_apply_ask": "Şimdi güncellemeyi uygulamak ister misiniz?",
        "update_later": "Daha sonra 'Zip'ten Güncellemeyi Uygula...' menüsünden uygulayabilirsiniz.",
        "update_no_asset": "İndirilebilir bir varlık bulunamadı.",
        "update_exe_ready": "İndirilen dosya bir .exe güncellemesidir. Mevcut programı kapatıp indirilen dosyayı çalıştırarak kurulumu tamamlayabilirsiniz.",
        "update_open_folder_ask": "İndirilen dosyanın bulunduğu klasör açılsın mı?",
        "update_applied": "Güncelleme başarıyla uygulandı. Uygulamayı yeniden başlatmanız önerilir.",
        
        # Dialogs
        "dialog_update": "Güncelleme",
        "dialog_info": "Bilgi",
        "dialog_error": "Hata",
        "dialog_warning": "Uyarı",
        "dialog_confirm": "Onay",
        
        # Tooltips
        "tooltip_factor_f": "Genellikle 0.72 (Sınıf 1 için)",
        "tooltip_factor_e": "Genellikle 1.0 (Dikişsiz veya ERW)",
        "tooltip_factor_t": "Sıcaklık Derating Faktörü (T)\n1.00 (<= 121°C)\n0.967 (135°C)\n0.933 (149°C)",
        
        # Language Change
        "lang_change_title": "Dil Değişikliği",
        "lang_change_message": "Dil değişikliği için uygulamayı yeniden başlatmanız gerekiyor.",
        "lang_restart_now": "Şimdi yeniden başlatılsın mı?",
        
        # Log Headers
        "log_time": "Zaman",
        "log_level": "Seviye",
        "log_message": "Mesaj",
        
        # Report
        "report_saved": "Rapor kaydedildi.",
        "dialog_success": "Başarılı",
        
        # Gas selection
        "select_gas": "Gaz Seçin",
        "delete": "Sil",
        
        # Results table
        "result_parameter": "Parametre",
        "result_value": "Değer",
        "result_unit": "Birim",
        "results_profile_data": "Akış Profili",
        "results_charts": "Grafikler",
        "export_csv": "CSV'ye Aktar",
        "col_distance": "Mesafe (m)",
        "col_pressure": "Basınç (Pa)",
        "col_velocity": "Hız (m/s)",
        "warning_choked": "DİKKAT: Akış boğulma noktasına çok yakın veya sonik hızı aşmak üzere (Mach > 0.8)! Çapı artırmayı değerlendirin.",
        
        # Project
        "project_saved": "Proje kaydedildi.",
        "project_loaded": "Proje yüklendi.",
        "save_error": "Kaydetme hatası",
        "load_error": "Yükleme hatası",
        
        # Results panel
        "calculation_results": "Hesaplama Sonuçları",
        "calculating_progress": "Hesaplanıyor... %",
        "show_graphs": "Grafikleri Göster",
        "save_report": "Raporu Kaydet",
        
        # Menu - Help
        "menu_help": "Yardım",
        "menu_user_guide": "Kullanım Kılavuzu",
        "menu_about": "Hakkında",
        
        # About Dialog
        "about_title": "Hakkında",
        "about_description": "Gaz akış, basınç kaybı ve boru mukavemet hesaplamalarını mühendislik standartlarına göre yapan hesaplama aracı.",
        
        # Changelog Dialog
        "changelog_title": "Güncelleme Notları",
        "changelog_content": """YENİ VE ÖNE ÇIKAN ÖZELLİKLER (V6.1 Güncellemeleri)
=================================================

Versiyon 6.1 Dev Güncellemesi:
------------------------------
1. 🎨 Tamamen Yenilenmiş Modern Arayüz (UI/UX):
- Koyu lacivert vurgulu, "Card" tasarımlı yeni şık renk paleti.
- Yeni "Segmentli Butonlar" ile hızlı Hesaplama Hedefi seçimi.
- Gaz karışımı için renk geçişli % doluluk çubuğu eklendi.
- Footer (alt çubuk) kısmına canlı durum ve hesaplama süresi göstergesi eklendi.

2. 🚀 Çekirdek Performans Optimizasyonları (100x Hız Artışı):
- Standard Density ve Thermodinamik Propertiyler için LRU-style önbellekleme (Cache) sistemi.
- Min. Çap seçimlerinde anlamsız simülasyonları atlayan "Analitik Hız Ön-Filtresi".
- Alternatif boru senaryoları aynı anda hesaplanarak (Threaded Parallel) bekleme süresi ortadan kaldırıldı.

3. 📉 Gelişmiş Sonuç Sekmeleri ve Grafikler:
- P-v ve T-s grafikleri artık ayrı pencerede değil, doğrudan sonuç paneline gömülü.
- Yeni "Profil Verisi" sekmesi ile segment-segment boru içi analiz detayları tablosu.
- Sonuçları kolayca Excel'e aktarabilmek için "CSV İndir" butonu.

4. 📐 Etkileşimli 3B Sistem Şeması:
- Şematik çizim sekmesi 3B boru efekti, renkli ΔP çubuğu ve Hız limito barları ile tamamen yeniden kodlandı.

Önceki 6.1 Özellikleri (Ağırlık Optimizasyonu):
----------------------------------------------
- Minimum Çap hesabında "Alternatif Senaryolar" menüsü ile en düşük ağırlığı ve fiyatı olan boru önerilir.
- "Hızlı Hesaplama" simülasyonları kısaltan bir mod eklendi.""",
        "dont_show_again": "Bir daha gösterme",
        
        # Project

        # User Guide
        "guide_title": "Kullanım Kılavuzu",
        "guide_content": """KULLANIM KILAVUZU
=================

Program, gaz akış, basınç kaybı ve boru mukavemet hesaplamalarını mühendislik standartlarına göre yapar.

1.  GAZ KARIŞIMI:
    • Bileşenleri seçip yüzdeleri girin
    • Canlı Arama ile gaz listesini kolayca filtreleyebilirsiniz
    • Bileşim Türü (Mol % / Kütle %) seçimi yapın

2.  GİRİŞ KOŞULLARI:
    • Giriş Basıncı, Sıcaklık ve birimlerini seçin

3.  AKIŞ VE TASARIM KRİTERLERİ:
    • Akış Değeri ve Maks. Hız limitini girin
    • Tasarım Basıncı, Malzeme ve ASME B31.8 tasarım faktörlerini (F, E, T) belirleyin
    • Bu veriler, boru mukavemet kontrolü için kritik öneme sahiptir

4.  HESAPLAMA SEÇENEKLERİ:
    • Akışkan Özelliği: Akışkanın boru boyunca yoğunluk değişimini ihmal edip 
      etmeyeceğinizi seçin. Uzun boru hatları için "Sıkıştırılabilir" seçilmelidir.
    • Termodinamik Model: Gaz özelliklerini hesaplamak için kullanılacak 
      matematiksel modeli seçin (Örn: Peng-Robinson veya CoolProp).
    • Hesaplanacak Değer:
        - Çıkış Basıncı: Belirtilen uzunluk için çıkış basıncını hesaplar.
        - Maksimum Uzunluk: Giriş ve istenen çıkış basıncı arasındaki 
          maksimum boru uzunluğunu hesaplar.
        - Minimum Çap: Hız limiti ve tasarım basıncına göre en hafif 
          ticari boruyu seçer (ASME B36.10M listesi taranır).

5.  BORU GEOMETRİSİ VE ELEMANLARI:
    • Çap / Et Kalınlığı: Sadece "Çıkış Basıncı" ve "Maksimum Uzunluk" 
      modlarında kullanılır.
    • Boru Elemanları: Boru hattındaki valf ve dirsek gibi ekipmanlardan 
      kaynaklanan lokal kayıpları hesaplamak için adetlerini girin.
    • Kv/Cv girişleri: Küresel vanaların K-faktörünü daha hassas 
      hesaplamaya yarar.

6.  PROGRAM LOGLARI SEKMESİ:
    • Tüm iterasyonlar, kritik kararlar ve hatalar bu sekmede 
      zaman damgasıyla takip edilebilir.
    • Filtre seçenekleri ile sadece belirli seviyeleri görüntüleyebilirsiniz.

NOTLAR:
• Virgül ve nokta ile ondalık sayı girişi desteklenir.
• Hesaplama sırasında ilerleme durumu takip edilebilir.
• Sonuçlar tabloda, şemada ve detaylı rapor olarak görüntülenebilir.
• Proje kaydetme/yükleme ile çalışmalarınızı saklayabilirsiniz.
""",
        
        # Program Details
        "program_details_title": "Program Detayı ve Referanslar",
        "program_details_content": """PROGRAM DETAYI VE REFERANSLAR
=============================

Bu program, Gaz Kompresörleri, Pompalar, Turbo Makinalar ve Akışkanlar Mekaniği alanındaki uzmanlığınızı yansıtacak şekilde tasarlanmıştır.

KULLANILAN TEMEL PRENSİPLER:

1.  AKIM ANALİZİ:
    • Hız Kriteri: Hız kontrolü için minimum gerekli iç çap hesaplanır:
        A_min = Q_akt / v_max
    • Sürtünme Faktörü (f): Darcy-Weisbach denklemi için Colebrook-White 
      korelasyonunun iteratif çözümü kullanılır.
    • Basınç Kaybı (ΔP): Darcy-Weisbach denklemi ve lokal kayıp katsayıları (ΣK):
        ΔP_toplam = f × (L/D_i) × (ρ×v²/2) + ΣK × (ρ×v²/2)
    • Sıkıştırılabilir Akış: İzotermal akış varsayımı altında ortalama 
      koşulların iteratif çözümü.

2.  TERMODİNAMİK MODELLER (Z, ρ, Cp, μ Hesaplamaları):
    • CoolProp (Yüksek Hassasiyet): Helmholtz Serbest Enerji denklemlerine 
      dayalı, en yüksek doğruluk seviyesinde termodinamik özellik hesaplaması 
      yapar. Viskozite hesaplamasındaki kritik nokta hataları, Lee-Kesler/LBC 
      korelasyonlarına dayalı kaba tahmin ile güvenli bir şekilde aşılır.
    • Peng-Robinson (PR EOS): Hidrokarbon işleme endüstrisinde faz denge ve 
      yoğunluk hesaplamaları için Kübik Durum Denklemi standardıdır.
    • Soave-Redlich-Kwong (SRK EOS): PR'a alternatif olarak kullanılan bir 
      diğer yaygın Kübik Durum Denklemi.
    • Pseudo-Critical (Kay's Rule): Karışımın sahte-kritik noktalarını 
      belirleyerek Z faktörünü Standing-Katz diyagramı korelasyonları ile 
      tahmin eden, hızlı mühendislik kestirim modelidir.

3.  BORU MUKAVEMETİ VE SEÇİMİ:
    • Boru Et Kalınlığı (ASME B31.8 - Gaz İletim): 
      Gerekli minimum et kalınlığı (Hoop Stress için):
        t_gerekli = (P_tasarım × D_d) / (2 × SMYS × F × E × T)
      
      P_tasarım: Tasarım Basıncı (Gauge)
      D_d: Dış Çap
      SMYS: Malzemenin Akma Dayanımı
      F, E, T: ASME B31.8 tasarım faktörleri
      
    • Ticari Boru Seçimi: ASME B36.10M-2018 standardına göre listelenen tüm 
      ticari NPS ve Schedule'lar denenir ve hem hız kriterini hem de 
      mukavemet kriterini sağlayan en küçük boru seçilir.

REFERANSLAR:
• ASME B31.8 (Gas Transmission and Distribution Piping Systems)
• ASME B36.10M (Welded and Seamless Wrought Steel Pipe)
• CoolProp Documentation (EOS implementations for fluid properties)
• Peng, D.-Y.; Robinson, D. B. (1976). Ind. Eng. Chem. Fundam., 15(1), 59-64.
• Soave, G. (1972). Chem. Eng. Sci., 27(6), 1197-1203.
• Kay, W.B. (1936). Ind. Eng. Chem., 28(9), 1014-1019.
""",
    },
    
    "en": {
        # App Title
        "app_title": "Natural Gas Calculator",
        
        # Menu - File
        "menu_file": "File",
        "menu_save_project": "Save Project (JSON)",
        "menu_load_project": "Open Project (JSON)",
        "menu_exit": "Exit",
        
        # Menu - Update
        "menu_update": "Update",
        "menu_check_updates": "Check for Updates",
        "menu_download_latest": "Download Latest Version",
        "menu_apply_update": "Apply Update from Zip...",
        "menu_update_config": "Update Configuration...",
        
        # Menu - Language
        "menu_language": "Language",
        "lang_turkish": "Türkçe",
        "lang_english": "English",
        "menu_view": "View",
        "theme_light": "Light Theme",
        "theme_dark": "Dark Theme",
        "theme_contrast": "High Contrast",
        
        # Tabs
        "tab_calculation": "Calculation",
        "tab_logs": "Activity Log",
        
        # Sections
        "section_gas_mixture": "1. Gas Mixture",
        "section_process_conditions": "2. Process Conditions",
        "section_pipe_properties": "3. Pipe and Line Properties",
        "section_design_criteria": "Design Criteria (Min. Diameter Calc.)",
        "section_fittings": "Pipe Fittings (Count)",
        "toggle_fittings_show": "▶ Show Pipe Fittings",
        "toggle_fittings_hide": "▼ Hide Pipe Fittings",
        
        # Gas Section
        "gas_search": "Search Gas:",
        "btn_add_gas": "Add",
        "gas_total": "Total:",
        "composition_type": "Composition Type:",
        "mol_percent": "Mol %",
        "mass_percent": "Mass %",
        "gas_preset": "Preset:",
        "gas_preset_select": "-- Select --",
        
        # Process Section
        "inlet_pressure": "Inlet Pressure:",
        "temperature": "Temperature:",
        "flow_rate": "Flow Rate:",
        "calc_target": "Calculation Target:",
        "thermo_model": "Model:",
        "flow_type": "Flow Type:",
        
        # Calculation Targets
        "target_pressure_drop": "Outlet Pressure",
        "target_max_length": "Maximum Length",
        "target_min_diameter": "Minimum Diameter",
        
        # Flow Types
        "flow_incompressible": "Incompressible",
        "flow_compressible": "Compressible",
        
        # Pipe Section
        "material": "Material:",
        "length": "Length (m):",
        "outer_diameter": "Outer Diameter (mm):",
        "wall_thickness": "Wall Thickness (mm):",
        "nps": "NPS:",
        "schedule": "Schedule:",
        "smys": "SMYS (MPa):",
        "manual_custom": "Manuel / Custom",
        "target_outlet_pressure": "Target Outlet Pressure:",
        "max_velocity": "Max. Velocity (m/s):",
        "design_pressure": "Design Pressure:",
        "factor_f": "Design Factor (F):",
        "factor_e": "Longit. Joint Factor (E):",
        "factor_t": "Temp. Derating Factor (T):",
        "unit_weight": "Unit Weight (API 5L):",
        "tooltip_factor_f": "Usually 0.72 (Class 1)",
        "tooltip_factor_e": "Usually 1.0 (Seamless or ERW)",
        "tooltip_factor_t": "Temp. Derating Factor (T)\n1.00 (<= 121°C)\n0.967 (135°C)\n0.933 (149°C)",
        "btn_show_graphs": "Graphs",
        "btn_save_report": "Save Report",
        
        # Schematic Labels
        "schematic_inlet": "INLET",
        "schematic_outlet": "OUTLET",
        "schematic_pending": "Calculation Pending",
        "schematic_calculating": "Calculating...",
        "schematic_completed": "Calculation Completed",
        "schematic_error": "Calculation Error",
        "schematic_results": "LAST CALCULATION RESULTS",
        "schematic_details": "CALCULATION DETAILS",
        "schematic_selection_details": "SELECTION DETAILS",
        
        # Schematic Targets
        "schematic_target_pressure": "Outlet Pressure Calculation",
        "schematic_target_length": "Maximum Line Length",
        "schematic_target_diameter": "Minimum Pipe Diameter",
        
        # Schematic Values
        "schematic_p_inlet": "P_inlet",
        "schematic_p_outlet": "P_outlet",
        "schematic_p_target": "P_target",
        "schematic_temp": "Temperature",
        "schematic_flow": "Flow Rate",
        "schematic_length": "Length",
        "schematic_diameter": "Diameter",
        "schematic_velocity": "Velocity",
        "schematic_fittings": "Fittings",
        "schematic_unknown": "???",
        
        # Detail Labels
        "detail_reynolds": "Re",
        "detail_friction": "f",
        "detail_laminar": "Laminar",
        "detail_transition": "Transition",
        "detail_turbulent": "Turbulent",
        "detail_pipe_loss": "Pipe",
        "detail_fitting_loss": "Fittings",
        "detail_density": "ρ",
        "detail_min_theoretical": "Min. Theoretical Diameter",
        "detail_wall_thickness": "Wall Thickness",
        "detail_velocity_usage": "Velocity Usage",
        "detail_alternatives": "alternative pipes available",
        
        # Log Section
        "log_filter": "Filter:",
        "log_all": "All",
        "log_info": "INFO",
        "log_warning": "WARNING",
        "log_error": "ERROR",
        "btn_clear_logs": "Clear",
        
        # Messages
        "msg_program_started": "PROGRAM STARTED",
        "msg_version": "Application version",
        "msg_calculation_started": "Calculation started...",
        "msg_calculation_completed": "Calculation completed successfully.",
        "msg_calculation_error": "Calculation error",
        "msg_starting": "Starting...",
        "msg_calculating": "Calculating...",
        "msg_completed": "Completed",
        
        # Validation
        "validation_positive_pressure": "Inlet pressure must be positive.",
        "validation_positive_temp": "Temperature must be above absolute zero.",
        "validation_positive_flow": "Flow rate must be positive.",
        "validation_add_gas": "You must add at least one gas component.",
        "validation_positive_length": "Length must be positive.",
        "validation_positive_diameter": "Outer diameter cannot be zero or negative.",
        "validation_positive_thickness": "Wall thickness cannot be zero or negative.",
        "validation_invalid_geometry": "Invalid pipe geometry. Inner diameter cannot be zero or negative.",
        
        # Gas Composition
        "gas_composition_warning": "Gas composition total is",
        "gas_composition_normalize": "Normalize to 100%?",
        "gas_composition_normalized": "Gas composition normalized",
        
        # Updates
        "update_checking": "Checking for updates...",
        "update_config_error": "Update configuration missing or connection error.",
        "update_new_version": "New version found",
        "update_changes": "Changes",
        "update_download_ask": "Do you want to download?",
        "update_available": "Update Available",
        "update_up_to_date": "Your application is up to date.",
        "update_downloading": "Downloading latest version...",
        "update_downloaded": "File downloaded",
        "update_download_cancelled": "Update download was cancelled.",
        "update_save_as": "Save update file",
        "update_private_repo_skip": "Automatic update check was skipped. A GitHub token is required for the private repository.",
        "update_token_required": "This repository is private. Do you want to enter a GitHub token to check for updates?",
        "update_token_prompt": "Enter your GitHub Personal Access Token. This value is stored only in local user settings.",
        "update_apply_ask": "Do you want to apply the update now?",
        "update_later": "You can apply it later from 'Apply Update from Zip...' menu.",
        "update_no_asset": "No downloadable asset found.",
        "update_exe_ready": "The downloaded file is a .exe update package. Close the current program and run the downloaded file to complete the update.",
        "update_open_folder_ask": "Open the folder that contains the downloaded file?",
        "update_applied": "Update applied successfully. Please restart the application.",
        
        # Dialogs
        "dialog_update": "Update",
        "dialog_info": "Info",
        "dialog_error": "Error",
        "dialog_warning": "Warning",
        "dialog_confirm": "Confirm",
        
        # Tooltips
        "tooltip_factor_f": "Design Factor (F)\nPer ASME B31.8:\n0.72 (Class 1)\n0.60 (Class 2)\n0.50 (Class 3)\n0.40 (Class 4)",
        "tooltip_factor_e": "Longitudinal Joint Factor (E)\n1.00 (Seamless/ERW)\n0.80 (Some spiral welded types)",
        "tooltip_factor_t": "Temperature Derating Factor (T)\n1.00 (<= 250°F)\n0.967 (275°F)\n0.933 (300°F)",
        
        # Language Change
        "lang_change_title": "Language Change",
        "lang_change_message": "The application needs to restart to change the language.",
        "lang_restart_now": "Restart now?",
        
        # Log Headers
        "log_time": "Time",
        "log_level": "Level",
        "log_message": "Message",
        
        # Report
        "report_saved": "Report saved.",
        "dialog_success": "Success",
        
        # Gas selection
        "select_gas": "Select Gas",
        "delete": "Delete",
        
        # Results table
        "result_parameter": "Parameter",
        "result_value": "Value",
        "result_unit": "Unit",
        "results_profile_data": "Profile Data",
        "results_charts": "Charts",
        "export_csv": "Export to CSV",
        "col_distance": "Distance (m)",
        "col_pressure": "Pressure (Pa)",
        "col_velocity": "Velocity (m/s)",
        "warning_choked": "WARNING: Flow is very close to or exceeding sonic velocity (Mach > 0.8)! Consider increasing pipe diameter.",
        
        # Project
        "project_saved": "Project saved.",
        "project_loaded": "Project loaded.",
        "save_error": "Save error",
        "load_error": "Load error",
        
        # Results panel
        "calculation_results": "Calculation Results",
        "calculating_progress": "Calculating... %",
        "show_graphs": "Show Graphs",
        "save_report": "Save Report",
        
        # Menu - Help
        "menu_help": "Help",
        "menu_user_guide": "User Guide",
        "menu_about": "About",
        
        # About Dialog
        "about_title": "About",
        "about_description": "A calculation tool for gas flow, pressure drop and pipe strength analysis according to engineering standards.",

        # Changelog Dialog
        "changelog_title": "Update Notes",
        "changelog_content": """Version 5.0 Core Features:
--------------------------
1. New Thermodynamic Models: Peng-Robinson, SRK and Kay's Rule.
2. Full support for NCM, SCM, and ACM volumetric flow rates.
3. English and Turkish multi-language support.
4. Canvas-based Schematic Viewer and P-v / T-s diagrams.
- Minimum Diameter calculation now suggests the lowest weight (cheapest) pipe under "Alternative Scenarios".
- "Fast Calculation" mode added to drastically shorten full simulation loops.""",
        "dont_show_again": "Do not show again",
        
        # User Guide
        "guide_title": "User Guide",
        "guide_content": """USER GUIDE
=================

This program performs gas flow, pressure drop, and pipe strength calculations according to engineering standards.

1.  GAS MIXTURE:
    • Select components and enter percentages
    • Use Live Search to easily filter the gas list
    • Choose Composition Type (Mol % / Mass %)

2.  INPUT CONDITIONS:
    • Select Inlet Pressure, Temperature and their units

3.  FLOW AND DESIGN CRITERIA:
    • Enter Flow Rate and Max. Velocity limit
    • Specify Design Pressure, Material and ASME B31.8 design factors (F, E, T)
    • This data is critical for pipe strength verification

4.  CALCULATION OPTIONS:
    • Fluid Property: Choose whether to ignore density changes along 
      the pipe. For long pipelines, "Compressible" should be selected.
    • Thermodynamic Model: Select the mathematical model for calculating 
      gas properties (e.g., Peng-Robinson or CoolProp).
    • Calculation Target:
        - Outlet Pressure: Calculates outlet pressure for a given length.
        - Maximum Length: Calculates maximum pipe length between inlet 
          and target outlet pressure.
        - Minimum Diameter: Selects the lightest commercial pipe based 
          on velocity limit and design pressure (ASME B36.10M list).

5.  PIPE GEOMETRY AND FITTINGS:
    • Diameter / Wall Thickness: Used only in "Outlet Pressure" and 
      "Maximum Length" modes.
    • Pipe Fittings: Enter quantities for valves and elbows to calculate 
      local losses from equipment in the pipeline.
    • Kv/Cv inputs: Enable more precise K-factor calculation for 
      ball valves.

6.  ACTIVITY LOG TAB:
    • All iterations, critical decisions and errors can be tracked 
      in this tab with timestamps.
    • Use filter options to display only specific levels.

NOTES:
• Decimal number input with comma and dot is supported.
• Calculation progress can be tracked during execution.
• Results can be viewed in table, schematic and detailed report formats.
• Save/load projects to preserve your work.
""",
        
        # Program Details
        "program_details_title": "Program Details and References",
        "program_details_content": """PROGRAM DETAILS AND REFERENCES
==============================

This program is designed to reflect your expertise in Gas Compressors, Pumps, Turbomachinery, and Fluid Mechanics.

FUNDAMENTAL PRINCIPLES USED:

1.  FLOW ANALYSIS:
    • Velocity Criterion: Minimum required inner diameter is calculated for 
      velocity control:
        A_min = Q_act / v_max
    • Friction Factor (f): Iterative solution of the Colebrook-White 
      correlation for the Darcy-Weisbach equation.
    • Pressure Loss (ΔP): Darcy-Weisbach equation and local loss coefficients (ΣK):
        ΔP_total = f × (L/D_i) × (ρ×v²/2) + ΣK × (ρ×v²/2)
    • Compressible Flow: Iterative solution of average conditions under 
      isothermal flow assumption.

2.  THERMODYNAMIC MODELS (Z, ρ, Cp, μ Calculations):
    • CoolProp (High Accuracy): Thermodynamic property calculations based on 
      Helmholtz Free Energy equations with the highest accuracy level. 
      Critical point errors in viscosity calculations are safely handled 
      using Lee-Kesler/LBC correlation fallback estimates.
    • Peng-Robinson (PR EOS): The standard Cubic Equation of State for phase 
      equilibrium and density calculations in the hydrocarbon processing industry.
    • Soave-Redlich-Kwong (SRK EOS): Another commonly used Cubic Equation of 
      State as an alternative to PR.
    • Pseudo-Critical (Kay's Rule): A fast engineering estimation model that 
      determines the pseudo-critical points of the mixture and estimates the 
      Z factor using Standing-Katz chart correlations.

3.  PIPE STRENGTH AND SELECTION:
    • Wall Thickness (ASME B31.8 - Gas Transmission): 
      Required minimum wall thickness (for Hoop Stress):
        t_required = (P_design × D_o) / (2 × SMYS × F × E × T)
      
      P_design: Design Pressure (Gauge)
      D_o: Outer Diameter
      SMYS: Specified Minimum Yield Strength
      F, E, T: ASME B31.8 design factors
      
    • Commercial Pipe Selection: All commercial NPS and Schedules listed per 
      ASME B36.10M-2018 standard are evaluated, and the smallest pipe meeting 
      both velocity and strength criteria is selected.

REFERENCES:
• ASME B31.8 (Gas Transmission and Distribution Piping Systems)
• ASME B36.10M (Welded and Seamless Wrought Steel Pipe)
• CoolProp Documentation (EOS implementations for fluid properties)
• Peng, D.-Y.; Robinson, D. B. (1976). Ind. Eng. Chem. Fundam., 15(1), 59-64.
• Soave, G. (1972). Chem. Eng. Sci., 27(6), 1197-1203.
• Kay, W.B. (1936). Ind. Eng. Chem., 28(9), 1014-1019.
""",
    }
}

# Fitting names translations
FITTING_TRANSLATIONS = {
    "tr": {
        "90° Dirsek": "90° Dirsek",
        "45° Dirsek": "45° Dirsek",
        "30° Dirsek": "30° Dirsek",
        "60° Dirsek": "60° Dirsek",
        "180° Dirsek": "180° Dirsek",
        "Tee (Doğrudan)": "Tee (Doğrudan)",
        "Tee (Yan Dal)": "Tee (Yan Dal)",
        "Küresel Vana (Tam Açık)": "Küresel Vana (Tam Açık)",
        "Globe Vana (Tam Açık)": "Globe Vana (Tam Açık)",
        "Gate Vana (Tam Açık)": "Gate Vana (Tam Açık)",
        "Check Valve": "Check Valve",
    },
    "en": {
        "90° Dirsek": "90° Elbow",
        "45° Dirsek": "45° Elbow",
        "30° Dirsek": "30° Elbow",
        "60° Dirsek": "60° Elbow",
        "180° Dirsek": "180° U-Bend",
        "Tee (Doğrudan)": "Tee (Run)",
        "Tee (Yan Dal)": "Tee (Branch)",
        "Küresel Vana (Tam Açık)": "Ball Valve (Fully Open)",
        "Globe Vana (Tam Açık)": "Globe Valve (Fully Open)",
        "Gate Vana (Tam Açık)": "Gate Valve (Fully Open)",
        "Check Valve": "Check Valve",
    }
}


def set_language(lang: str):
    """Set the current language."""
    global _current_lang
    if lang in TRANSLATIONS:
        _current_lang = lang


def get_language() -> str:
    """Get the current language code."""
    return _current_lang


def t(key: str, default: str = None) -> str:
    """Get translation for a key."""
    translations = TRANSLATIONS.get(_current_lang, TRANSLATIONS["tr"])
    return translations.get(key, default or key)


def t_fitting(fitting_name: str) -> str:
    """Get translated fitting name."""
    translations = FITTING_TRANSLATIONS.get(_current_lang, FITTING_TRANSLATIONS["tr"])
    return translations.get(fitting_name, fitting_name)


def get_fitting_name_tr(fitting_name_translated: str) -> str:
    """Get Turkish fitting name from translated name (for K factor lookup)."""
    if _current_lang == "tr":
        return fitting_name_translated
    # Reverse lookup
    en_to_tr = {v: k for k, v in FITTING_TRANSLATIONS["en"].items()}
    return en_to_tr.get(fitting_name_translated, fitting_name_translated)

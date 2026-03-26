import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from translations import t

class ResultsPanel(ttk.Frame):
    def __init__(self, parent, app_context, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_context
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self, text=t("calculation_results"), style="Header.TLabel").pack(anchor="w", pady=(0, 5))
        
        # Summary Card (Hesaplama özet kartı)
        self.app.summary_card = tk.Frame(self, bg="#e8f5e9", relief="groove", bd=1, height=40)
        self.app.summary_card.pack(fill="x", pady=(0, 5))
        self.app.summary_card.pack_propagate(False)
        self.app.summary_label = tk.Label(self.app.summary_card, text="", font=("Segoe UI", 10, "bold"),
                                       bg="#e8f5e9", fg="#2e7d32", anchor="center")
        self.app.summary_label.pack(fill="both", expand=True)
        self.app.summary_card.pack_forget()  # Başlangıçta gizle
        
        # Uyarı Afişi (Sonik sınır uyarıları vs)
        self.app.warning_card = tk.Frame(self, bg="#fff3cd", relief="solid", bd=1, height=35)
        self.app.warning_card.pack_propagate(False)
        self.app.warning_label = tk.Label(self.app.warning_card, text="", font=("Segoe UI", 9, "bold"),
                                       bg="#fff3cd", fg="#856404", anchor="center")
        self.app.warning_label.pack(fill="both", expand=True)
        # warning_card gizli başlıyor, hata/uyarı durumunda pack edilecek (summary_card'ın altına)
        
        # Hesapla & Rapor butonları — En çok önce "bottom" olarak paketlenir
        # Böylece genişleyen Notebook'un altına düşmeden her zaman görünür kalır.
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", fill="x", pady=5)
        
        # Progress Button Container
        self.app.progress_container = tk.Frame(btn_frame, bg="#e0e0e0", height=50)
        self.app.progress_container.pack(fill="x")
        self.app.progress_container.pack_propagate(False)
        
        # Progress Bar (Canvas tabanlı)
        self.app.progress_canvas = tk.Canvas(self.app.progress_container, height=50, bg="#28a745",
                                          highlightthickness=0)
        self.app.progress_canvas.pack(fill="both", expand=True)
        
        # Progress değişkenleri
        self.app.progress_value = 0
        self.app.progress_text_id = None
        self.app.progress_bar_id = None
        self.app.is_calculating = False
        
        # İlk durumu çiz
        self.app._draw_progress_button(t("btn_calculate"), 0, idle=True)
        
        # Tıklama olayı
        self.app.progress_canvas.bind("<Button-1>", lambda e: self.app.start_calculation())
        self.app.progress_canvas.bind("<Enter>", self.app._on_progress_hover)
        self.app.progress_canvas.bind("<Leave>", self.app._on_progress_leave)
        self.app.progress_canvas.bind("<Configure>", self.app._on_progress_resize)
        
        ttk.Button(btn_frame, text=t("save_report"), command=self.app.save_report).pack(fill="x", pady=(3, 0))

        # Sonuç Sekmeleri — Butonlardan sonra paketlenir, kalan alanı alır
        self.app.res_notebook = ttk.Notebook(self)
        self.app.res_notebook.pack(fill="both", expand=True)
        
        # 1. Tablo Sekmesi
        self.app.tab_table = ttk.Frame(self.app.res_notebook)
        self.app.res_notebook.add(self.app.tab_table, text=t("results_summary"))
        
        # Treeview
        cols = ("param", "value", "unit")
        self.app.res_tree = ttk.Treeview(self.app.tab_table, columns=cols, show="headings", height=20)
        self.app.res_tree.heading("param", text=t("result_parameter"))
        self.app.res_tree.heading("value", text=t("result_value"))
        self.app.res_tree.heading("unit", text=t("result_unit"))
        
        self.app.res_tree.column("param", width=180)
        self.app.res_tree.column("value", width=100, anchor="e")
        self.app.res_tree.column("unit", width=80, anchor="w")
        
        self.app.res_tree.tag_configure("success", foreground="green")
        self.app.res_tree.tag_configure("warning", foreground="orange")
        self.app.res_tree.tag_configure("error", foreground="red")
        
        self.app.res_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 1.1 Akış Profili Sekmesi (YENİ)
        self.app.tab_profile = ttk.Frame(self.app.res_notebook)
        self.app.res_notebook.add(self.app.tab_profile, text=t("results_profile_data"))
        
        prof_cols = ("distance", "pressure", "velocity")
        self.app.prof_tree = ttk.Treeview(self.app.tab_profile, columns=prof_cols, show="headings", height=15)
        self.app.prof_tree.heading("distance", text=t("col_distance"))
        self.app.prof_tree.heading("pressure", text=t("col_pressure"))
        self.app.prof_tree.heading("velocity", text=t("col_velocity"))
        
        self.app.prof_tree.column("distance", width=100, anchor="center")
        self.app.prof_tree.column("pressure", width=120, anchor="center")
        self.app.prof_tree.column("velocity", width=120, anchor="center")
        
        self.app.prof_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.app.btn_export_csv = ttk.Button(self.app.tab_profile, text=t("export_csv"), command=self.app.export_profile_to_csv, state="disabled")
        self.app.btn_export_csv.pack(pady=5)
        
        # 2. Şematik Görünüm
        self.app.tab_schematic = ttk.Frame(self.app.res_notebook)
        self.app.res_notebook.add(self.app.tab_schematic, text=t("results_schematic"))
        
        self.app.schematic_canvas = tk.Canvas(self.app.tab_schematic, bg="white")
        self.app.schematic_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.app.schematic_canvas.bind("<Configure>", self.app.draw_schematic)

        # 3. Metin Sekmesi
        self.app.tab_text = ttk.Frame(self.app.res_notebook)
        self.app.res_notebook.add(self.app.tab_text, text=t("results_report"))
        
        self.app.report_text = ScrolledText(self.app.tab_text, width=50, height=40, font=("Consolas", 10))
        self.app.report_text.pack(fill="both", expand=True)
        
        # 4. Grafikler Sekmesi (YENİ)
        self.app.tab_charts = ttk.Frame(self.app.res_notebook)
        self.app.res_notebook.add(self.app.tab_charts, text=t("results_charts"))
        self.app.charts_container = ttk.Frame(self.app.tab_charts)
        self.app.charts_container.pack(fill="both", expand=True, padx=5, pady=5)

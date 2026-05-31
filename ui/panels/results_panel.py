import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from translations import t

class ResultsPanel(ttk.Frame):
    def __init__(self, parent, app_context, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_context
        self.widgets = {}
        self.setup_ui()

    def register(self, app):
        vars(app).update(self.widgets)

    def setup_ui(self):
        ttk.Label(self, text=t("calculation_results"), style="Header.TLabel").pack(anchor="w", pady=(0, 5))

        # Summary Card (Hesaplama özet kartı)
        self.widgets['summary_card'] = tk.Frame(self, bg="#e8f5e9", relief="groove", bd=1, height=40)
        self.widgets['summary_card'].pack(fill="x", pady=(0, 5))
        self.widgets['summary_card'].pack_propagate(False)
        self.widgets['summary_label'] = tk.Label(self.widgets['summary_card'], text="", font=(self.app.font_family, 10, "bold"),
                                       bg="#e8f5e9", fg="#2e7d32", anchor="center")
        self.widgets['summary_label'].pack(fill="both", expand=True)
        self.widgets['summary_card'].pack_forget()

        # Uyarı Afişi (Sonik sınır uyarıları vs)
        self.widgets['warning_card'] = tk.Frame(self, bg="#fff3cd", relief="solid", bd=1, height=35)
        self.widgets['warning_card'].pack_propagate(False)
        self.widgets['warning_label'] = tk.Label(self.widgets['warning_card'], text="", font=(self.app.font_family, 9, "bold"),
                                       bg="#fff3cd", fg="#856404", anchor="center")
        self.widgets['warning_label'].pack(fill="both", expand=True)

        # Hesapla & Rapor butonları
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", fill="x", pady=5)

        # Progress Button Container
        self.widgets['progress_container'] = tk.Frame(btn_frame, bg="#e0e0e0", height=50)
        self.widgets['progress_container'].pack(fill="x")
        self.widgets['progress_container'].pack_propagate(False)

        # Progress Bar (Canvas tabanlı)
        self.widgets['progress_canvas'] = tk.Canvas(self.widgets['progress_container'], height=50, bg="#28a745",
                                          highlightthickness=0)
        self.widgets['progress_canvas'].pack(fill="both", expand=True)

        # Progress değişkenleri
        self.widgets['progress_value'] = 0
        self.widgets['progress_text_id'] = None
        self.widgets['progress_bar_id'] = None
        self.widgets['is_calculating'] = False

        # Widget'ları app'e kopyala (register öncesi app metotları erişebilsin)
        vars(self.app).update(self.widgets)

        # İlk durumu çiz
        self.app._draw_progress_button(t("btn_calculate"), 0, idle=True)

        # Tıklama olayı
        self.widgets['progress_canvas'].bind("<Button-1>", lambda e: self.app.start_calculation())
        self.widgets['progress_canvas'].bind("<Enter>", self.app._on_progress_hover)
        self.widgets['progress_canvas'].bind("<Leave>", self.app._on_progress_leave)
        self.widgets['progress_canvas'].bind("<Configure>", self.app._on_progress_resize)

        ttk.Button(btn_frame, text=t("save_report"), command=self.app.save_report).pack(fill="x", pady=(3, 0))

        # Sonuç Sekmeleri
        self.widgets['res_notebook'] = ttk.Notebook(self)
        self.widgets['res_notebook'].pack(fill="both", expand=True)

        # 1. Tablo Sekmesi
        self.widgets['tab_table'] = ttk.Frame(self.widgets['res_notebook'])
        self.widgets['res_notebook'].add(self.widgets['tab_table'], text=t("results_summary"))

        cols = ("param", "value", "unit")
        self.widgets['res_tree'] = ttk.Treeview(self.widgets['tab_table'], columns=cols, show="headings", height=20)
        self.widgets['res_tree'].heading("param", text=t("result_parameter"))
        self.widgets['res_tree'].heading("value", text=t("result_value"))
        self.widgets['res_tree'].heading("unit", text=t("result_unit"))

        self.widgets['res_tree'].column("param", width=180)
        self.widgets['res_tree'].column("value", width=100, anchor="e")
        self.widgets['res_tree'].column("unit", width=80, anchor="w")

        self.widgets['res_tree'].tag_configure("success", foreground="green")
        self.widgets['res_tree'].tag_configure("warning", foreground="orange")
        self.widgets['res_tree'].tag_configure("error", foreground="red")

        self.widgets['res_tree'].pack(fill="both", expand=True, padx=5, pady=5)

        # 1.1 Akış Profili Sekmesi
        self.widgets['tab_profile'] = ttk.Frame(self.widgets['res_notebook'])
        self.widgets['res_notebook'].add(self.widgets['tab_profile'], text=t("results_profile_data"))

        prof_cols = ("distance", "pressure", "velocity")
        self.widgets['prof_tree'] = ttk.Treeview(self.widgets['tab_profile'], columns=prof_cols, show="headings", height=15)
        self.widgets['prof_tree'].heading("distance", text=t("col_distance"))
        self.widgets['prof_tree'].heading("pressure", text=t("col_pressure"))
        self.widgets['prof_tree'].heading("velocity", text=t("col_velocity"))

        self.widgets['prof_tree'].column("distance", width=100, anchor="center")
        self.widgets['prof_tree'].column("pressure", width=120, anchor="center")
        self.widgets['prof_tree'].column("velocity", width=120, anchor="center")

        self.widgets['prof_tree'].pack(fill="both", expand=True, padx=5, pady=5)

        self.widgets['btn_export_csv'] = ttk.Button(self.widgets['tab_profile'], text=t("export_csv"), command=self.app.export_profile_to_csv, state="disabled")
        self.widgets['btn_export_csv'].pack(pady=5)

        # 2. Şematik Görünüm
        self.widgets['tab_schematic'] = ttk.Frame(self.widgets['res_notebook'])
        self.widgets['res_notebook'].add(self.widgets['tab_schematic'], text=t("results_schematic"))

        self.widgets['schematic_canvas'] = tk.Canvas(self.widgets['tab_schematic'], bg="white")
        self.widgets['schematic_canvas'].pack(fill="both", expand=True, padx=5, pady=5)
        self.widgets['schematic_canvas'].bind("<Configure>", self.app.draw_schematic)

        # 3. Metin Sekmesi
        self.widgets['tab_text'] = ttk.Frame(self.widgets['res_notebook'])
        self.widgets['res_notebook'].add(self.widgets['tab_text'], text=t("results_report"))

        self.widgets['report_text'] = ScrolledText(self.widgets['tab_text'], width=50, height=40, font=("Consolas", 10))
        self.widgets['report_text'].pack(fill="both", expand=True)

        # 4. Grafikler Sekmesi
        self.widgets['tab_charts'] = ttk.Frame(self.widgets['res_notebook'])
        self.widgets['res_notebook'].add(self.widgets['tab_charts'], text=t("results_charts"))
        self.widgets['charts_container'] = ttk.Frame(self.widgets['tab_charts'])
        self.widgets['charts_container'].pack(fill="both", expand=True, padx=5, pady=5)

    # ── Results API ──

    def clear_report(self):
        self.widgets['report_text'].delete(1.0, "end")

    def get_report(self):
        return self.widgets['report_text'].get(1.0, "end")

    def append_report(self, text):
        self.widgets['report_text'].insert("end", text)

    def clear_results_table(self):
        for item in self.widgets['res_tree'].get_children():
            self.widgets['res_tree'].delete(item)

    def add_result_row(self, param, value, unit, tag=""):
        return self.widgets['res_tree'].insert("", "end", values=(param, value, unit), tags=(tag,))

    def clear_profile_table(self):
        for item in self.widgets['prof_tree'].get_children():
            self.widgets['prof_tree'].delete(item)

    def add_profile_row(self, distance, pressure, velocity):
        return self.widgets['prof_tree'].insert("", "end", values=(distance, pressure, velocity))

    def enable_csv_export(self, enable=True):
        state = "normal" if enable else "disabled"
        self.widgets['btn_export_csv'].config(state=state)

    def show_warning(self, message):
        self.widgets['warning_label'].config(text=message)
        try:
            self.widgets['warning_card'].pack(fill="x", pady=(0, 5), before=self.widgets['progress_container'].master)
        except tk.TclError:
            self.widgets['warning_card'].pack(fill="x", pady=(0, 5))

    def hide_warning(self):
        self.widgets['warning_card'].pack_forget()

    def show_summary(self, message):
        self.widgets['summary_label'].config(text=message)
        try:
            self.widgets['summary_card'].pack(fill="x", pady=(0, 5), before=self.widgets['warning_card'])
        except tk.TclError:
            self.widgets['summary_card'].pack(fill="x", pady=(0, 5))

    def hide_summary(self):
        self.widgets['summary_card'].pack_forget()

    def set_calculating(self, state):
        self.widgets['is_calculating'] = state
        self.widgets['progress_canvas'].config(cursor="wait" if state else "")

    def set_progress(self, value, text=None):
        self.widgets['progress_value'] = value
        self.app._draw_progress_button(text or f"%{int(value)}", value, idle=(value >= 100))

    def reset_progress(self):
        self.widgets['progress_value'] = 0
        self.widgets['is_calculating'] = False
        self.app._draw_progress_button(t("btn_calculate"), 0, idle=True)

    def select_tab(self, tab_name):
        tab_map = {
            "summary": self.widgets['tab_table'],
            "profile": self.widgets['tab_profile'],
            "schematic": self.widgets['tab_schematic'],
            "report": self.widgets['tab_text'],
            "charts": self.widgets['tab_charts'],
        }
        if tab_name in tab_map:
            self.widgets['res_notebook'].select(tab_map[tab_name])

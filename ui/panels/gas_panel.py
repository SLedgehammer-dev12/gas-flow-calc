import tkinter as tk
from tkinter import ttk
from translations import t
from data import COOLPROP_GASES, GAS_PRESETS


class GasPanel(ttk.LabelFrame):
    def __init__(self, parent, app_context, **kwargs):
        super().__init__(parent,
                         text="⚗  " + t("section_gas_mixture"),
                         style="Bold.TLabelframe",
                         padding=(12, 8),
                         **kwargs)
        self.app = app_context
        self.setup_ui()

    def setup_ui(self):
        # ── Üst Kısım: Arama + Seçim + Ekle ─────────────────
        top = ttk.Frame(self)
        top.pack(fill="x")

        ttk.Label(top, text=t("gas_search")).pack(side="left")
        self.app.gas_search_var = tk.StringVar()
        self.app.gas_search_var.trace_add("write", self.app.filter_gas_list)
        ttk.Entry(top, textvariable=self.app.gas_search_var, width=16).pack(
            side="left", padx=5)

        self.app.gas_combo = ttk.Combobox(
            top,
            values=[g["name"] for g in COOLPROP_GASES.values()],
            width=22, state="readonly")
        self.app.gas_combo.set(t("select_gas"))
        self.app.gas_combo.pack(side="left", padx=5)

        ttk.Button(top, text="＋ " + t("btn_add_gas"),
                   command=self.app.add_gas_component).pack(side="left")

        # ── Preset Satırı ────────────────────────────────────
        preset = ttk.Frame(self)
        preset.pack(fill="x", pady=(5, 0))
        ttk.Label(preset, text=t("gas_preset")).pack(side="left")
        preset_names = [t("gas_preset_select")] + list(GAS_PRESETS.keys())
        self.app.gas_preset_combo = ttk.Combobox(
            preset, values=preset_names, width=18, state="readonly")
        self.app.gas_preset_combo.set(t("gas_preset_select"))
        self.app.gas_preset_combo.pack(side="left", padx=5)
        self.app.gas_preset_combo.bind(
            "<<ComboboxSelected>>", self.app._on_preset_selected)

        # ── Bileşen Listesi (Canvas + Scrollbar) ─────────────
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="x", pady=(6, 0))

        self.app.gas_list_canvas = tk.Canvas(
            list_frame, height=118, highlightthickness=0,
            bg="#ffffff")
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical",
            command=self.app.gas_list_canvas.yview)
        self.app.gas_list_inner = ttk.Frame(self.app.gas_list_canvas)

        self.app.gas_list_inner.bind(
            "<Configure>",
            lambda e: self.app.gas_list_canvas.configure(
                scrollregion=self.app.gas_list_canvas.bbox("all")))
        self.app.gas_list_canvas.create_window(
            (0, 0), window=self.app.gas_list_inner, anchor="nw")
        self.app.gas_list_canvas.configure(
            yscrollcommand=scrollbar.set)

        self.app.gas_list_canvas.pack(side="left", fill="x", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── Alt Bar: Bileşim Türü + Yüzde Progress Bar ───────
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(6, 0))

        ttk.Label(bottom, text=t("composition_type")).pack(side="left")
        self.app.comp_type = ttk.Combobox(
            bottom,
            values=[t("mol_percent"), t("mass_percent")],
            width=10, state="readonly")
        self.app.comp_type.set(t("mol_percent"))
        self.app.comp_type.pack(side="left", padx=5)

        ttk.Separator(bottom, orient="vertical").pack(
            side="left", fill="y", padx=8)

        ttk.Label(bottom, text=t("gas_total") + ":").pack(side="left")
        self.app.gas_total_label = tk.Label(
            bottom, text="0.00 %",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff", fg="#78909c")
        self.app.gas_total_label.pack(side="left", padx=(4, 2))

        self.app.gas_status_label = tk.Label(
            bottom, text="",
            font=("Segoe UI", 10),
            bg="#ffffff", fg="#78909c")
        self.app.gas_status_label.pack(side="left", padx=2)

        # Renkli doluluk çubuğu (toplam % görsel)
        bar_frame = tk.Frame(bottom, bg="#e0e0e0", height=8, width=80,
                             relief="flat")
        bar_frame.pack(side="left", padx=(8, 0), pady=4)
        bar_frame.pack_propagate(False)
        self.app.gas_total_bar = tk.Frame(bar_frame, bg="#43a047", height=8)
        self.app.gas_total_bar.place(x=0, y=0, relheight=1.0, width=0)
        self.app._gas_bar_frame = bar_frame   # referans sakla (update için)

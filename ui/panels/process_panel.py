import tkinter as tk
from tkinter import ttk
from translations import t


class ProcessPanel(ttk.LabelFrame):
    def __init__(self, parent, app_context, **kwargs):
        super().__init__(parent,
                         text="⚙  " + t("section_process_conditions"),
                         style="Bold.TLabelframe",
                         padding=(12, 8),
                         **kwargs)
        self.app = app_context
        self.setup_ui()

    def setup_ui(self):
        grid = ttk.Frame(self)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(4, weight=1)

        # ── Satır 0: Basınç & Sıcaklık ──────────────────────
        ttk.Label(grid, text=t("inlet_pressure")).grid(
            row=0, column=0, sticky="w", pady=6)
        self.app.p_in_var = tk.DoubleVar(value=50.0)
        ttk.Entry(grid, textvariable=self.app.p_in_var, width=10).grid(
            row=0, column=1, padx=5)
        self.app.p_unit = ttk.Combobox(
            grid, values=["Barg", "Bara", "Psig", "Psia"], width=7, state="readonly")
        self.app.p_unit.set("Barg")
        self.app.p_unit.grid(row=0, column=2)

        ttk.Label(grid, text=t("temperature")).grid(
            row=0, column=3, sticky="w", padx=(20, 5))
        self.app.t_var = tk.DoubleVar(value=20.0)
        ttk.Entry(grid, textvariable=self.app.t_var, width=10).grid(
            row=0, column=4, padx=5)
        self.app.t_unit = ttk.Combobox(
            grid, values=["°C", "°F", "K"], width=7, state="readonly")
        self.app.t_unit.set("°C")
        self.app.t_unit.grid(row=0, column=5)

        # ── Satır 1: Debi & Akış türü ────────────────────────
        ttk.Label(grid, text=t("flow_rate")).grid(
            row=1, column=0, sticky="w", pady=6)
        self.app.flow_var = tk.DoubleVar(value=1945000.0)
        ttk.Entry(grid, textvariable=self.app.flow_var, width=10).grid(
            row=1, column=1, padx=5)
        self.app.flow_unit = ttk.Combobox(
            grid, values=["Sm³/h", "kg/s"], width=7, state="readonly")
        self.app.flow_unit.set("Sm³/h")
        self.app.flow_unit.grid(row=1, column=2)

        ttk.Label(grid, text=t("flow_type")).grid(
            row=1, column=3, sticky="w", padx=(20, 5))
        self.app.flow_type = ttk.Combobox(
            grid,
            values=[t("flow_incompressible"), t("flow_compressible")],
            width=14, state="readonly")
        self.app.flow_type.set(t("flow_compressible"))
        self.app.flow_type.grid(row=1, column=4)
        self.app.flow_type.bind("<<ComboboxSelected>>",
                                self.app.update_ui_visibility)

        # ── Satır 2: Termodinamik Model ──────────────────────
        ttk.Label(grid, text=t("thermo_model")).grid(
            row=2, column=0, sticky="w", pady=6)
        self.app.thermo_model = ttk.Combobox(grid, values=[
            "CoolProp (High Accuracy EOS)",
            "Peng-Robinson (PR EOS)",
            "Soave-Redlich-Kwong (SRK EOS)",
            "Pseudo-Critical (Kay's Rule)"
        ], width=30, state="readonly")
        self.app.thermo_model.set("CoolProp (High Accuracy EOS)")
        self.app.thermo_model.grid(row=2, column=1, columnspan=5,
                                   sticky="w", padx=5)

        # ── Satır 3: Hesaplama Hedefi (Segmented Buttons) ────
        ttk.Separator(self, orient="horizontal").pack(
            fill="x", pady=(8, 6))

        seg_label = ttk.Label(self,
                              text=t("calc_target") + ":",
                              style="Hint.TLabel")
        seg_label.pack(anchor="w")

        seg_frame = ttk.Frame(self)
        seg_frame.pack(fill="x", pady=(4, 0))

        self.app.calc_target = tk.StringVar(
            value=t("target_min_diameter"))

        targets = [
            ("📉  " + t("target_pressure_drop"), t("target_pressure_drop")),
            ("📏  " + t("target_max_length"),    t("target_max_length")),
            ("⭕  " + t("target_min_diameter"),  t("target_min_diameter")),
        ]

        self.app._seg_buttons = {}
        for label_text, val in targets:
            btn = ttk.Button(
                seg_frame,
                text=label_text,
                style="SegBtnActive.TButton" if val == self.app.calc_target.get()
                      else "SegBtn.TButton",
                command=lambda v=val: self._on_seg_click(v)
            )
            btn.pack(side="left", padx=(0, 4), pady=2)
            self.app._seg_buttons[val] = btn

    def _on_seg_click(self, val):
        """Segmented buton tıklamasında stil güncelle ve event tetikle."""
        self.app.calc_target.set(val)

    def get(self):
        """Mevcut hesaplama hedefini döndürür (Combobox uyumlu arayüz)."""
        return self.app.calc_target.get()

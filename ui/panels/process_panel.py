import tkinter as tk
from tkinter import ttk
from translations import t
from target_utils import (
    TARGET_PRESSURE_DROP,
    TARGET_MAX_LENGTH,
    TARGET_MIN_DIAMETER,
)
from ui.widgets import ValidatedEntry


class ProcessPanel(ttk.LabelFrame):
    def __init__(self, parent, app_context, **kwargs):
        super().__init__(
            parent,
            text="⚙  " + t("section_process_conditions"),
            style="Bold.TLabelframe",
            padding=(12, 8),
            **kwargs,
        )
        self.app = app_context
        self.widgets = {}
        self.setup_ui()

    def register(self, app):
        vars(app).update(self.widgets)

    def setup_ui(self):
        grid = ttk.Frame(self)
        grid.pack(fill="x")
        grid.columnconfigure(6, weight=1)

        # Row 0: Pressure + Temperature
        ttk.Label(grid, text=t("inlet_pressure")).grid(row=0, column=0, sticky="w", pady=6)
        self.widgets['p_in_var'] = tk.DoubleVar(value=50.0)
        ValidatedEntry(
            grid,
            textvariable=self.widgets['p_in_var'],
            width=10,
            validation_type="float",
            min_value=0.0001,
            allow_zero=False,
            allow_negative=False
        ).grid(row=0, column=1, padx=(4, 4), sticky="w")

        self.widgets['p_unit'] = ttk.Combobox(
            grid, values=["Barg", "Bara", "Psig", "Psia"], width=7, state="readonly"
        )
        self.widgets['p_unit'].set("Barg")
        self.widgets['p_unit'].grid(row=0, column=2, padx=(0, 10), sticky="w")

        ttk.Label(grid, text=t("temperature")).grid(row=0, column=3, sticky="w", padx=(4, 4))
        self.widgets['t_var'] = tk.DoubleVar(value=20.0)
        ValidatedEntry(
            grid,
            textvariable=self.widgets['t_var'],
            width=10,
            validation_type="float",
            min_value=-273.15,
            allow_zero=True,
            allow_negative=True
        ).grid(row=0, column=4, padx=(4, 4), sticky="w")

        self.widgets['t_unit'] = ttk.Combobox(
            grid, values=["°C", "°F", "K"], width=7, state="readonly"
        )
        self.widgets['t_unit'].set("°C")
        self.widgets['t_unit'].grid(row=0, column=5, sticky="w")

        # Row 1: Flow + Flow Type
        ttk.Label(grid, text=t("flow_rate")).grid(row=1, column=0, sticky="w", pady=6)
        self.widgets['flow_var'] = tk.DoubleVar(value=1945000.0)
        ValidatedEntry(
            grid,
            textvariable=self.widgets['flow_var'],
            width=10,
            validation_type="float",
            min_value=0.0001,
            allow_zero=False,
            allow_negative=False
        ).grid(row=1, column=1, padx=(4, 4), sticky="w")

        self.widgets['flow_unit'] = ttk.Combobox(
            grid, values=["Sm³/h", "kg/s"], width=7, state="readonly"
        )
        self.widgets['flow_unit'].set("Sm³/h")
        self.widgets['flow_unit'].grid(row=1, column=2, padx=(0, 10), sticky="w")

        ttk.Label(grid, text=t("flow_type")).grid(row=1, column=3, sticky="w", padx=(4, 4))
        self.widgets['flow_type'] = ttk.Combobox(
            grid,
            values=[t("flow_incompressible"), t("flow_compressible")],
            width=14,
            state="readonly",
        )
        self.widgets['flow_type'].set(t("flow_compressible"))
        self.widgets['flow_type'].grid(row=1, column=4, columnspan=2, sticky="w")
        self.widgets['flow_type'].bind("<<ComboboxSelected>>", self.app.update_ui_visibility)

        # Row 2: Thermodynamic model
        ttk.Label(grid, text=t("thermo_model")).grid(row=2, column=0, sticky="w", pady=6)
        self.widgets['thermo_model'] = ttk.Combobox(
            grid,
            values=[
                "CoolProp (High Accuracy EOS)",
                "AGA-8 GERG-2008",
                "AGA-8 DETAIL",
                "Peng-Robinson (PR EOS)",
                "Soave-Redlich-Kwong (SRK EOS)",
                "Pseudo-Critical (Kay's Rule)",
                "GERG-88 (Virial EOS)",
            ],
            width=34,
            state="readonly",
        )
        self.widgets['thermo_model'].set("CoolProp (High Accuracy EOS)")
        self.widgets['thermo_model'].grid(row=2, column=1, columnspan=5, sticky="w", padx=(4, 4))

        # Row 3: Calculation target
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(8, 6))

        seg_label = ttk.Label(self, text=t("calc_target") + ":", style="Hint.TLabel")
        seg_label.pack(anchor="w")

        seg_frame = ttk.Frame(self)
        seg_frame.pack(fill="x", pady=(4, 0))

        self.widgets['calc_target'] = tk.StringVar(value=TARGET_MIN_DIAMETER)

        targets = [
            ("📉  " + t("target_pressure_drop"), TARGET_PRESSURE_DROP),
            ("📏  " + t("target_max_length"), TARGET_MAX_LENGTH),
            ("⭕  " + t("target_min_diameter"), TARGET_MIN_DIAMETER),
        ]

        self.widgets['_seg_buttons'] = {}
        for label_text, val in targets:
            btn = ttk.Button(
                seg_frame,
                text=label_text,
                style="SegBtnActive.TButton" if val == self.widgets['calc_target'].get() else "SegBtn.TButton",
                command=lambda v=val: self._on_seg_click(v),
            )
            btn.pack(side="left", padx=(0, 4), pady=2)
            self.widgets['_seg_buttons'][val] = btn

    def _on_seg_click(self, val):
        self.widgets['calc_target'].set(val)

    def get(self):
        return self.widgets['calc_target'].get()

import tkinter as tk
from tkinter import ttk
from translations import t, t_fitting
from data import PIPE_MATERIALS, ASME_B36_10M_DATA, FITTING_K_FACTORS
from ui.widgets import ToolTip, ValidatedEntry

class PipePanel(ttk.LabelFrame):
    def __init__(self, parent, app_context, **kwargs):
        super().__init__(parent, text=t("section_pipe_properties"), style="Bold.TLabelframe", padding=10, **kwargs)
        self.app = app_context
        self.widgets = {}
        self.setup_ui()

    def register(self, app):
        vars(app).update(self.widgets)
        # fitting_counts dict is special — share the same dict object
        if 'fitting_counts' in self.widgets:
            app.fitting_counts = self.widgets['fitting_counts']

    def setup_ui(self):
        # Boru Geometrisi
        geo_frame = ttk.Frame(self)
        geo_frame.pack(fill="x", pady=5)

        # Row 0: Material + SMYS + Length
        ttk.Label(geo_frame, text=t("material")).grid(row=0, column=0, sticky="w")
        self.widgets['material_combo'] = ttk.Combobox(geo_frame, values=list(PIPE_MATERIALS.keys()), width=25, state="readonly")
        self.widgets['material_combo'].set("API 5L Grade B")
        self.widgets['material_combo'].grid(row=0, column=1, padx=5)
        self.widgets['material_combo'].bind("<<ComboboxSelected>>", self._on_material_changed)

        ttk.Label(geo_frame, text=t("smys")).grid(row=0, column=2, padx=(15, 5))
        self.widgets['smys_var'] = tk.DoubleVar(value=PIPE_MATERIALS.get("API 5L Grade B", 241))
        self.widgets['ent_smys'] = ValidatedEntry(
            geo_frame,
            textvariable=self.widgets['smys_var'],
            width=8,
            validation_type="float",
            min_value=0.001,
            allow_zero=False,
            allow_negative=False
        )
        self.widgets['ent_smys'].grid(row=0, column=3)
        self.widgets['ent_smys'].config(state="disabled")

        self.widgets['lbl_len'] = ttk.Label(geo_frame, text=t("length"))
        self.widgets['lbl_len'].grid(row=0, column=4, padx=(15, 5))
        self.widgets['len_var'] = tk.DoubleVar(value=100)
        self.widgets['ent_len'] = ValidatedEntry(
            geo_frame,
            textvariable=self.widgets['len_var'],
            width=10,
            validation_type="float",
            min_value=0.0001,
            allow_zero=False,
            allow_negative=False
        )
        self.widgets['ent_len'].grid(row=0, column=5)

        # Row 1: NPS + Schedule + OD + WT
        nps_keys = list(ASME_B36_10M_DATA.keys())
        ttk.Label(geo_frame, text=t("nps")).grid(row=1, column=0, sticky="w", pady=5)
        self.widgets['nps_combo'] = ttk.Combobox(geo_frame, values=nps_keys, width=10, state="readonly")
        self.widgets['nps_combo'].grid(row=1, column=1, padx=5, sticky="w")
        self.widgets['nps_combo'].bind("<<ComboboxSelected>>", self._on_nps_changed)

        ttk.Label(geo_frame, text=t("schedule")).grid(row=1, column=2, padx=(15, 5))
        self.widgets['schedule_combo'] = ttk.Combobox(geo_frame, values=[], width=12, state="readonly")
        self.widgets['schedule_combo'].grid(row=1, column=3)
        self.widgets['schedule_combo'].bind("<<ComboboxSelected>>", self._on_schedule_changed)

        self.widgets['lbl_diam'] = ttk.Label(geo_frame, text=t("outer_diameter"))
        self.widgets['lbl_diam'].grid(row=1, column=4, padx=(15, 5))
        self.widgets['diam_var'] = tk.DoubleVar()
        self.widgets['ent_diam'] = ValidatedEntry(
            geo_frame,
            textvariable=self.widgets['diam_var'],
            width=10,
            validation_type="float",
            min_value=0.0001,
            allow_zero=False,
            allow_negative=False
        )
        self.widgets['ent_diam'].grid(row=1, column=5)

        self.widgets['lbl_thick'] = ttk.Label(geo_frame, text=t("wall_thickness"))
        self.widgets['lbl_thick'].grid(row=2, column=0, sticky="w", pady=5)
        self.widgets['thick_var'] = tk.DoubleVar()
        self.widgets['ent_thick'] = ValidatedEntry(
            geo_frame,
            textvariable=self.widgets['thick_var'],
            width=10,
            validation_type="float",
            min_value=0.0001,
            allow_zero=False,
            allow_negative=False
        )
        self.widgets['ent_thick'].grid(row=2, column=1, padx=5)

        # Ekstra Hedef Girdileri (Dinamik)
        self.widgets['lbl_target_p'] = ttk.Label(geo_frame, text=t("target_outlet_pressure"))
        self.widgets['target_p_var'] = tk.DoubleVar()
        self.widgets['ent_target_p'] = ValidatedEntry(
            geo_frame,
            textvariable=self.widgets['target_p_var'],
            width=10,
            validation_type="float",
            min_value=0.0001,
            allow_zero=False,
            allow_negative=False
        )
        self.widgets['target_p_unit'] = ttk.Combobox(geo_frame, values=["Barg", "Bara", "Psig", "Psia"], width=8, state="readonly")
        self.widgets['target_p_unit'].set("Barg")

        self.widgets['lbl_max_vel'] = ttk.Label(geo_frame, text=t("max_velocity"))
        self.widgets['max_vel_var'] = tk.DoubleVar(value=20)
        self.widgets['ent_max_vel'] = ValidatedEntry(
            geo_frame,
            textvariable=self.widgets['max_vel_var'],
            width=10,
            validation_type="float",
            min_value=0.0001,
            allow_zero=False,
            allow_negative=False
        )

        # Tasarım Faktörleri (Min Çap için)
        self.widgets['design_frame'] = ttk.LabelFrame(self, text=t("section_design_criteria"), padding=5)

        ttk.Label(self.widgets['design_frame'], text=t("design_pressure")).grid(row=0, column=0, sticky="w")
        self.widgets['p_design_var'] = tk.DoubleVar(value=82.5)
        self.widgets['ent_p_design'] = ValidatedEntry(
            self.widgets['design_frame'],
            textvariable=self.widgets['p_design_var'],
            width=10,
            validation_type="float",
            min_value=0.0001,
            allow_zero=False,
            allow_negative=False
        )
        self.widgets['ent_p_design'].grid(row=0, column=1, padx=5)
        self.widgets['p_design_unit'] = ttk.Combobox(self.widgets['design_frame'], values=["Barg", "Bara", "Psig", "Psia"], width=8, state="readonly")
        self.widgets['p_design_unit'].set("Barg")
        self.widgets['p_design_unit'].grid(row=0, column=2)

        ttk.Label(self.widgets['design_frame'], text=t("factor_f")).grid(row=0, column=3, padx=(15, 5))
        self.widgets['factor_f'] = tk.DoubleVar(value=0.72)
        self.widgets['ent_factor_f'] = ValidatedEntry(
            self.widgets['design_frame'],
            textvariable=self.widgets['factor_f'],
            width=6,
            validation_type="float",
            min_value=0.01,
            max_value=1.0,
            allow_zero=False,
            allow_negative=False
        )
        self.widgets['ent_factor_f'].grid(row=0, column=4)
        ToolTip(self.widgets['ent_factor_f'], t("tooltip_factor_f"))

        ttk.Label(self.widgets['design_frame'], text=t("factor_e")).grid(row=0, column=5, padx=(15, 5))
        self.widgets['factor_e'] = tk.DoubleVar(value=1.0)
        self.widgets['ent_factor_e'] = ValidatedEntry(
            self.widgets['design_frame'],
            textvariable=self.widgets['factor_e'],
            width=6,
            validation_type="float",
            min_value=0.01,
            max_value=1.0,
            allow_zero=False,
            allow_negative=False
        )
        self.widgets['ent_factor_e'].grid(row=0, column=6)
        ToolTip(self.widgets['ent_factor_e'], t("tooltip_factor_e"))

        ttk.Label(self.widgets['design_frame'], text=t("factor_t")).grid(row=0, column=7, padx=(15, 5))
        self.widgets['factor_t'] = tk.DoubleVar(value=1.0)
        self.widgets['ent_factor_t'] = ValidatedEntry(
            self.widgets['design_frame'],
            textvariable=self.widgets['factor_t'],
            width=6,
            validation_type="float",
            min_value=0.01,
            max_value=1.0,
            allow_zero=False,
            allow_negative=False
        )
        self.widgets['ent_factor_t'].grid(row=0, column=8)
        ToolTip(self.widgets['ent_factor_t'], t("tooltip_factor_t"))

        # Optimizasyon Seçenekleri (Min Çap için)
        self.widgets['opt_weight_var'] = tk.BooleanVar(value=False)
        self.widgets['chk_opt_weight'] = ttk.Checkbutton(self.widgets['design_frame'], text=t("opt_lowest_weight"), variable=self.widgets['opt_weight_var'])
        self.widgets['chk_opt_weight'].grid(row=1, column=0, columnspan=4, padx=5, pady=(10, 0), sticky="w")

        self.widgets['fast_calc_var'] = tk.BooleanVar(value=True)
        self.widgets['chk_fast_calc'] = ttk.Checkbutton(self.widgets['design_frame'], text=t("fast_calc"), variable=self.widgets['fast_calc_var'])
        self.widgets['chk_fast_calc'].grid(row=1, column=4, columnspan=5, padx=5, pady=(10, 0), sticky="w")

        # Boru Elemanları (Fittings) — Collapsible
        self.widgets['_fittings_visible'] = False
        self.widgets['fit_toggle_btn'] = ttk.Button(self, text=t("toggle_fittings_show"),
                                          command=self._toggle_fittings)
        self.widgets['fit_toggle_btn'].pack(fill="x", pady=(10, 0))

        self.widgets['fit_frame'] = ttk.LabelFrame(self, text=t("section_fittings"), padding=5)

        # 2 Kolonlu Fittings Düzeni
        items = list(FITTING_K_FACTORS.keys())
        half = (len(items) + 1) // 2

        self.widgets['fitting_counts'] = {}
        for i, item in enumerate(items):
            col = 0 if i < half else 3
            row = i if i < half else i - half

            ttk.Label(self.widgets['fit_frame'], text=t_fitting(item)).grid(row=row, column=col, sticky="w", padx=5, pady=2)
            var = tk.IntVar(value=0)
            self.widgets['fitting_counts'][item] = var
            var.trace_add("write", lambda *args, v=var: self._clamp_fitting_value(v))
            ValidatedEntry(
                self.widgets['fit_frame'],
                textvariable=var,
                width=5,
                validation_type="int",
                min_value=0,
                allow_negative=False
            ).grid(row=row, column=col+1, padx=5)

            if item == "Küresel Vana (Tam Açık)":
                ttk.Label(self.widgets['fit_frame'], text="Kv:").grid(row=row, column=col+2)
                ValidatedEntry(
                    self.widgets['fit_frame'],
                    textvariable=self.app.ball_valve_kv,
                    width=5,
                    validation_type="float",
                    min_value=0.0,
                    allow_negative=False
                ).grid(row=row, column=col+3, padx=5)

    # ── Pipe Panel Methods ──

    def _on_nps_changed(self, event=None):
        from data import ASME_B36_10M_DATA
        nps = self.app.nps_combo.get()
        if nps in ASME_B36_10M_DATA:
            data = ASME_B36_10M_DATA[nps]
            schedules = list(data["schedules"].keys())
            self.app.schedule_combo.config(values=schedules)
            self.app.schedule_combo.set("")
            self.app.diam_var.set(data["OD_mm"])
            self.app.thick_var.set(0)
            self.app.ent_diam.config(state="readonly")
            self.app.ent_thick.config(state="readonly")

    def _on_schedule_changed(self, event=None):
        from data import ASME_B36_10M_DATA
        nps = self.app.nps_combo.get()
        schedule = self.app.schedule_combo.get()
        if nps in ASME_B36_10M_DATA and schedule:
            data = ASME_B36_10M_DATA[nps]
            self.app.diam_var.set(data["OD_mm"])
            wt = data["schedules"].get(schedule, 0)
            self.app.thick_var.set(wt)
            self.app.ent_diam.config(state="readonly")
            self.app.ent_thick.config(state="readonly")

    def _toggle_fittings(self):
        from translations import t
        if self.app._fittings_visible:
            self.app.fit_frame.pack_forget()
            self.app.fit_toggle_btn.config(text=t("toggle_fittings_show"))
        else:
            self.app.fit_frame.pack(fill="x", pady=(0, 10))
            self.app.fit_toggle_btn.config(text=t("toggle_fittings_hide"))
        self.app._fittings_visible = not self.app._fittings_visible

    def _on_material_changed(self, event=None):
        from data import PIPE_MATERIALS
        material = self.app.material_combo.get()
        if material == "Manuel / Custom":
            self.app.ent_smys.config(state="normal")
            self.app.smys_var.set(0)
        else:
            smys = PIPE_MATERIALS.get(material, 0)
            self.app.smys_var.set(smys)
            self.app.ent_smys.config(state="disabled")

    def _clamp_fitting_value(self, var):
        try:
            val = var.get()
            if val < 0:
                var.set(0)
        except (tk.TclError, ValueError):
            pass

    # ── PipePanel Visibility API ──

    def show_length(self, show=True):
        if show:
            self.widgets['lbl_len'].grid(); self.widgets['ent_len'].grid()
        else:
            self.widgets['lbl_len'].grid_remove(); self.widgets['ent_len'].grid_remove()

    def show_target_pressure(self, show=True):
        if show:
            self.widgets['lbl_target_p'].grid(row=2, column=2, padx=(15, 5), sticky="w")
            self.widgets['ent_target_p'].grid(row=2, column=3)
            self.widgets['target_p_unit'].grid(row=2, column=4)
        else:
            self.widgets['lbl_target_p'].grid_remove()
            self.widgets['ent_target_p'].grid_remove()
            self.widgets['target_p_unit'].grid_remove()

    def show_max_velocity(self, show=True):
        if show:
            self.widgets['lbl_max_vel'].grid(row=2, column=4, padx=(15, 5))
            self.widgets['ent_max_vel'].grid(row=2, column=5)
        else:
            self.widgets['lbl_max_vel'].grid_remove()
            self.widgets['ent_max_vel'].grid_remove()

    def show_design_frame(self, show=True):
        if show:
            self.widgets['design_frame'].pack(fill="x", pady=(10, 0), before=self.widgets['fit_toggle_btn'])
        else:
            self.widgets['design_frame'].pack_forget()

    def show_nps_schedule(self, show=True):
        if show:
            self.widgets['nps_combo'].grid()
            self.widgets['schedule_combo'].grid()
        else:
            self.widgets['nps_combo'].grid_remove()
            self.widgets['schedule_combo'].grid_remove()

    def show_diameter_thickness(self, show=True):
        if show:
            self.widgets['lbl_diam'].grid(row=1, column=4, padx=(15, 5))
            self.widgets['ent_diam'].grid(row=1, column=5)
            self.widgets['lbl_thick'].grid(row=2, column=0, sticky="w", pady=5)
            self.widgets['ent_thick'].grid(row=2, column=1, padx=5)
        else:
            self.widgets['lbl_diam'].grid_remove()
            self.widgets['ent_diam'].grid_remove()
            self.widgets['lbl_thick'].grid_remove()
            self.widgets['ent_thick'].grid_remove()

    def lock_pipe_fields(self, lock=True):
        state = "disabled" if lock else "readonly"
        self.widgets['nps_combo'].config(state=state)
        self.widgets['schedule_combo'].config(state=state)
        self.widgets['ent_diam'].config(state=state)
        self.widgets['ent_thick'].config(state=state)

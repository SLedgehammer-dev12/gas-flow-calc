import tkinter as tk
from tkinter import ttk
from translations import t, t_fitting
from data import PIPE_MATERIALS, ASME_B36_10M_DATA, FITTING_K_FACTORS
from ui.widgets import ToolTip

class PipePanel(ttk.LabelFrame):
    def __init__(self, parent, app_context, **kwargs):
        super().__init__(parent, text=t("section_pipe_properties"), style="Bold.TLabelframe", padding=10, **kwargs)
        self.app = app_context
        self.setup_ui()

    def setup_ui(self):
        # Boru Geometrisi
        geo_frame = ttk.Frame(self)
        geo_frame.pack(fill="x", pady=5)
        
        # Row 0: Material + SMYS + Length
        ttk.Label(geo_frame, text=t("material")).grid(row=0, column=0, sticky="w")
        self.app.material_combo = ttk.Combobox(geo_frame, values=list(PIPE_MATERIALS.keys()), width=25, state="readonly")
        self.app.material_combo.set("API 5L Grade B")
        self.app.material_combo.grid(row=0, column=1, padx=5)
        self.app.material_combo.bind("<<ComboboxSelected>>", self.app._on_material_changed)
        
        ttk.Label(geo_frame, text=t("smys")).grid(row=0, column=2, padx=(15, 5))
        self.app.smys_var = tk.DoubleVar(value=PIPE_MATERIALS.get("API 5L Grade B", 241))
        self.app.ent_smys = ttk.Entry(geo_frame, textvariable=self.app.smys_var, width=8)
        self.app.ent_smys.grid(row=0, column=3)
        self.app.ent_smys.config(state="disabled")  # Varsayılan: otomatik
        
        self.app.lbl_len = ttk.Label(geo_frame, text=t("length"))
        self.app.lbl_len.grid(row=0, column=4, padx=(15, 5))
        self.app.len_var = tk.DoubleVar(value=100)
        self.app.ent_len = ttk.Entry(geo_frame, textvariable=self.app.len_var, width=10)
        self.app.ent_len.grid(row=0, column=5)
        
        # Row 1: NPS + Schedule + OD + WT
        nps_keys = list(ASME_B36_10M_DATA.keys())
        ttk.Label(geo_frame, text=t("nps")).grid(row=1, column=0, sticky="w", pady=5)
        self.app.nps_combo = ttk.Combobox(geo_frame, values=nps_keys, width=10, state="readonly")
        self.app.nps_combo.grid(row=1, column=1, padx=5, sticky="w")
        self.app.nps_combo.bind("<<ComboboxSelected>>", self.app._on_nps_changed)
        
        ttk.Label(geo_frame, text=t("schedule")).grid(row=1, column=2, padx=(15, 5))
        self.app.schedule_combo = ttk.Combobox(geo_frame, values=[], width=12, state="readonly")
        self.app.schedule_combo.grid(row=1, column=3)
        self.app.schedule_combo.bind("<<ComboboxSelected>>", self.app._on_schedule_changed)
        
        self.app.lbl_diam = ttk.Label(geo_frame, text=t("outer_diameter"))
        self.app.lbl_diam.grid(row=1, column=4, padx=(15, 5))
        self.app.diam_var = tk.DoubleVar()
        self.app.ent_diam = ttk.Entry(geo_frame, textvariable=self.app.diam_var, width=10)
        self.app.ent_diam.grid(row=1, column=5)
        
        self.app.lbl_thick = ttk.Label(geo_frame, text=t("wall_thickness"))
        self.app.lbl_thick.grid(row=2, column=0, sticky="w", pady=5)
        self.app.thick_var = tk.DoubleVar()
        self.app.ent_thick = ttk.Entry(geo_frame, textvariable=self.app.thick_var, width=10)
        self.app.ent_thick.grid(row=2, column=1, padx=5)

        # Ekstra Hedef Girdileri (Dinamik)
        self.app.lbl_target_p = ttk.Label(geo_frame, text=t("target_outlet_pressure"))
        self.app.target_p_var = tk.DoubleVar()
        self.app.ent_target_p = ttk.Entry(geo_frame, textvariable=self.app.target_p_var, width=10)
        self.app.target_p_unit = ttk.Combobox(geo_frame, values=["Barg", "Bara", "Psig", "Psia"], width=8, state="readonly")
        self.app.target_p_unit.set("Barg")
        
        self.app.lbl_max_vel = ttk.Label(geo_frame, text=t("max_velocity"))
        self.app.max_vel_var = tk.DoubleVar(value=20)
        self.app.ent_max_vel = ttk.Entry(geo_frame, textvariable=self.app.max_vel_var, width=10)


        # Tasarım Faktörleri (Min Çap için)
        self.app.design_frame = ttk.LabelFrame(self, text=t("section_design_criteria"), padding=5)

        ttk.Label(self.app.design_frame, text=t("design_pressure")).grid(row=0, column=0, sticky="w")
        self.app.p_design_var = tk.DoubleVar(value=82.5)
        self.app.ent_p_design = ttk.Entry(self.app.design_frame, textvariable=self.app.p_design_var, width=10)
        self.app.ent_p_design.grid(row=0, column=1, padx=5)
        self.app.p_design_unit = ttk.Combobox(self.app.design_frame, values=["Barg", "Bara", "Psig", "Psia"], width=8, state="readonly")
        self.app.p_design_unit.set("Barg")
        self.app.p_design_unit.grid(row=0, column=2)

        ttk.Label(self.app.design_frame, text=t("factor_f")).grid(row=0, column=3, padx=(15, 5))
        self.app.factor_f = tk.DoubleVar(value=0.72)
        self.app.ent_factor_f = ttk.Entry(self.app.design_frame, textvariable=self.app.factor_f, width=6)
        self.app.ent_factor_f.grid(row=0, column=4)
        ToolTip(self.app.ent_factor_f, t("tooltip_factor_f"))

        ttk.Label(self.app.design_frame, text=t("factor_e")).grid(row=0, column=5, padx=(15, 5))
        self.app.factor_e = tk.DoubleVar(value=1.0)
        self.app.ent_factor_e = ttk.Entry(self.app.design_frame, textvariable=self.app.factor_e, width=6)
        self.app.ent_factor_e.grid(row=0, column=6)
        ToolTip(self.app.ent_factor_e, t("tooltip_factor_e"))

        ttk.Label(self.app.design_frame, text=t("factor_t")).grid(row=0, column=7, padx=(15, 5))
        self.app.factor_t = tk.DoubleVar(value=1.0)
        self.app.ent_factor_t = ttk.Entry(self.app.design_frame, textvariable=self.app.factor_t, width=6)
        self.app.ent_factor_t.grid(row=0, column=8)
        ToolTip(self.app.ent_factor_t, t("tooltip_factor_t"))

        # Optimizasyon Seçenekleri (Min Çap için)
        self.app.opt_weight_var = tk.BooleanVar(value=False)
        self.app.chk_opt_weight = ttk.Checkbutton(self.app.design_frame, text=t("opt_lowest_weight"), variable=self.app.opt_weight_var)
        self.app.chk_opt_weight.grid(row=1, column=0, columnspan=4, padx=5, pady=(10, 0), sticky="w")

        self.app.fast_calc_var = tk.BooleanVar(value=True)
        self.app.chk_fast_calc = ttk.Checkbutton(self.app.design_frame, text=t("fast_calc"), variable=self.app.fast_calc_var)
        self.app.chk_fast_calc.grid(row=1, column=4, columnspan=5, padx=5, pady=(10, 0), sticky="w")

        # Boru Elemanları (Fittings) — Collapsible
        self.app._fittings_visible = False
        self.app.fit_toggle_btn = ttk.Button(self, text=t("toggle_fittings_show"),
                                          command=self.app._toggle_fittings)
        self.app.fit_toggle_btn.pack(fill="x", pady=(10, 0))
        
        self.app.fit_frame = ttk.LabelFrame(self, text=t("section_fittings"), padding=5)
        
        # 2 Kolonlu Fittings Düzeni
        items = list(FITTING_K_FACTORS.keys())
        half = (len(items) + 1) // 2
        
        for i, item in enumerate(items):
            col = 0 if i < half else 3
            row = i if i < half else i - half
            
            ttk.Label(self.app.fit_frame, text=t_fitting(item)).grid(row=row, column=col, sticky="w", padx=5, pady=2)
            var = tk.IntVar(value=0)
            self.app.fitting_counts[item] = var
            var.trace_add("write", lambda *args, v=var: self.app._clamp_fitting_value(v))
            ttk.Entry(self.app.fit_frame, textvariable=var, width=5).grid(row=row, column=col+1, padx=5)
            
            if item == "Küresel Vana (Tam Açık)":
                ttk.Label(self.app.fit_frame, text="Kv:").grid(row=row, column=col+2)
                ttk.Entry(self.app.fit_frame, textvariable=self.app.ball_valve_kv, width=5).grid(row=row, column=col+3)

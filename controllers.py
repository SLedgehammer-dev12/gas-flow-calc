from translations import t
from data import PIPE_ROUGHNESS, FITTING_K_FACTORS
from calculations import GasFlowCalculator
from format_utils import safe_format, safe_number, safe_text
from flow_utils import FLOW_MODE_INCOMPRESSIBLE, normalize_flow_mode

class GasFlowController:
    def __init__(self):
        self.calculator = GasFlowCalculator()
        
    def _parse_float(self, val, default=0.0):
        try:
            return float(val) if val else default
        except (ValueError, TypeError):
            return default
            
    def _parse_int(self, val, default=0):
        try:
            return int(val) if val else default
        except (ValueError, TypeError):
            return default

    def prepare_inputs(self, ui_state, mole_fractions_override=None):
        """Converts raw UI state dict into calculations input dict and validates it."""
        errors = []
        
        # 1. Gas Composition
        mole_fractions = {}
        if mole_fractions_override is not None:
            mole_fractions = mole_fractions_override
        else:
            gas_components = ui_state.get("gas_components", {})
            if not gas_components:
                errors.append(t("validation_add_gas") if t("validation_add_gas") != "validation_add_gas" else "Lütfen en az bir gaz bileşeni ekleyin.")
            else:
                total_mole = sum(self._parse_float(v) for v in gas_components.values())
                if total_mole <= 0:
                    errors.append("Gaz oranları toplamı pozitif olmalıdır.")
                else:
                    mole_fractions = {k: self._parse_float(v)/total_mole for k, v in gas_components.items() if self._parse_float(v) > 0}
                    
        if ui_state.get("comp_type") == "Kütle %" and mole_fractions:
            mole_fractions = self.calculator.mass_to_mole_fraction(mole_fractions)
            
        # 2. Basic Params Validation
        p_in_val = self._parse_float(ui_state.get("p_in", 0))
        if p_in_val <= 0: errors.append(t("validation_positive_pressure") if "validation_positive_pressure" in t("validation_positive_pressure") else "Giriş basıncı pozitif olmalıdır.")
        
        t_val = self._parse_float(ui_state.get("t_val", 25))
        if t_val <= -273.15: errors.append("Sıcaklık mutlak sıfırdan büyük olmalıdır.")
        
        flow_val = self._parse_float(ui_state.get("flow_val", 0))
        if flow_val <= 0: errors.append(t("validation_positive_flow") if "validation_positive_flow" in t("validation_positive_flow") else "Akış debisi pozitif olmalıdır.")
        
        target = ui_state.get("calc_target")
        
        len_val = self._parse_float(ui_state.get("len_val", 100))
        diam_val = self._parse_float(ui_state.get("diam_val", 0))
        thick_val = self._parse_float(ui_state.get("thick_val", 0))
        target_p_val = self._parse_float(ui_state.get("target_p_val", 0))
        max_vel = self._parse_float(ui_state.get("max_vel_val", 20))
        p_design_val = self._parse_float(ui_state.get("p_design_val", 0))
        
        flow_type = ui_state.get("flow_type")
        flow_mode = normalize_flow_mode(flow_type)
        
        if target == t("target_pressure_drop"):
            if len_val <= 0: errors.append("Boru uzunluğu pozitif olmalıdır.")
            if diam_val <= 0: errors.append("Boru çapı pozitif olmalıdır.")
            if thick_val >= diam_val / 2: errors.append("Et kalınlığı yarıçaptan küçük olmalıdır.")
        elif target == t("target_max_length"):
            if target_p_val <= 0: errors.append("Hedef çıkış basıncı pozitif olmalıdır.")
            if diam_val <= 0: errors.append("Boru çapı pozitif olmalıdır.")
        elif target == t("target_min_diameter"):
            if max_vel <= 0: errors.append("Maksimum hız limiti pozitif olmalıdır.")
            if p_design_val <= 0: errors.append("Tasarım basıncı pozitif olmalıdır.")
            if flow_mode != FLOW_MODE_INCOMPRESSIBLE and len_val <= 0:
                errors.append("Sıkıştırılabilir akış çap hesabı için boru uzunluğu gereklidir.")

        D_inner = diam_val - 2 * thick_val
        if target != t("target_min_diameter") and D_inner <= 0:
            errors.append("Geçersiz boru çapı/kalınlığı. İç çap negatif veya sıfır olamaz.")
            
        if errors:
            return None, errors
            
        # Conversions
        p_unit = ui_state.get("p_unit")
        if p_unit == "Barg": P_in = (p_in_val + 1.01325) * 1e5
        elif p_unit == "Bara": P_in = p_in_val * 1e5
        elif p_unit == "Psig": P_in = (p_in_val + 14.696) * 6894.76
        else: P_in = p_in_val * 6894.76
        
        t_unit = str(ui_state.get("t_unit", "°C")).strip() # Use cleaned string
        if t_unit == "°C": T = t_val + 273.15
        elif t_unit == "°F": T = (t_val - 32) * 5/9 + 273.15
        else: T = t_val
        
        # Target pressure conversion
        target_p_unit = ui_state.get("target_p_unit", "Barg")
        abs_pa_target = 0
        if target_p_unit == "Barg": abs_pa_target = (target_p_val + 1.01325) * 1e5
        elif target_p_unit == "Bara": abs_pa_target = target_p_val * 1e5
        elif target_p_unit == "Psig": abs_pa_target = (target_p_val + 14.696) * 6894.76
        elif target_p_unit == "Psia": abs_pa_target = target_p_val * 6894.76
        
        # Design pressure conversion
        p_design_unit = ui_state.get("p_design_unit", "Barg")
        abs_pa_design = 0
        if p_design_unit == "Barg": abs_pa_design = (p_design_val + 1.01325) * 1e5
        elif p_design_unit == "Bara": abs_pa_design = p_design_val * 1e5
        elif p_design_unit == "Psig": abs_pa_design = (p_design_val + 14.696) * 6894.76
        elif p_design_unit == "Psia": abs_pa_design = p_design_val * 6894.76
        P_design_gauge = max(0, abs_pa_design - 101325)
        
        # Fittings K
        total_k = 0
        fitting_counts = ui_state.get("fitting_counts", {})
        for name, count_val in fitting_counts.items():
            count = self._parse_int(count_val)
            if count > 0 and name in FITTING_K_FACTORS:
                total_k += FITTING_K_FACTORS[name] * count
                
        material = ui_state.get("material", "API 5L Grade B")

        return {
            "P_in": P_in, "T": T, "mole_fractions": mole_fractions,
            "library_choice": ui_state.get("thermo_model"),
            "flow_rate": flow_val, "flow_unit": ui_state.get("flow_unit"),
            "D_inner": D_inner, "L": len_val,
            "roughness": PIPE_ROUGHNESS.get(material, 4.57e-5),
            "total_k": total_k,
            "flow_property": flow_type,
            "flow_mode": flow_mode,
            "target": target,
            "P_out_target": abs_pa_target if target == t("target_max_length") else 0,
            
            # Min Diameter additions
            "max_velocity": max_vel,
            "optimize_weight": ui_state.get("opt_weight", False),
            "fast_calculation": ui_state.get("fast_calc", False),
            "P_design": P_design_gauge,
            "material": material,
            "SMYS": self._parse_float(ui_state.get("smys_val", 0)),
            "F": self._parse_float(ui_state.get("factor_f", 0.72)),
            "E": self._parse_float(ui_state.get("factor_e", 1.0)),
            "T_factor": self._parse_float(ui_state.get("factor_t", 1.0))
        }, None

    def get_results_table_data(self, result, target, ui_state):
        """Returns a list of tuples (param, value, unit, tag) to populate the results treeview."""
        if not result: return []
        rows = []
        
        if target == t("target_pressure_drop"):
            rows.append(("Giriş Basıncı", safe_format(self._parse_float(ui_state.get('p_in', 0)), ".2f"), ui_state.get('p_unit', '')))
            rows.append(("Çıkış Basıncı", safe_format(safe_number(result['P_out'], 0.0)/1e5, ".4f"), "bara"))
            rows.append(("Toplam Basınç Kaybı", safe_format(safe_number(result['delta_p_total'], 0.0)/1e5, ".4f"), "bar"))
            rows.append(("Giriş Hızı", safe_format(result['velocity_in'], ".2f"), "m/s"))
            rows.append(("Çıkış Hızı", safe_format(result['velocity_out'], ".2f"), "m/s"))
            
        elif target == t("target_max_length"):
            if "error" in result:
                rows.append(("Durum", "HATA", "", "error"))
                rows.append(("Mesaj", safe_text(result['error']), ""))
            else:
                rows.append(("Maksimum Uzunluk", safe_format(result['L_max'], ".2f"), "m"))
                rows.append(("Reynolds", safe_format(result['Re'], ".0f"), ""))
                
        elif target == t("target_min_diameter"):
            if result.get('selected_pipe'):
                p = result['selected_pipe']
                rows.append(("Seçilen Boru", f"{safe_text(p['nominal'])}\"", f"Sch {safe_text(p['schedule'])}", "success"))
                rows.append(("İç Çap", safe_format(p['D_inner_mm'], ".2f"), "mm"))
                if 'weight_per_m' in p:
                    rows.append((t("unit_weight") if t("unit_weight") != "unit_weight" else "Birim Ağırlık", safe_format(p['weight_per_m'], ".2f"), "kg/m"))
                rows.append(("Çıkış Hızı", safe_format(result['velocity_out'], ".2f"), "m/s"))
                rows.append(("Limit Hız", safe_format(result['max_vel'], ".2f"), "m/s"))
                
                status_tag = "success" if "Uygun" in result['velocity_status'] else "warning"
                rows.append(("Durum", result['velocity_status'], "", status_tag))
                
                # Alternatives
                if 'alternatives' in result and result['alternatives']: # Dict instead of list
                    rows.append(("", "", ""))
                    rows.append(("--- Alternatif Seçenekler ---", "", "", "warning"))
                    for key, alt in result['alternatives'].items():
                        p_alt = alt['pipe']
                        rows.append((f"[★] {safe_text(alt['note'])}", f"{safe_text(p_alt['nominal'])}\" Sch {safe_text(p_alt['schedule'])}", ""))
                        if 'weight_per_m' in p_alt:
                            rows.append((f"   ↳ Birim Ağırlık", safe_format(p_alt['weight_per_m'], ".2f"), "kg/m"))
                        if 'result' in alt and 'velocity_out' in alt['result']:
                            rows.append((f"   ↳ Çıkış Hızı", safe_format(alt['result']['velocity_out'], ".2f"), "m/s"))
            else:
                rows.append(("Durum", "Uygun Boru Yok", "", "error"))

        if 'm_dot' in result:
             rows.append(("Kütlesel Debi", safe_format(result['m_dot'], ".4f"), "kg/s"))

        if 'phase_info' in result:
            phase_info = result['phase_info']
            tag = {
                'ok': 'success',
                'warning': 'warning',
                'critical': 'error',
            }.get(phase_info.get('warning_level', 'ok'), '')
            rows.append(("Akışkan Fazı", safe_text(phase_info.get('phase_label_tr', '-')), "", tag))
            vapor_quality = phase_info.get('vapor_quality')
            if vapor_quality is not None:
                rows.append(("Buhar Kalitesi (Q)", safe_format(vapor_quality, ".3f"), "[-]"))
            formula_label = phase_info.get('formula_label_tr')
            if formula_label:
                rows.append(("Formül Seti", safe_text(formula_label), ""))
            transition_distance = phase_info.get('transition_to_two_phase_m')
            if transition_distance is not None:
                rows.append(("İki Faz Geçişi", safe_format(transition_distance, ".2f"), "m", tag))

        return rows

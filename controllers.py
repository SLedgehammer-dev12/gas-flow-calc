from translations import t
from data import PIPE_ROUGHNESS, FITTING_K_FACTORS
from calculations import GasFlowCalculator
from format_utils import safe_format, safe_number, safe_text
from constants import convert_pressure_to_pa, convert_temperature_to_k
from flow_utils import FLOW_MODE_INCOMPRESSIBLE, normalize_flow_mode
from target_utils import (
    TARGET_PRESSURE_DROP,
    TARGET_MAX_LENGTH,
    TARGET_MIN_DIAMETER,
)

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
                errors.append(t("validation_add_gas", "Lütfen en az bir gaz bileşeni ekleyin."))
            else:
                total_mole = sum(self._parse_float(v) for v in gas_components.values())
                if total_mole <= 0:
                    errors.append(t("val_mole_total_positive", "Gaz oranları toplamı pozitif olmalıdır."))
                else:
                    mole_fractions = {k: self._parse_float(v)/total_mole for k, v in gas_components.items() if self._parse_float(v) > 0}
                    
        if ui_state.get("comp_type") == t("mass_percent", "Kütle %") and mole_fractions:
            mole_fractions = self.calculator.mass_to_mole_fraction(mole_fractions)
            
        # 2. Basic Params Validation
        p_in_val = self._parse_float(ui_state.get("p_in", 0))
        if p_in_val <= 0: errors.append(t("val_pressure_positive", "Giriş basıncı pozitif olmalıdır."))
        if p_in_val > 1000: errors.append(t("val_pressure_max", "Giriş basıncı 1000 bar'dan büyük olamaz."))

        t_val = self._parse_float(ui_state.get("t_val", 25))
        if t_val <= -273.15: errors.append(t("val_temp_abs_zero", "Sıcaklık mutlak sıfırdan büyük olmalıdır."))
        if t_val > 500: errors.append(t("val_temp_max", "Sıcaklık 500°C'den büyük olamaz."))

        flow_val = self._parse_float(ui_state.get("flow_val", 0))
        if flow_val <= 0: errors.append(t("val_flow_positive", "Akış debisi pozitif olmalıdır."))
        if flow_val > 1e8: errors.append(t("val_flow_too_high", "Akış debisi çok yüksek. Lütfen değeri kontrol edin."))
        
        target = ui_state.get("calc_target")
        
        len_val = self._parse_float(ui_state.get("len_val", 100))
        diam_val = self._parse_float(ui_state.get("diam_val", 0))
        thick_val = self._parse_float(ui_state.get("thick_val", 0))
        target_p_val = self._parse_float(ui_state.get("target_p_val", 0))
        max_vel = self._parse_float(ui_state.get("max_vel_val", 20))
        p_design_val = self._parse_float(ui_state.get("p_design_val", 0))
        
        flow_type = ui_state.get("flow_type")
        flow_mode = normalize_flow_mode(flow_type)
        
        if target == TARGET_PRESSURE_DROP:
            if len_val <= 0: errors.append(t("val_length_positive", "Boru uzunluğu pozitif olmalıdır."))
            if diam_val <= 0: errors.append(t("val_diameter_positive", "Boru çapı pozitif olmalıdır."))
            if thick_val >= diam_val / 2: errors.append(t("val_thickness_range", "Et kalınlığı yarıçaptan küçük olmalıdır."))
        elif target == TARGET_MAX_LENGTH:
            if target_p_val <= 0: errors.append(t("val_target_pressure_positive", "Hedef çıkış basıncı pozitif olmalıdır."))
            if diam_val <= 0: errors.append(t("val_diameter_positive", "Boru çapı pozitif olmalıdır."))
        elif target == TARGET_MIN_DIAMETER:
            if max_vel <= 0: errors.append(t("val_max_velocity_positive", "Maksimum hız limiti pozitif olmalıdır."))
            if p_design_val <= 0: errors.append(t("val_design_pressure_positive", "Tasarım basıncı pozitif olmalıdır."))
            if flow_mode != FLOW_MODE_INCOMPRESSIBLE and len_val <= 0:
                errors.append(t("val_length_required_compressible", "Sıkıştırılabilir akış çap hesabı için boru uzunluğu gereklidir."))

        D_inner = diam_val - 2 * thick_val
        if target != TARGET_MIN_DIAMETER and D_inner <= 0:
            errors.append(t("val_invalid_diameter", "Geçersiz boru çapı/kalınlığı. İç çap negatif veya sıfır olamaz."))

        smys_val = self._parse_float(ui_state.get("smys_val", 0))
        if target == TARGET_MIN_DIAMETER and smys_val <= 0:
            errors.append(t("val_smys_positive", "Minimum çap hesabı için SMYS (akma dayanımı) pozitif olmalıdır."))
            
        if errors:
            return None, errors
            
        # Conversions
        P_in = convert_pressure_to_pa(p_in_val, ui_state.get("p_unit"))        
        T = convert_temperature_to_k(t_val, ui_state.get("t_unit", "°C"))
        
        # Target pressure conversion
        target_p_unit = ui_state.get("target_p_unit", "Barg")
        abs_pa_target = convert_pressure_to_pa(target_p_val, target_p_unit)
        
        # Design pressure conversion
        p_design_unit = ui_state.get("p_design_unit", "Barg")
        abs_pa_design = convert_pressure_to_pa(p_design_val, p_design_unit)
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
            "P_out_target": abs_pa_target if target == TARGET_MAX_LENGTH else 0,
            
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
        
        if target == TARGET_PRESSURE_DROP:
            rows.append((t("label_inlet_pressure", "Giriş Basıncı"), safe_format(self._parse_float(ui_state.get('p_in', 0)), ".2f"), ui_state.get('p_unit', '')))
            rows.append((t("label_outlet_pressure", "Çıkış Basıncı"), safe_format(safe_number(result['P_out'], 0.0)/1e5, ".4f"), "bara"))
            rows.append((t("label_total_pressure_drop", "Toplam Basınç Kaybı"), safe_format(safe_number(result['delta_p_total'], 0.0)/1e5, ".4f"), "bar"))
            rows.append((t("label_inlet_velocity", "Giriş Hızı"), safe_format(result['velocity_in'], ".2f"), "m/s"))
            rows.append((t("label_outlet_velocity", "Çıkış Hızı"), safe_format(result['velocity_out'], ".2f"), "m/s"))

        elif target == TARGET_MAX_LENGTH:
            if "error" in result:
                rows.append((t("label_status", "Durum"), t("label_error", "HATA"), "", "error"))
                rows.append((t("label_message", "Mesaj"), safe_text(result['error']), ""))
            else:
                rows.append((t("label_max_length", "Maksimum Uzunluk"), safe_format(result['L_max'], ".2f"), "m"))
                rows.append(("Reynolds", safe_format(result['Re'], ".0f"), ""))
                rows.append((t("label_friction_factor", "Sürtünme Faktörü (f)"), safe_format(result.get('f'), ".5f"), ""))
                rows.append((t("label_inlet_velocity", "Giriş Hızı"), safe_format(result.get('velocity_in'), ".2f"), "m/s"))
                rows.append((t("label_outlet_velocity", "Çıkış Hızı"), safe_format(result.get('velocity_out'), ".2f"), "m/s"))
                rows.append((t("label_outlet_pressure", "Çıkış Basıncı"), safe_format(safe_number(result.get('P_out'), 0.0)/1e5, ".4f"), "bara"))

        elif target == TARGET_MIN_DIAMETER:
            if result.get('selected_pipe'):
                p = result['selected_pipe']
                rows.append((t("label_selected_pipe", "Seçilen Boru"), f"{safe_text(p['nominal'])}\"", f"Sch {safe_text(p['schedule'])}", "success"))
                rows.append((t("label_inner_diameter", "İç Çap"), safe_format(p['D_inner_mm'], ".2f"), "mm"))
                if 'weight_per_m' in p:
                    rows.append((t("unit_weight", "Birim Ağırlık"), safe_format(p['weight_per_m'], ".2f"), "kg/m"))
                rows.append((t("label_outlet_velocity", "Çıkış Hızı"), safe_format(result['velocity_out'], ".2f"), "m/s"))
                rows.append((t("label_limit_velocity", "Limit Hız"), safe_format(result['max_vel'], ".2f"), "m/s"))

                status_tag = "success" if "Uygun" in result['velocity_status'] else "warning"
                rows.append((t("label_status", "Durum"), result['velocity_status'], "", status_tag))

                if 'alternatives' in result and result['alternatives']:
                    rows.append(("", "", ""))
                    title = t("label_alternative_options", "Alternatif Seçenekler")
                    rows.append((f"--- {title} ---", "", "", "warning"))
                    for key, alt in result['alternatives'].items():
                        p_alt = alt['pipe']
                        rows.append((f"[★] {safe_text(alt['note'])}", f"{safe_text(p_alt['nominal'])}\" Sch {safe_text(p_alt['schedule'])}", ""))
                        if 'weight_per_m' in p_alt:
                            rows.append((f"   ↳ {t('unit_weight', 'Birim Ağırlık')}", safe_format(p_alt['weight_per_m'], ".2f"), "kg/m"))
                        if 'result' in alt and 'velocity_out' in alt['result']:
                            rows.append((f"   ↳ {t('label_outlet_velocity', 'Çıkış Hızı')}", safe_format(alt['result']['velocity_out'], ".2f"), "m/s"))
            else:
                rows.append((t("label_status", "Durum"), t("label_no_pipe_found", "Uygun Boru Yok"), "", "error"))

        if 'm_dot' in result:
             rows.append((t("label_mass_flow", "Kütlesel Debi"), safe_format(result['m_dot'], ".4f"), "kg/s"))

        if 'phase_info' in result:
            phase_info = result['phase_info']
            tag = {
                'ok': 'success',
                'warning': 'warning',
                'critical': 'error',
            }.get(phase_info.get('warning_level', 'ok'), '')
            rows.append((t("label_fluid_phase", "Akışkan Fazı"), safe_text(phase_info.get('phase_label_tr', '-')), "", tag))
            vapor_quality = phase_info.get('vapor_quality')
            if vapor_quality is not None:
                rows.append((t("label_vapor_quality", "Buhar Kalitesi (Q)"), safe_format(vapor_quality, ".3f"), "[-]"))
            formula_label = phase_info.get('formula_label_tr')
            if formula_label:
                rows.append((t("label_formula_set", "Formül Seti"), safe_text(formula_label), ""))
            transition_distance = phase_info.get('transition_to_two_phase_m')
            if transition_distance is not None:
                rows.append((t("label_two_phase_transition", "İki Faz Geçişi"), safe_format(transition_distance, ".2f"), "m", tag))

        return rows

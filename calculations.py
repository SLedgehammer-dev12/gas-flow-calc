
import math
import numpy as np
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import CoolProp.CoolProp as CP
from data import COOLPROP_GASES, PIPE_MATERIALS, PIPE_ROUGHNESS, FITTING_K_FACTORS, ASME_B36_10M_DATA
from flow_utils import FLOW_MODE_INCOMPRESSIBLE, normalize_flow_mode

# R: Evrensel Gaz Sabiti [J/(mol*K)]
R_J_mol_K = 8.314462618
MIN_PRESSURE_PA = 1000.0 # Mutlak minimum basınç (1000 Pa)

_GAS_NAME_LOOKUP = {}
for gas_key, gas_props in COOLPROP_GASES.items():
    canonical_name = gas_props["id"]
    _GAS_NAME_LOOKUP[gas_key.casefold()] = canonical_name
    _GAS_NAME_LOOKUP[canonical_name.casefold()] = canonical_name
    _GAS_NAME_LOOKUP[gas_props["name"].casefold()] = canonical_name


def _cp_arg(value):
    if isinstance(value, str):
        return value.encode("ascii")
    return value


def cp_propssi(*args):
    try:
        return CP.PropsSI(*args)
    except TypeError:
        return CP.PropsSI(*(_cp_arg(arg) for arg in args))


def cp_abstract_state(backend, fluids):
    try:
        return CP.AbstractState(backend, fluids)
    except TypeError:
        return CP.AbstractState(_cp_arg(backend), _cp_arg(fluids))


class GasFlowCalculator:
    def __init__(self):
        self.log_callback = None
        # Standart yoğunluk cache’i: (gaz_taple, kütüp) -> kg/m3
        self._std_density_cache = {}
        # Termodinamik özellik cache’i: (P, T, gaz_tuple, kutuphane) -> props_dict
        self._thermo_cache = {}
        self._phase_envelope_cache = {}

    def set_log_callback(self, callback):
        """Log mesajlarını dışarıya (örn. GUI) iletmek için callback fonksiyonu."""
        self.log_callback = callback

    def log(self, message, level="INFO"):
        if self.log_callback:
            self.log_callback(message, level)

    def clear_thermo_cache(self):
        """Her yeni hesaplama başlangıcında cache'i temizle."""
        self._thermo_cache.clear()
        self._std_density_cache.clear()
        self._phase_envelope_cache.clear()

    # --- YARDIMCI FONKSİYONLAR ---
    def validate_inputs(self, inputs):
        """Temel giriş doğrulama."""
        if not inputs.get("mole_fractions"): raise ValueError("Gaz bileşimi boş olamaz.")
        if inputs.get("P_in") < 0: raise ValueError("Giriş basıncı negatif olamaz.")
        if inputs.get("T") <= 0: raise ValueError("Sıcaklık pozitif olmalıdır.")
        return True

    def normalize_gas_name(self, gas):
        text = str(gas).strip()
        canonical = _GAS_NAME_LOOKUP.get(text.casefold())
        if not canonical and "(" in text:
            canonical = _GAS_NAME_LOOKUP.get(text.split("(", 1)[0].strip().casefold())
        if canonical:
            return canonical
        raise ValueError(f"Desteklenmeyen gaz tanimi: {gas}")

    def normalize_mole_fractions(self, mole_fractions):
        normalized = {}
        for gas, fraction in mole_fractions.items():
            canonical = self.normalize_gas_name(gas)
            normalized[canonical] = normalized.get(canonical, 0.0) + float(fraction)

        total = sum(normalized.values())
        if total <= 0:
            raise ValueError("Gaz bilesimi bos olamaz.")

        return {gas: value / total for gas, value in normalized.items()}

    def is_mass_flow_unit(self, flow_unit):
        return str(flow_unit).strip().casefold() == "kg/s"

    def calculate_mass_flow_rate(self, flow_rate, flow_unit, standard_density):
        """Normalize any supported flow input to kg/s."""
        if self.is_mass_flow_unit(flow_unit):
            return float(flow_rate)
        return (float(flow_rate) / 3600.0) * standard_density

    def mass_to_mole_fraction(self, mass_fractions):
        total_moles = 0.0; moles = {}
        for gas, mass_frac in mass_fractions.items():
            canonical = self.normalize_gas_name(gas)
            try: MW = cp_propssi('M', canonical)
            except Exception as e: raise ValueError(f"{gas} için moleküler ağırlık alınamadı: {str(e)}")
            moles[canonical] = mass_frac / MW; total_moles += moles[canonical]
        if total_moles == 0: raise ValueError("Toplam mol sıfır!")
        return {gas: mole / total_moles for gas, mole in moles.items()}

    def get_friction_factor(self, Re, relative_roughness):
        if Re < 2000: return 64 / Re
        else:
            # Colebrook-White denklemi iteratif çözüm 
            f_old = 0.02
            for _ in range(20):
                inner = (relative_roughness / 3.7) + (2.51 / (Re * math.sqrt(f_old)))
                f_new = (-2 * math.log10(inner)) ** -2
                if abs(f_new - f_old) < 1e-6: return f_new
                f_old = f_new
            return f_old

    def get_churchill_friction_factor(self, Re, relative_roughness):
        if Re <= 0:
            return 0.0
        if Re < 2000:
            return 64.0 / Re

        A = (2.457 * math.log(1.0 / (((7.0 / Re) ** 0.9) + 0.27 * relative_roughness))) ** 16
        B = (37530.0 / Re) ** 16
        return 8.0 * (((8.0 / Re) ** 12) + ((A + B) ** -1.5)) ** (1.0 / 12.0)

    # --- TERMODİNAMİK MODELLER ---
    def get_pure_component_props(self, gas_id):
        gas_id = self.normalize_gas_name(gas_id)
        try:
            return {
                'Tc': cp_propssi('TCRIT', gas_id), 'Pc': cp_propssi('PCRIT', gas_id),
                'omega': cp_propssi('ACENTRIC', gas_id), 'MW': cp_propssi('M', gas_id) * 1000
            }
        except Exception as e:
            # GÜVENLİK DÜZELTMESİ: Varsayılan değer atamak yerine hata fırlatıyoruz.
            raise ValueError(f"CoolProp hatası ({gas_id}): Kritik özellikler alınamadı. {str(e)}")

    def calculate_cubic_eos_props(self, P, T, mole_fractions, EOS_type):
        mole_fractions = self.normalize_mole_fractions(mole_fractions)
        self.log(f"Hesaplama: {EOS_type} modeli kullanılıyor.", "DEBUG")
        A_c, B_c = (0.45724, 0.07780) if EOS_type == "PR" else (0.42748, 0.08664)
        kappa_coeffs = (0.37464, 1.54226, -0.26992) if EOS_type == "PR" else (0.48, 1.574, -0.176)
        
        b_mix = 0; sqrt_a_mix = 0; MW_mix = 0
        
        for gas, y in mole_fractions.items():
            props = self.get_pure_component_props(gas)
            
            omega = props['omega']
            kappa = kappa_coeffs[0] + kappa_coeffs[1] * omega + kappa_coeffs[2] * omega**2
            
            alpha = (1 + kappa * (1 - math.sqrt(T / props['Tc'])))**2
            a_i = A_c * (R_J_mol_K * props['Tc'])**2 / props['Pc'] * alpha
            b_i = B_c * R_J_mol_K * props['Tc'] / props['Pc']

            b_mix += y * b_i
            sqrt_a_mix += y * math.sqrt(a_i)
            MW_mix += y * props['MW']

        a_mix = sqrt_a_mix**2
        
        A = a_mix * P / (R_J_mol_K * T)**2
        B = b_mix * P / (R_J_mol_K * T)
        
        if EOS_type == "PR":
            coeffs = [1, (B - 1), (A - 3*B**2 - 2*B), (-A*B + B**2 + B**3)]
        else:
            coeffs = [1, -1, (A - B - B**2), -A*B]
        
        roots = np.roots(coeffs)
        real_roots = roots[np.isreal(roots)].real

        if len(real_roots) == 0:
            raise ValueError(f"{EOS_type} modelinde P={P/1e5:.1f} bara, T={T:.1f} K noktasında gerçek kök bulunamadı.")

        Z = max(real_roots)
        
        density = (P * MW_mix * 1e-3) / (Z * R_J_mol_K * T)
        standard_density = (101325 * MW_mix * 1e-3) / (1.0 * R_J_mol_K * 288.15) 
        viscosity = 1.5e-5 * math.sqrt(MW_mix / 16.04) # Basit tahmin

        Cp_mix, Cv_mix = 0, 0
        for gas, y in mole_fractions.items():
            try:
                cp_i = cp_propssi('CP0MASS', 'T', T, 'P', 101325, gas) / 1000
                cv_i = cp_propssi('CV0MASS', 'T', T, 'P', 101325, gas) / 1000
                Cp_mix += y * cp_i
                Cv_mix += y * cv_i
            except ValueError:
                Cp_mix += y * 2.0; Cv_mix += y * 1.6
        if Cv_mix == 0: Cv_mix = 1.0
        k_avg = Cp_mix / Cv_mix
        Cv_mix = Cp_mix / k_avg

        # Sonic Velocity Check (Ideal Gas Approx with Z)
        gamma = k_avg if k_avg > 0 else 1.3
        sonic_velocity = math.sqrt(gamma * Z * R_J_mol_K * T / (MW_mix * 1e-3))
        
        return {
            "MW": MW_mix, "Cp": Cp_mix, "Cv": Cv_mix, "Z": Z, "density": density,
            "viscosity": viscosity, "standard_density": standard_density,
            "EOS_model": EOS_type,
            "sonic_velocity": sonic_velocity
        }

    def create_coolprop_state(self, mole_fractions):
        """CoolProp AbstractState nesnesi oluşturur (Performans için)."""
        try:
            backend = "HEOS"
            normalized = self.normalize_mole_fractions(mole_fractions)
            fluids = list(normalized.keys())
            fractions = list(normalized.values())
            
            # Gaz isimlerini CoolProp formatına uygun hale getir (örn. "Methane (CH4)" -> "Methane")
            # Ancak data.py'da zaten CoolProp isimleri anahtar olarak kullanılıyor (örn. "METHANE" -> "Methane (CH4)")
            # Wait, data.py keys are "METHANE", values are "Methane (CH4)".
            # But inputs['mole_fractions'] keys come from data.py keys?
            # Let's check main.py add_gas_component.
            # It uses gas_id which is the key (e.g. "METHANE").
            # But CoolProp needs "Methane".
            # I need a mapping from ID to CoolProp Name.
            # In data.py: "METHANE": "Methane (CH4)".
            # CoolProp expects "Methane".
            # I should probably clean the names.
            
            state = cp_abstract_state(backend, "&".join(fluids))
            state.set_mole_fractions(fractions)
            return state
        except Exception as e:
            self.log(f"CoolProp State Oluşturma Hatası: {e}", "ERROR")
            return None

    def build_mixture_string(self, mole_fractions):
        normalized = self.normalize_mole_fractions(mole_fractions)
        return "&".join([f"{gas}[{fraction:.6f}]" for gas, fraction in normalized.items()])

    def _phase_envelope_key(self, mole_fractions):
        normalized = self.normalize_mole_fractions(mole_fractions)
        return tuple((gas, round(fraction, 8)) for gas, fraction in sorted(normalized.items()))

    def _get_phase_envelope_summary(self, mole_fractions):
        key = self._phase_envelope_key(mole_fractions)
        if key in self._phase_envelope_cache:
            return self._phase_envelope_cache[key]

        normalized = dict(key)
        if len(normalized) <= 1:
            summary = None
        else:
            try:
                state = cp_abstract_state("HEOS", "&".join(normalized.keys()))
                state.set_mole_fractions(list(normalized.values()))
                state.build_phase_envelope("")
                envelope = state.get_phase_envelope_data()
                summary = {
                    "T_min": min(envelope.T),
                    "T_max": max(envelope.T),
                    "p_min": min(envelope.p),
                    "p_max": max(envelope.p),
                    "curve": tuple((float(t), float(p)) for t, p in zip(envelope.T, envelope.p)),
                }
            except Exception as exc:
                self.log(f"Phase envelope olusturulamadi: {exc}", "WARNING")
                summary = None

        self._phase_envelope_cache[key] = summary
        return summary

    def _get_components_below_triple_point(self, mole_fractions, T):
        normalized = self.normalize_mole_fractions(mole_fractions)
        components = []
        for gas, fraction in normalized.items():
            try:
                triple_T = float(cp_propssi("TTRIPLE", gas))
            except Exception:
                continue
            if T + 1e-6 < triple_T:
                components.append({
                    "gas": gas,
                    "fraction": fraction,
                    "T_triple": triple_T,
                })
        return components

    def _interpolate_envelope_pressures(self, envelope_summary, T):
        if not envelope_summary or "curve" not in envelope_summary:
            return []

        curve = envelope_summary["curve"]
        pressures = []
        for index in range(len(curve) - 1):
            T1, P1 = curve[index]
            T2, P2 = curve[index + 1]
            if (T1 <= T <= T2) or (T2 <= T <= T1):
                if abs(T2 - T1) < 1e-12:
                    pressures.extend((P1, P2))
                else:
                    ratio = (T - T1) / (T2 - T1)
                    pressures.append(P1 + ratio * (P2 - P1))

        pressures.sort()
        unique_pressures = []
        for value in pressures:
            if not unique_pressures or abs(value - unique_pressures[-1]) > max(1e-3, abs(value) * 1e-6):
                unique_pressures.append(value)
        return unique_pressures

    def _estimate_phase_from_envelope(self, P, T, mole_fractions):
        envelope = self._get_phase_envelope_summary(mole_fractions)
        pressures = self._interpolate_envelope_pressures(envelope, T)
        if not pressures:
            return None

        low_pressure = min(pressures)
        high_pressure = max(pressures)
        tolerance = max(100.0, abs(high_pressure) * 1e-4)

        if len(pressures) == 1:
            if P < low_pressure - tolerance:
                return {"phase": "gas", "vapor_quality": None, "envelope_pressures": tuple(pressures)}
            if P > high_pressure + tolerance:
                return {"phase": "liquid", "vapor_quality": None, "envelope_pressures": tuple(pressures)}
            return {"phase": "two_phase", "vapor_quality": 0.5, "envelope_pressures": tuple(pressures)}

        if P < low_pressure - tolerance:
            return {"phase": "gas", "vapor_quality": None, "envelope_pressures": tuple(pressures)}
        if P > high_pressure + tolerance:
            return {"phase": "liquid", "vapor_quality": None, "envelope_pressures": tuple(pressures)}

        span = max(high_pressure - low_pressure, tolerance)
        vapor_quality = (high_pressure - P) / span
        vapor_quality = min(max(vapor_quality, 0.0), 1.0)
        return {
            "phase": "two_phase",
            "vapor_quality": vapor_quality,
            "envelope_pressures": tuple(pressures),
        }

    def detect_phase(self, P, T, mole_fractions, state=None):
        normalized = self.normalize_mole_fractions(mole_fractions)
        phase_code = CP.iphase_unknown
        vapor_quality = None
        fallback_reason = None
        envelope_hint = None
        low_temperature_components = self._get_components_below_triple_point(normalized, T)

        if state is not None:
            try:
                try:
                    state.unspecify_phase()
                except Exception:
                    pass
                state.update(CP.PT_INPUTS, P, T)
                phase_code = int(state.phase())
                quality_value = state.Q()
                if 0.0 <= quality_value <= 1.0:
                    vapor_quality = quality_value
            except ValueError as exc:
                fallback_reason = str(exc)
                phase_code = CP.iphase_unknown

        if phase_code == CP.iphase_unknown:
            mixture = self.build_mixture_string(normalized)
            try:
                phase_code = int(cp_propssi("Phase", "P", P, "T", T, mixture))
                quality_value = cp_propssi("Q", "P", P, "T", T, mixture)
                if 0.0 <= quality_value <= 1.0:
                    vapor_quality = quality_value
            except Exception as exc:
                fallback_reason = str(exc)
                phase_code = CP.iphase_unknown

        if phase_code == CP.iphase_unknown:
            envelope_hint = self._estimate_phase_from_envelope(P, T, normalized)
            if envelope_hint:
                vapor_quality = envelope_hint.get("vapor_quality")
                phase_code = {
                    "gas": CP.iphase_gas,
                    "liquid": CP.iphase_liquid,
                    "two_phase": CP.iphase_twophase,
                }.get(envelope_hint["phase"], CP.iphase_unknown)

        if len(normalized) > 1 and phase_code in (
            CP.iphase_liquid,
            CP.iphase_supercritical_liquid,
            CP.iphase_unknown,
        ):
            envelope = self._get_phase_envelope_summary(normalized)
            if envelope and T > envelope["T_max"] + 1e-6:
                phase_code = CP.iphase_gas

        if phase_code in (CP.iphase_gas, CP.iphase_supercritical_gas):
            phase_info = {
                "phase": "gas",
                "phase_label_tr": "Tek Fazli Gaz",
                "vapor_quality": None,
                "warning_level": "ok",
                "warning_msg_tr": "",
                "phase_code": phase_code,
            }
            if envelope_hint:
                phase_info["phase_detection_source"] = "envelope"
            return phase_info

        if phase_code in (CP.iphase_liquid, CP.iphase_supercritical_liquid):
            phase_info = {
                "phase": "liquid",
                "phase_label_tr": "Tek Fazli Sivi",
                "vapor_quality": None,
                "warning_level": "warning",
                "warning_msg_tr": (
                    "Sivi faz tespit edildi. Darcy-Weisbach, Churchill surtunme faktoru ve "
                    "yogunluk degisimine bagli ivmelenme duzeltmesi kullanildi. "
                    "Kot farki girdisi olmadigi icin yercekimi terimi hesaba dahil edilmedi."
                ),
                "phase_code": phase_code,
            }
            if envelope_hint:
                phase_info["phase_detection_source"] = "envelope"
            if low_temperature_components:
                significant = [item["gas"] for item in low_temperature_components if item["fraction"] >= 0.01]
                component_text = ", ".join(significant or [low_temperature_components[0]["gas"]])
                phase_info["warning_level"] = "critical"
                phase_info["warning_msg_tr"] = (
                    f"Kriyojenik bolgede sivi/kati riski var ({component_text}). "
                    "CoolProp PT flash bu bolgede kararsiz olabilir; sonuc yaklasiktir."
                )
                phase_info["solid_risk_components"] = low_temperature_components
            return phase_info

        if phase_code == CP.iphase_twophase:
            warning_level = "warning"
            if vapor_quality is None or vapor_quality <= 0.85:
                warning_level = "critical"
            phase_info = {
                "phase": "two_phase",
                "phase_label_tr": "Iki Fazli (Gaz + Sivi Karisimi)",
                "vapor_quality": vapor_quality,
                "warning_level": warning_level,
                "warning_msg_tr": "Iki fazli bolge tespit edildi. Faz-ozgul basinc kaybi korelasyonu henuz devrede degil.",
                "phase_code": phase_code,
            }
            if envelope_hint:
                phase_info["phase_detection_source"] = "envelope"
                phase_info["warning_msg_tr"] = (
                    "CoolProp PT flash dogrudan cozulmedi; faz zarfi kullanilarak iki fazli bolge tespit edildi."
                )
            return phase_info

        if phase_code in (CP.iphase_supercritical, CP.iphase_critical_point):
            return {
                "phase": "supercritical",
                "phase_label_tr": "Superkritik",
                "vapor_quality": None,
                "warning_level": "ok",
                "warning_msg_tr": "",
                "phase_code": phase_code,
            }

        if low_temperature_components:
            significant = [item["gas"] for item in low_temperature_components if item["fraction"] >= 0.01]
            component_text = ", ".join(significant or [low_temperature_components[0]["gas"]])
            warning_message = (
                f"Bazi bilesenler uclu nokta sicakliginin altinda ({component_text}); "
                "kati faz riski nedeniyle CoolProp faz flash'i desteklenmedi."
            )
        elif fallback_reason:
            warning_message = (
                "CoolProp faz flash'i bu PT noktasinda cozulmedi. "
                "Faz zarfi disi veya metastabil bolge nedeniyle sonuc tek-faz varsayimiyla yorumlanmalidir."
            )
        else:
            warning_message = "Faz belirlenemedi. Hesap tek faz varsayimlariyla yorumlanmalidir."

        phase_info = {
            "phase": "unknown",
            "phase_label_tr": "Belirsiz",
            "vapor_quality": vapor_quality,
            "warning_level": "critical" if low_temperature_components else "warning",
            "warning_msg_tr": warning_message,
            "phase_code": phase_code,
            "solid_risk_components": low_temperature_components or None,
            "phase_detection_error": fallback_reason,
        }
        if fallback_reason and not envelope_hint:
            self.log(
                "CoolProp faz tespiti PT flash ile cozulmedi; envelope veya model fallback kullanilacak.",
                "WARNING",
            )
        return phase_info

    def enrich_phase_info(self, phase_info, flow_mode):
        info = dict(phase_info)
        phase = info.get("phase")

        if phase == "two_phase":
            info["formula_mode"] = "two_phase"
            info["formula_label_tr"] = "Lockhart-Martinelli Iki Fazli Korelasyon"
        elif phase == "liquid":
            info["formula_mode"] = "single_phase_liquid"
            info["formula_label_tr"] = "Darcy-Weisbach + Churchill f + Ivmelenme Duzeltmesi"
        elif normalize_flow_mode(flow_mode) == FLOW_MODE_INCOMPRESSIBLE:
            info["formula_mode"] = "single_phase_incompressible_gas"
            info["formula_label_tr"] = "Darcy-Weisbach (Sabit Yogunluk)"
        else:
            info["formula_mode"] = "single_phase_gas"
            info["formula_label_tr"] = "Darcy-Weisbach (Sikistirilabilir Gaz)"

        return info

    def _build_phase_split_state(self, fluids, fractions):
        state = cp_abstract_state("HEOS", "&".join(fluids))
        state.set_mole_fractions(fractions)
        return state

    def _phase_split_properties(self, P, T, mole_fractions, state):
        normalized = self.normalize_mole_fractions(mole_fractions)
        fluids = list(normalized.keys())

        quality_molar = state.Q()
        liquid_fractions = state.mole_fractions_liquid()
        vapor_fractions = state.mole_fractions_vapor()

        liquid_state = self._build_phase_split_state(fluids, liquid_fractions)
        vapor_state = self._build_phase_split_state(fluids, vapor_fractions)
        liquid_state.update(CP.PT_INPUTS, P, T)
        vapor_state.update(CP.PT_INPUTS, P, T)

        mw_liquid = liquid_state.molar_mass()
        mw_vapor = vapor_state.molar_mass()
        denom = quality_molar * mw_vapor + (1.0 - quality_molar) * mw_liquid
        quality_mass = quality_molar if denom <= 0 else (quality_molar * mw_vapor) / denom

        return {
            "quality_molar": quality_molar,
            "quality_mass": quality_mass,
            "rho_liquid": liquid_state.rhomass(),
            "rho_vapor": vapor_state.rhomass(),
            "mu_liquid": liquid_state.viscosity(),
            "mu_vapor": vapor_state.viscosity(),
        }

    def _single_phase_segment_loss(
        self,
        mass_flow,
        density,
        viscosity,
        dL,
        D_m,
        area,
        relative_roughness,
        K_seg,
        friction_model="colebrook",
    ):
        velocity = mass_flow / (density * area) if density > 0 else 0.0
        if velocity <= 0 or viscosity <= 0:
            return {
                "dp_total": 0.0,
                "dp_friction": 0.0,
                "dp_fitting": 0.0,
                "dp_acceleration": 0.0,
                "velocity": velocity,
                "Re": 0.0,
                "f": 0.0,
            }

        Re = (density * velocity * D_m) / viscosity
        if friction_model == "churchill":
            f = self.get_churchill_friction_factor(Re, relative_roughness)
        else:
            f = self.get_friction_factor(Re, relative_roughness)
        dp_friction = f * (dL / D_m) * (density * velocity**2) / 2
        dp_fitting = K_seg * (density * velocity**2) / 2
        return {
            "dp_total": dp_friction + dp_fitting,
            "dp_friction": dp_friction,
            "dp_fitting": dp_fitting,
            "dp_acceleration": 0.0,
            "velocity": velocity,
            "Re": Re,
            "f": f,
        }

    def _liquid_acceleration_loss(self, mass_flow, area, density_in, density_out):
        if area <= 0 or density_in <= 0 or density_out <= 0:
            return 0.0
        mass_flux = mass_flow / area
        return mass_flux * mass_flux * ((1.0 / density_out) - (1.0 / density_in))

    def _two_phase_segment_loss(self, m_dot, dL, D_m, area, relative_roughness, K_seg, split_props):
        quality_mass = min(max(split_props["quality_mass"], 1e-6), 1.0 - 1e-6)

        liquid_loss = self._single_phase_segment_loss(
            m_dot * (1.0 - quality_mass),
            split_props["rho_liquid"],
            split_props["mu_liquid"],
            dL,
            D_m,
            area,
            relative_roughness,
            K_seg,
            friction_model="churchill",
        )
        vapor_loss = self._single_phase_segment_loss(
            m_dot * quality_mass,
            split_props["rho_vapor"],
            split_props["mu_vapor"],
            dL,
            D_m,
            area,
            relative_roughness,
            K_seg,
        )

        dp_liquid = max(liquid_loss["dp_total"], 1e-9)
        dp_vapor = max(vapor_loss["dp_total"], 1e-9)
        X = math.sqrt(dp_liquid / dp_vapor)
        phi_l_sq = 1.0 + 20.0 / max(X, 1e-6) + 1.0 / max(X * X, 1e-6)
        dp_total = phi_l_sq * dp_liquid

        bulk_density = 1.0 / (
            quality_mass / split_props["rho_vapor"] + (1.0 - quality_mass) / split_props["rho_liquid"]
        )
        bulk_velocity = m_dot / (bulk_density * area)

        return {
            "dp_total": dp_total,
            "dp_friction": dp_total,
            "dp_fitting": 0.0,
            "velocity": bulk_velocity,
            "Re": vapor_loss["Re"],
            "f": vapor_loss["f"],
            "quality_mass": quality_mass,
            "phi_l_sq": phi_l_sq,
        }

    def _get_std_density(self, mixture):
        """Standart yoğunluğu cache’den al veya hesapla.
        101325 Pa, 288.15 K değişmediğinden her hesaplama için 1 kere yeterli."""
        if mixture not in self._std_density_cache:
            try:
                d = cp_propssi('D', 'P', 101325, 'T', 288.15, mixture)
            except Exception:
                d = 0.0
            self._std_density_cache[mixture] = d
        return self._std_density_cache[mixture]

    def _state_phase_candidates(self, phase_hint, low_temperature_components):
        if phase_hint == "gas":
            return (CP.iphase_gas, CP.iphase_liquid)
        if phase_hint == "liquid":
            return (CP.iphase_liquid, CP.iphase_twophase, CP.iphase_gas)
        if phase_hint == "two_phase":
            return (CP.iphase_liquid, CP.iphase_gas)
        if low_temperature_components:
            return (CP.iphase_liquid, CP.iphase_twophase, CP.iphase_gas)
        return (CP.iphase_gas, CP.iphase_liquid)

    def _update_state_with_phase_fallback(self, state, P, T, mole_fractions, phase_info=None):
        try:
            state.unspecify_phase()
        except Exception:
            pass

        try:
            state.update(CP.PT_INPUTS, P, T)
            return {"mode": "direct", "imposed_phase": None}
        except ValueError as direct_error:
            resolved_phase_info = phase_info
            if resolved_phase_info is None:
                if mole_fractions:
                    resolved_phase_info = self.detect_phase(P, T, mole_fractions, state=None)
                else:
                    resolved_phase_info = {"phase": "unknown", "solid_risk_components": []}
            phase_hint = resolved_phase_info.get("phase")
            low_temperature_components = resolved_phase_info.get("solid_risk_components") or []
            last_error = direct_error

            for imposed_phase in self._state_phase_candidates(phase_hint, low_temperature_components):
                try:
                    try:
                        state.unspecify_phase()
                    except Exception:
                        pass
                    state.specify_phase(imposed_phase)
                    state.update(CP.PT_INPUTS, P, T)
                    return {"mode": "imposed", "imposed_phase": imposed_phase}
                except Exception as imposed_error:
                    last_error = imposed_error

            raise last_error

    def _approximate_two_phase_split_properties(self, P, T, mole_fractions, phase_info):
        normalized = self.normalize_mole_fractions(mole_fractions)
        gas_state = self.create_coolprop_state(normalized)
        liquid_state = self.create_coolprop_state(normalized)
        if gas_state is None or liquid_state is None:
            raise ValueError("Iki faz yaklasik split state olusturulamadi.")

        gas_state.specify_phase(CP.iphase_gas)
        gas_state.update(CP.PT_INPUTS, P, T)
        liquid_state.specify_phase(CP.iphase_liquid)
        liquid_state.update(CP.PT_INPUTS, P, T)

        quality_mass = phase_info.get("vapor_quality")
        if quality_mass is None:
            quality_mass = 0.5

        return {
            "quality_molar": quality_mass,
            "quality_mass": min(max(quality_mass, 1e-6), 1.0 - 1e-6),
            "rho_liquid": liquid_state.rhomass(),
            "rho_vapor": gas_state.rhomass(),
            "mu_liquid": liquid_state.viscosity(),
            "mu_vapor": gas_state.viscosity(),
            "approximate": True,
        }

    def _get_two_phase_split_properties(self, P, T, mole_fractions, state, phase_info):
        try:
            self._update_state_with_phase_fallback(state, P, T, mole_fractions, phase_info=phase_info)
            quality = state.Q()
            if 0.0 <= quality <= 1.0 and int(state.phase()) == CP.iphase_twophase:
                split_props = self._phase_split_properties(P, T, mole_fractions, state)
                split_props["approximate"] = False
                return split_props
        except Exception:
            pass

        self.log(
            "CoolProp iki faz PT split cozulmedi; gaz/sivi dallari ile yaklasik split kullaniliyor.",
            "WARNING",
        )
        return self._approximate_two_phase_split_properties(P, T, mole_fractions, phase_info)

    def calculate_coolprop_properties(self, P, T, mixture, state=None, mole_fractions=None):
        # Termodinamik özellik cache’i: aynı (P, T, mixture) üçlüsü için tekrar hesaplama
        cache_key = (round(P, 1), round(T, 4), mixture)
        if cache_key in self._thermo_cache:
            return self._thermo_cache[cache_key]
        
        viscosity_fallback = False

        # —— Standart yoğunluk: cache’den ——
        standard_density = self._get_std_density(mixture)
        if state:
            try:
                phase_info = None
                if mole_fractions is not None:
                    phase_info = self.detect_phase(P, T, mole_fractions, state=None)
                state_resolution = self._update_state_with_phase_fallback(
                    state,
                    P,
                    T,
                    mole_fractions or {},
                    phase_info=phase_info,
                )
                density = state.rhomass()
                viscosity = state.viscosity()
                MW_mix = state.molar_mass() * 1000
                Cp = state.cpmass() / 1000
                Cv = state.cvmass() / 1000
                Z = state.compressibility_factor()
                thermo_fallback = state_resolution["mode"] != "direct"
                
                # Standart yoğunluk artık cache’den geliyor (yukarıda hesaplanıyor)
                
                # Sonic Velocity
                try: 
                    sonic_velocity = state.speed_sound()
                except ValueError:
                    gamma = Cp / Cv if Cv > 0 else 1.3
                    sonic_velocity = math.sqrt(gamma * Z * R_J_mol_K * T / (MW_mix * 1e-3))
                
            except ValueError as e:
                 if mole_fractions is not None:
                     self.log(
                         "CoolProp PT flash cozulmedi; Peng-Robinson fallback ile hesap devam ediyor.",
                         "WARNING",
                     )
                     props = self.calculate_cubic_eos_props(P, T, mole_fractions, "PR")
                     props["standard_density"] = standard_density
                     props["viscosity_fallback"] = True
                     props["thermo_fallback"] = True
                     props["fallback_reason"] = str(e)
                     self._thermo_cache[cache_key] = props
                     return props
                 return self.calculate_coolprop_properties(P, T, mixture, state=None, mole_fractions=None)
        else:
            # AbstractState yok, doğrudan PropsSI — standart yoğunluk cache’den zaten geldi
            
            MW_mix = cp_propssi('M', 'P', P, 'T', T, mixture) * 1000
            thermo_fallback = False

            try:
                viscosity = cp_propssi('V', 'P', P, 'T', T, mixture)
            except Exception:
                viscosity_fallback = True
                viscosity = 1.5e-5 * math.sqrt(MW_mix / 16.04) # Basit tahmin
            
            Cp = cp_propssi('C', 'P', P, 'T', T, mixture) / 1000
            Cv = cp_propssi('O', 'P', P, 'T', T, mixture) / 1000
            Z = cp_propssi('Z', 'P', P, 'T', T, mixture)
            density = cp_propssi('D', 'P', P, 'T', T, mixture)
            
            try:
                sonic_velocity = cp_propssi('A', 'P', P, 'T', T, mixture)
            except ValueError:
                gamma = Cp / Cv if Cv > 0 else 1.3
                sonic_velocity = math.sqrt(gamma * Z * R_J_mol_K * T / (MW_mix * 1e-3))

        props = {
            "MW": MW_mix, "Cp": Cp, "Cv": Cv, "Z": Z,
            "density": density,
            "viscosity": viscosity, "standard_density": standard_density, 
            "viscosity_fallback": viscosity_fallback,
            "thermo_fallback": thermo_fallback,
            "sonic_velocity": sonic_velocity
        }
        # Cache'e kaydet (cache_key yukarıda tanımlandı)
        self._thermo_cache[cache_key] = props
        return props

    def calculate_pseudo_critical_properties(self, P, T, mole_fractions):
        mole_fractions = self.normalize_mole_fractions(mole_fractions)
        # self.log("Hesaplama: Pseudo-Critical (Kay's Rule) modeli kullanılıyor.", "DEBUG")
        Ppc, Tpc, MW_mix = 0, 0, 0
        for gas, y in mole_fractions.items():
            props = self.get_pure_component_props(gas)
            Ppc += y * props['Pc']; Tpc += y * props['Tc']; MW_mix += y * props['MW']
        
        Pr = P / Ppc; Tr = T / Tpc
        # Dranchuk-Abou-Kassem (DAK) Z-Factor Correlation
        # Iterative Solution
        # Constants
        A1 = 0.3265; A2 = -1.0700; A3 = -0.5339; A4 = 0.01569; A5 = -0.05165
        A6 = 0.5475; A7 = -0.7361; A8 = 0.1844; A9 = 0.1056; A10 = 0.6134; A11 = 0.7210
        
        # Initial guess for reduced density rho_r
        # Hall-Yarborough initial guess
        t_r = 1.0 / Tr
        A = 0.06125 * t_r * math.exp(-1.2 * (1 - t_r)**2)
        if Pr < 0.01:
            Z = 1.0
        else:
            rho_r = 0.27 * Pr / Tr # Ideal gas approximation

            # Newton-Raphson Iteration
            for _ in range(20):
                R1 = A1 + A2/Tr + A3/Tr**3 + A4/Tr**4 + A5/Tr**5
                R2 = 0.27 * Pr / Tr
                R3 = A6 + A7/Tr + A8/Tr**2
                R4 = A9 * (A7/Tr + A8/Tr**2)
                
                exp_term = math.exp(-A11 * rho_r**2)
                
                f = R1*rho_r - R2/rho_r + R3*rho_r**2 - R4*rho_r**5 + \
                    A10 * (1 + A11*rho_r**2) * (rho_r**2 / Tr**3) * exp_term + 1
                
                d_term_exp = (2*A10*rho_r/Tr**3) * exp_term * (1 + A11*rho_r**2) - \
                             (2*A10*A11*rho_r**3/Tr**3) * exp_term * (1 + A11*rho_r**2) + \
                             A10 * (rho_r**2/Tr**3) * exp_term * (2*A11*rho_r)
                
                df = R1 + R2/rho_r**2 + 2*R3*rho_r - 5*R4*rho_r**4 + d_term_exp
                
                if abs(df) < 1e-6: break
                rho_r_new = rho_r - f / df
                if abs(rho_r_new - rho_r) < 1e-6:
                    rho_r = rho_r_new; break
                rho_r = rho_r_new
                
            Z = (0.27 * Pr) / (rho_r * Tr) if rho_r > 0 else 1.0
            
        density = (P * MW_mix * 1e-3) / (Z * R_J_mol_K * T)
        standard_density = (101325 * MW_mix * 1e-3) / (1.0 * R_J_mol_K * 288.15) 
        
        # Lee-Gonzalez-Eakin Viscosity Correlation
        # API Technical Data Book Procedure 11A4.1
        # MW: Molecular Weight
        # T: Temperature (Rankine) -> Convert K to R
        # rho: Density (g/cc) -> Convert kg/m3 to g/cc
        
        T_R = T * 1.8
        rho_gcc = density / 1000.0
        
        X = 3.5 + 986.0 / T_R + 0.01 * MW_mix
        Y = 2.4 - 0.2 * X
        K = ( (9.4 + 0.02 * MW_mix) * T_R**1.5 ) / (209 + 19 * MW_mix + T_R)
        
        viscosity_micropoise = K * math.exp(X * (rho_gcc**Y))
        viscosity = viscosity_micropoise * 1e-7 # Convert Micropoise to Pa.s (1 uP = 1e-7 Pa.s)

        Cp_mix, Cv_mix = 0, 0
        for gas, y in mole_fractions.items():
            try:
                cp_i = cp_propssi('CP0MASS', 'T', T, 'P', 101325, gas) / 1000
                cv_i = cp_propssi('CV0MASS', 'T', T, 'P', 101325, gas) / 1000
                Cp_mix += y * cp_i
                Cv_mix += y * cv_i
            except ValueError:
                Cp_mix += y * 2.0; Cv_mix += y * 1.6 # Tahmini değerler
        
        # k_avg düzeltmesi
        if Cv_mix == 0: Cv_mix = 1.0
        k_avg = Cp_mix / Cv_mix
        
        # Sonic Velocity Check (Ideal Gas Approx with Z)
        # c = sqrt(k * Z * R * T / MW)
        gamma = k_avg
        sonic_velocity = math.sqrt(gamma * Z * R_J_mol_K * T / (MW_mix * 1e-3))

        return {
            "MW": MW_mix, "Cp": Cp_mix, "Cv": Cv_mix, "Z": Z, "density": density,
            "viscosity": viscosity, "standard_density": standard_density,
            "Ppc": Ppc, "Tpc": Tpc, "Pr": Pr, "Tr": Tr,
            "sonic_velocity": sonic_velocity
        }

    def calculate_thermo_properties(self, P, T, mole_fractions, library_choice, state=None):
        mole_fractions = self.normalize_mole_fractions(mole_fractions)
        if library_choice == "CoolProp (High Accuracy EOS)":
            mixture = self.build_mixture_string(mole_fractions)
            return self.calculate_coolprop_properties(P, T, mixture, state, mole_fractions=mole_fractions)
        elif library_choice == "Peng-Robinson (PR EOS)":
            return self.calculate_cubic_eos_props(P, T, mole_fractions, "PR")
        elif library_choice == "Soave-Redlich-Kwong (SRK EOS)":
            return self.calculate_cubic_eos_props(P, T, mole_fractions, "SRK")
        elif library_choice == "Pseudo-Critical (Kay's Rule)":
            return self.calculate_pseudo_critical_properties(P, T, mole_fractions)
        else:
            raise ValueError(f"Geçersiz termodinamik model seçimi: {library_choice}")

    # --- AKIŞ VE BORU HESAPLARI ---
    def calculate_pressure_drop(self, inputs, num_segments=20):
        """
        Giriş: P_in, T, mole_fractions, library_choice, flow_rate, D_inner, L, roughness, total_k, flow_property
        Çıkış: P_out, delta_p_total, delta_p_pipe, delta_p_fittings, velocity_in, velocity_out, status, profile_data
        """
        P_in = inputs['P_in']; T = inputs['T']; mole_fractions = inputs['mole_fractions']
        library_choice = inputs['library_choice']; flow_val = inputs['flow_rate']; flow_unit = inputs['flow_unit']
        D_inner = inputs['D_inner']; L = inputs['L']; roughness = inputs['roughness']; total_k = inputs['total_k']
        flow_property = inputs.get('flow_property')
        flow_mode = inputs.get('flow_mode') or normalize_flow_mode(flow_property)

        # CoolProp State Optimization
        cp_state = None
        if library_choice == "CoolProp (High Accuracy EOS)":
            cp_state = self.create_coolprop_state(mole_fractions)

        phase_info_inlet = self.enrich_phase_info(
            self.detect_phase(P_in, T, mole_fractions, state=cp_state),
            flow_mode,
        )
        gas_props_in = self.calculate_thermo_properties(P_in, T, mole_fractions, library_choice, cp_state)
        rho_in = gas_props_in['density']

        m_dot = self.calculate_mass_flow_rate(flow_val, flow_unit, gas_props_in['standard_density'])

        # Çapı metreye çevir (Girdi mm)

        D_m = D_inner / 1000.0
        A = math.pi * (D_m ** 2) / 4
        velocity_in = m_dot / (rho_in * A)
        relative_roughness = roughness / D_m

        delta_p_total = 0.0; delta_p_pipe = 0.0; delta_p_fittings = 0.0
        Re_final = 0.0; f_final = 0.0; P_out = P_in; velocity_out = velocity_in

        segment_count = max(1, int(num_segments) if num_segments else 1)
        dL = L / segment_count if segment_count > 0 else 0.0
        K_seg = total_k / segment_count if segment_count > 0 else total_k

        profile_data = {"distance": [0.0], "pressure": [P_in], "velocity": [velocity_in]}
        phase_profile = [{
            "distance": 0.0,
            "phase": phase_info_inlet["phase"],
            "phase_label_tr": phase_info_inlet["phase_label_tr"],
            "vapor_quality": phase_info_inlet.get("vapor_quality"),
            "formula_mode": phase_info_inlet["formula_mode"],
            "formula_label_tr": phase_info_inlet["formula_label_tr"],
        }]

        P_current = P_in
        total_pipe_loss = 0.0
        total_fitting_loss = 0.0
        total_acceleration_loss = 0.0
        first_two_phase_info = phase_info_inlet if phase_info_inlet["phase"] == "two_phase" else None
        transition_to_two_phase_m = 0.0 if first_two_phase_info else None
        fixed_density = gas_props_in["density"]
        fixed_viscosity = gas_props_in["viscosity"]
        phase_info_out = phase_info_inlet

        for i in range(segment_count):
            current_phase = self.enrich_phase_info(
                self.detect_phase(P_current, T, mole_fractions, state=cp_state),
                flow_mode,
            )

            if current_phase["phase"] == "two_phase" and library_choice == "CoolProp (High Accuracy EOS)" and cp_state is not None:
                split_props = self._get_two_phase_split_properties(
                    P_current, T, mole_fractions, cp_state, current_phase
                )
                segment = self._two_phase_segment_loss(
                    m_dot, dL, D_m, A, relative_roughness, K_seg, split_props
                )
                P_next = max(MIN_PRESSURE_PA, P_current - segment["dp_total"])
            else:
                props = self.calculate_thermo_properties(P_current, T, mole_fractions, library_choice, cp_state)
                density = props["density"]
                viscosity = props["viscosity"]
                liquid_phase = current_phase["phase"] == "liquid"
                if flow_mode == FLOW_MODE_INCOMPRESSIBLE and not liquid_phase:
                    density = fixed_density
                    viscosity = fixed_viscosity
                segment = self._single_phase_segment_loss(
                    m_dot,
                    density,
                    viscosity,
                    dL,
                    D_m,
                    A,
                    relative_roughness,
                    K_seg,
                    friction_model="churchill" if liquid_phase else "colebrook",
                )
                P_next = max(MIN_PRESSURE_PA, P_current - segment["dp_total"])
                if liquid_phase:
                    for _ in range(2):
                        next_props = self.calculate_thermo_properties(P_next, T, mole_fractions, library_choice, cp_state)
                        dp_acceleration = self._liquid_acceleration_loss(
                            m_dot,
                            A,
                            density,
                            next_props["density"],
                        )
                        P_updated = max(MIN_PRESSURE_PA, P_current - segment["dp_friction"] - segment["dp_fitting"] - dp_acceleration)
                        segment["dp_acceleration"] = dp_acceleration
                        segment["dp_total"] = segment["dp_friction"] + segment["dp_fitting"] + dp_acceleration
                        if abs(P_updated - P_next) < 1.0:
                            P_next = P_updated
                            break
                        P_next = P_updated
            current_dist = (i + 1) * dL

            total_pipe_loss += segment["dp_friction"]
            total_fitting_loss += segment["dp_fitting"]
            total_acceleration_loss += segment.get("dp_acceleration", 0.0)
            Re_final = segment["Re"]
            f_final = segment["f"]

            next_phase = self.enrich_phase_info(
                self.detect_phase(P_next, T, mole_fractions, state=cp_state),
                flow_mode,
            )
            if first_two_phase_info is None and next_phase["phase"] == "two_phase":
                first_two_phase_info = dict(next_phase)
                transition_to_two_phase_m = current_dist

            if next_phase["phase"] == "two_phase" and library_choice == "CoolProp (High Accuracy EOS)" and cp_state is not None:
                split_props_next = self._get_two_phase_split_properties(
                    P_next, T, mole_fractions, cp_state, next_phase
                )
                bulk_density_next = 1.0 / (
                    split_props_next["quality_mass"] / split_props_next["rho_vapor"] +
                    (1.0 - split_props_next["quality_mass"]) / split_props_next["rho_liquid"]
                )
                v_next = m_dot / (bulk_density_next * A)
            elif flow_mode == FLOW_MODE_INCOMPRESSIBLE and next_phase["phase"] != "liquid":
                v_next = velocity_in
            else:
                next_props = self.calculate_thermo_properties(P_next, T, mole_fractions, library_choice, cp_state)
                v_next = m_dot / (next_props["density"] * A)

            profile_data["distance"].append(current_dist)
            profile_data["pressure"].append(P_next)
            profile_data["velocity"].append(v_next)
            phase_profile.append({
                "distance": current_dist,
                "phase": next_phase["phase"],
                "phase_label_tr": next_phase["phase_label_tr"],
                "vapor_quality": next_phase.get("vapor_quality"),
                "formula_mode": next_phase["formula_mode"],
                "formula_label_tr": next_phase["formula_label_tr"],
            })

            P_current = P_next
            phase_info_out = next_phase

        P_out = P_current
        gas_props_out = self.calculate_thermo_properties(P_out, T, mole_fractions, library_choice, cp_state)

        if phase_info_out["phase"] == "two_phase" and library_choice == "CoolProp (High Accuracy EOS)" and cp_state is not None:
            split_props_out = self._get_two_phase_split_properties(
                P_out, T, mole_fractions, cp_state, phase_info_out
            )
            bulk_density_out = 1.0 / (
                split_props_out["quality_mass"] / split_props_out["rho_vapor"] +
                (1.0 - split_props_out["quality_mass"]) / split_props_out["rho_liquid"]
            )
            velocity_out = m_dot / (bulk_density_out * A)
        elif flow_mode == FLOW_MODE_INCOMPRESSIBLE and phase_info_out["phase"] != "liquid":
            velocity_out = velocity_in
        else:
            velocity_out = m_dot / (gas_props_out["density"] * A)

        profile_data["velocity"][-1] = velocity_out
        delta_p_total = P_in - P_out
        delta_p_pipe = total_pipe_loss
        delta_p_fittings = total_fitting_loss
        delta_p_acceleration = total_acceleration_loss

        choked_flow_status = "N/A"
        if phase_info_out["phase"] in {"gas", "supercritical"} and flow_mode != FLOW_MODE_INCOMPRESSIBLE:
            sonic_velocity_out = gas_props_out.get("sonic_velocity", 340)
            choked_flow_status = "OK"
            if velocity_out > sonic_velocity_out:
                choked_flow_status = "CHOKED (Sonik Hız Aşıldı!)"
            elif velocity_out > 0.8 * sonic_velocity_out:
                choked_flow_status = "Warning (Mach > 0.8)"

        phase_info = first_two_phase_info or phase_info_out
        if transition_to_two_phase_m is not None and phase_info["phase"] == "two_phase":
            phase_info = dict(phase_info)
            phase_info["transition_to_two_phase_m"] = transition_to_two_phase_m

        return {
            "P_out": P_out, "delta_p_total": delta_p_total,
            "delta_p_pipe": delta_p_pipe, "delta_p_fittings": delta_p_fittings,
            "delta_p_acceleration": delta_p_acceleration,
            "velocity_in": velocity_in, "velocity_out": velocity_out,
            "Re": Re_final, "f": f_final,
            "gas_props_in": gas_props_in, "gas_props_out": gas_props_out,
            "m_dot": m_dot,
            "profile_data": profile_data,
            "phase_profile": phase_profile,
            "transition_to_two_phase_m": transition_to_two_phase_m,
            "choked_status": choked_flow_status,
            "flow_mode": flow_mode,
            "phase_info": phase_info,
        }

    def calculate_max_length(self, inputs):
        """Maksimum uzunluk hesabı (Binary Search)."""
        P_in = inputs['P_in']; P_out_target = inputs['P_out_target']
        flow_property = inputs.get('flow_property')
        flow_mode = inputs.get('flow_mode') or normalize_flow_mode(flow_property)
        phase_info = self.enrich_phase_info(
            self.detect_phase(P_in, inputs['T'], inputs['mole_fractions']),
            flow_mode,
        )
        
        # Basınç Kontrolü
        if P_out_target > P_in: 
            raise ValueError("Çıkış basıncı giriş basıncından büyük olamaz.")
        if abs(P_in - P_out_target) < 100: # 1 mbar farktan az ise 0 kabul et
             # Temel debi hesabı için yine de özelliklere ihtiyaç var
             gas_props_in = self.calculate_thermo_properties(P_in, inputs['T'], inputs['mole_fractions'], inputs['library_choice'])
             m_dot = self.calculate_mass_flow_rate(inputs['flow_rate'], inputs['flow_unit'], gas_props_in['standard_density'])
                
             return {
                "L_max": 0, 
                "Re": 0, "f": 0, 
                "delta_p_pipe": 0, "delta_p_fittings": 0, "delta_p_acceleration": 0,
                "m_dot": m_dot,
                "gas_props_in": gas_props_in,
                "gas_props_out": gas_props_in,
                "note": "Giriş ve çıkış basıncı eşit.",
                "phase_info": phase_info,
                "flow_mode": flow_mode,
            }
        
        T = inputs['T']; mole_fractions = inputs['mole_fractions']
        library_choice = inputs['library_choice']; flow_val = inputs['flow_rate']; flow_unit = inputs['flow_unit']
        D_inner = inputs['D_inner']; roughness = inputs['roughness']; total_k = inputs['total_k']

        # Temel Özellikler
        # CoolProp State Optimization
        cp_state = None
        if library_choice == "CoolProp (High Accuracy EOS)":
            cp_state = self.create_coolprop_state(mole_fractions)

        gas_props_in = self.calculate_thermo_properties(P_in, T, mole_fractions, library_choice, cp_state)
        rho_in = gas_props_in['density']
        
        m_dot = self.calculate_mass_flow_rate(flow_val, flow_unit, gas_props_in['standard_density'])

        # Çapı metreye çevir
        D_m = D_inner / 1000.0
        A = math.pi * (D_m ** 2) / 4
        velocity_in = m_dot / (rho_in * A)
        relative_roughness = roughness / D_m
        
        delta_p_total_target = P_in - P_out_target
        L_max = 0; Re_final = 0; f_final = 0; delta_p_pipe = 0; delta_p_fittings = 0; delta_p_acceleration = 0
        phase_aware_binary = phase_info["phase"] in {"liquid", "two_phase", "unknown"}

        if phase_aware_binary:
            def solve_outlet_pressure(length, num_segments):
                profile_inputs = dict(inputs)
                profile_inputs["L"] = length
                profile_inputs["flow_mode"] = flow_mode
                profile_result = self.calculate_pressure_drop(profile_inputs, num_segments=num_segments)
                return profile_result["P_out"], profile_result

            P_min_length, zero_profile = solve_outlet_pressure(0.0, num_segments=4)
            if P_min_length < P_out_target:
                return {
                    "L_max": 0,
                    "Re": zero_profile.get("Re", 0.0),
                    "f": zero_profile.get("f", 0.0),
                    "delta_p_pipe": zero_profile.get("delta_p_pipe", 0.0),
                    "delta_p_fittings": zero_profile.get("delta_p_fittings", 0.0),
                    "delta_p_acceleration": zero_profile.get("delta_p_acceleration", 0.0),
                    "m_dot": m_dot,
                    "gas_props_in": zero_profile.get("gas_props_in", gas_props_in),
                    "gas_props_out": zero_profile.get("gas_props_out", gas_props_in),
                    "error": "Sifir boru uzunlugunda bile fitting kayiplari hedef cikis basincini saglamiyor.",
                    "phase_info": zero_profile.get("phase_info", phase_info),
                    "flow_mode": flow_mode,
                }

            L_low, L_high = 0.0, 1000000.0
            best_profile = zero_profile

            for _ in range(40):
                L_mid = (L_low + L_high) / 2
                P2, profile = solve_outlet_pressure(L_mid, num_segments=8)
                if P2 < P_out_target:
                    L_high = L_mid
                else:
                    L_low = L_mid
                    best_profile = profile

                if abs(L_high - L_low) < 0.1:
                    break

            L_max = L_low
            Re_final = best_profile.get("Re", 0.0)
            f_final = best_profile.get("f", 0.0)
            delta_p_pipe = best_profile.get("delta_p_pipe", 0.0)
            delta_p_fittings = best_profile.get("delta_p_fittings", 0.0)
            delta_p_acceleration = best_profile.get("delta_p_acceleration", 0.0)
            phase_info = best_profile.get("phase_info", phase_info)
        elif flow_mode == FLOW_MODE_INCOMPRESSIBLE:
            mu = gas_props_in['viscosity']
            Re = (rho_in * velocity_in * D_m) / mu if mu > 0 else 0.0
            f = self.get_churchill_friction_factor(Re, relative_roughness)
            
            delta_p_fittings = total_k * (rho_in * velocity_in ** 2) / 2
            if delta_p_fittings >= delta_p_total_target:
                return {
                    "L_max": 0,
                    "error": "Boru elemanı kayıpları toplam basınç farkını aşıyor!",
                    "phase_info": phase_info,
                    "flow_mode": flow_mode,
                    "gas_props_in": gas_props_in,
                    "gas_props_out": gas_props_in,
                }
            
            available_delta_p_pipe = delta_p_total_target - delta_p_fittings
            L_max = (available_delta_p_pipe * 2 * D_m) / (f * rho_in * velocity_in ** 2)
            
            Re_final = Re; f_final = f; delta_p_pipe = available_delta_p_pipe

        else: # Sıkıştırılabilir (Binary Search)
            def solve_outlet_pressure(length):
                P1 = P_in
                P2 = P1 if length <= 0 else P1 * 0.9
                Re = 0.0; f = 0.0; dp_pipe_local = 0.0; dp_fit_local = 0.0

                for _ in range(20):
                    P_avg = (P1 + P2) / 2
                    props = self.calculate_thermo_properties(P_avg, T, mole_fractions, library_choice, cp_state)
                    rho = props['density']; mu = props['viscosity']; v = m_dot / (rho * A)
                    Re = (rho * v * D_m) / mu; f = self.get_friction_factor(Re, relative_roughness)

                    dp_pipe_local = f * (length / D_m) * (rho * v**2) / 2
                    dp_fit_local = total_k * (rho * v**2) / 2
                    current_delta_p_total = dp_pipe_local + dp_fit_local

                    P2_new = max(MIN_PRESSURE_PA, P1 - current_delta_p_total)
                    if abs(P2_new - P2) < 100:
                        P2 = P2_new
                        break
                    P2 = P2_new

                return P2, Re, f, dp_pipe_local, dp_fit_local

            P_min_length, Re_zero, f_zero, _, dp_fit_zero = solve_outlet_pressure(0.0)
            if P_min_length < P_out_target:
                return {
                    "L_max": 0,
                    "Re": Re_zero,
                    "f": f_zero,
                    "delta_p_pipe": 0,
                    "delta_p_fittings": dp_fit_zero,
                    "m_dot": m_dot,
                    "error": "Sifir boru uzunlugunda bile fitting kayiplari hedef cikis basincini saglamiyor.",
                    "phase_info": phase_info,
                    "flow_mode": flow_mode,
                }

            L_low, L_high = 0.0, 1000000.0 # 1000 km üst limit
            best_Re = Re_zero; best_f = f_zero; best_dp_pipe = 0.0; best_dp_fit = dp_fit_zero

            for _ in range(50): # Binary Search İterasyonu
                L_mid = (L_low + L_high) / 2
                P2, Re, f, dp_pipe_mid, dp_fit_mid = solve_outlet_pressure(L_mid)

                if P2 < P_out_target: # Basınç çok düştü, L çok uzun
                    L_high = L_mid
                else: # Basınç hala yüksek, L daha uzun olabilir
                    L_low = L_mid
                    best_Re = Re; best_f = f; best_dp_pipe = dp_pipe_mid; best_dp_fit = dp_fit_mid

                if abs(L_high - L_low) < 0.1: break

            L_max = L_low
            Re_final = best_Re; f_final = best_f
            delta_p_pipe = best_dp_pipe; delta_p_fittings = best_dp_fit

        result = {
            "L_max": L_max, 
            "Re": Re_final, "f": f_final, 
            "delta_p_pipe": delta_p_pipe, "delta_p_fittings": delta_p_fittings,
            "delta_p_acceleration": delta_p_acceleration,
            "m_dot": m_dot,
            "gas_props_in": gas_props_in,
            "phase_info": phase_info,
            "flow_mode": flow_mode,
        }

        if L_max > 0:
            final_inputs = dict(inputs)
            final_inputs["L"] = L_max
            final_inputs["flow_mode"] = flow_mode
            final_profile = self.calculate_pressure_drop(final_inputs, num_segments=20)
            result["phase_info"] = final_profile.get("phase_info", phase_info)
            result["phase_profile"] = final_profile.get("phase_profile")
            result["transition_to_two_phase_m"] = final_profile.get("transition_to_two_phase_m")
            result["profile_data"] = final_profile.get("profile_data")
            result["gas_props_in"] = final_profile.get("gas_props_in", gas_props_in)
            result["gas_props_out"] = final_profile.get("gas_props_out", gas_props_in)
            result["delta_p_pipe"] = final_profile.get("delta_p_pipe", delta_p_pipe)
            result["delta_p_fittings"] = final_profile.get("delta_p_fittings", delta_p_fittings)
            result["delta_p_acceleration"] = final_profile.get("delta_p_acceleration", delta_p_acceleration)
        else:
            result["gas_props_out"] = gas_props_in

        return result


    def calculate_min_diameter(self, inputs):
        """Minimum çap hesabı ve ticari boru seçimi (İteratif ve Karşılaştırmalı)."""
        P_in = inputs['P_in']; T = inputs['T']; mole_fractions = inputs['mole_fractions']
        library_choice = inputs['library_choice']; flow_val = inputs['flow_rate']; flow_unit = inputs['flow_unit']
        max_vel = inputs['max_velocity']
        
        # Yeni Girdiler
        L = inputs.get('L', 0)
        flow_property = inputs.get('flow_property', "Sıkıştırılamaz")
        flow_mode = inputs.get('flow_mode') or normalize_flow_mode(flow_property)
        
        # Tasarım Parametreleri
        P_design = inputs['P_design']; material = inputs['material']
        SMYS_mpa = inputs.get('SMYS', PIPE_MATERIALS.get(material, 241))
        F = inputs['F']; E = inputs['E']; T_factor = inputs['T_factor']

        # Helper: API 5L Weight Calculation
        def calculate_pipe_weight_api5l(D_mm, t_mm):
            # w = t * (D - t) * 0.02466
            return t_mm * (D_mm - t_mm) * 0.02466

        # 1. Başlangıç Tahmini (Giriş Koşulları)
        gas_props_in = self.calculate_thermo_properties(P_in, T, mole_fractions, library_choice)
        rho_in = gas_props_in['density']
        
        m_dot = self.calculate_mass_flow_rate(flow_val, flow_unit, gas_props_in['standard_density'])
        flow_rate_actual_in = m_dot / rho_in

        if max_vel <= 0: raise ValueError("Maksimum hız pozitif olmalı.")
        
        # D_min tahmini (Referans için)
        D_min_inner_m = math.sqrt(4 * (flow_rate_actual_in / max_vel) / math.pi)
        D_min_inner_mm = D_min_inner_m * 1000

        # 2. İteratif Seçim ve Karşılaştırma
        # Tüm boruları al (Sıralı değil, gruplanmış lazım)
        all_pipes_flat = self.get_sorted_pipes(P_design, SMYS_mpa, F, E, T_factor) 
        # get_sorted_pipes zaten t_required kontrolü yapıyor.
        
        # Gruplama: Nominal Çap -> [Schedule List]
        grouped_pipes = {}
        for p in all_pipes_flat:
            nd = p['nominal']
            if nd not in grouped_pipes: grouped_pipes[nd] = []
            grouped_pipes[nd].append(p)
            
        # Nominal Çapları Sıralama (Küçükten büyüğe)
        def nd_sort_key(nd_str):
            try:
                s = nd_str.strip().replace('"', '')
                if ' ' in s: # e.g. "1 1/2"
                    parts = s.split(' ')
                    val = float(parts[0])
                    if '/' in parts[1]:
                        num, den = map(float, parts[1].split('/'))
                        val += num / den
                elif '/' in s: # e.g. "1/2"
                    num, den = map(float, s.split('/'))
                    val = num / den
                else: # e.g. "2" or "2.5"
                    val = float(s)
            except (ValueError, IndexError, ZeroDivisionError):
                val = 999.0
            return val
            
        sorted_nds = sorted(grouped_pipes.keys(), key=nd_sort_key)
        
        optimize_weight = inputs.get('optimize_weight', False)
        fast_calc = inputs.get('fast_calculation', True) # Yeni parametre

        selected_pipe = None
        final_result = None
        alternatives = {} # "thinner", "thicker", "lowest_weight" (if not selected)
        
        valid_candidates = []
        found_valid = False
        
        # En küçük çaptan başlayarak dene
        for nd in sorted_nds:
            schedules = sorted(grouped_pipes[nd], key=lambda x: x['t_mm']) # En inceden kalına
            
            # Bu ND için en ince (ve geçerli) schedule'ı al (zaten get_sorted_pipes geçerlileri döndürдü)
            candidate = schedules[0]
            
            # —— Öneri 2: Analitik Hız Ön Filtresi ——
            # Eğer ideal gaz yaklaşımıyla dahi hız limiti çok aşılıyorsa simulásyona girme
            D_cand_m = candidate['D_inner_mm'] / 1000.0
            A_cand = math.pi * (D_cand_m ** 2) / 4
            v_ideal = (m_dot / rho_in) / A_cand
            # Analitik oran: eğer ideal gaz tahmininde hız limitin %150'sinin üzerindeyse kesin uymuyor
            if v_ideal > max_vel * 1.5 and not found_valid:
                continue  # Bu çap çok küçük, simulásyona gerek yok
            
            if not found_valid or not fast_calc:
                # Simülasyon (Henüz geçerli bulunmadıysa VEYA hızlı hesaplama kapalıysa her çap için simülasyon yap)
                sim_inputs = inputs.copy()
                sim_inputs['D_inner'] = candidate['D_inner_mm'] # calculate_pressure_drop içinde metreye çevriliyor
                sim_res = self.calculate_pressure_drop(sim_inputs, num_segments=5) # Hızlı kontrol
                
                if sim_res['velocity_out'] <= max_vel:
                    found_valid = True
                    # Adayı kaydet
                    candidate['weight_per_m'] = calculate_pipe_weight_api5l(candidate['OD_mm'], candidate['t_mm'])
                    valid_candidates.append((candidate, nd, schedules))
                    
                    # Eğer ne ağırlık optimizasyonu ne de hızlı yoksayma istenmiyorsa (Yani V5'teki Orijinal Klasik Davranış)
                    if not optimize_weight and not fast_calc:
                        # V5'teki orijinal davranış simülasyona devam etmiyordu, ilk bulduğunda duruyordu.
                        # Ancak V6.1'de seçenekleri ayırdık. 
                        # Eğer Hızlı Hesaplama KAPALI ise, kullanıcının amacı tüm çaplar için basınç düşümünü görüp "En Düşük Ağırlığı" bulabilmek (arka planda olsa bile).
                        # Bu yüzden break YAPMIYORUZ, devam ediyoruz.
                        pass
                    
            else:
                # Daha büyük çaplar kesinlikle hız kriterini sağlar. Basınca da zaten baştan bakılmıştı.
                # Tekrar simülasyon yapmadan direkt ekle, sadece ağırlığı hesapla (Fast Calc = TRUE rotası)
                candidate['weight_per_m'] = calculate_pipe_weight_api5l(candidate['OD_mm'], candidate['t_mm'])
                valid_candidates.append((candidate, nd, schedules))

        if valid_candidates:
            if optimize_weight:
                # Tüm geçerli adayları ağırlığa göre sırala (en hafif olan en üstte)
                valid_candidates.sort(key=lambda x: x[0]['weight_per_m'])
                
            # İlk adayı seç (ya en küçük çap ya da en hafif)
            best_tuple = valid_candidates[0]
            selected_pipe = best_tuple[0]
            nd = best_tuple[1]
            schedules = best_tuple[2]
            
            # Hassas hesap
            sim_inputs = inputs.copy()
            sim_inputs['D_inner'] = selected_pipe['D_inner_mm']
            final_result = self.calculate_pressure_drop(sim_inputs, num_segments=20)
            final_result['velocity_status'] = "Uygun"
            
            # Ağırlık zaten hesaplıydı ama yine de koyalım
            if 'weight_per_m' not in selected_pipe:
                 selected_pipe['weight_per_m'] = calculate_pipe_weight_api5l(selected_pipe['OD_mm'], selected_pipe['t_mm'])
                 
            # Alternatifleri paralel simüle et (ThreadPoolExecutor)
            def run_alt_sim(inp):
                return self.calculate_pressure_drop(inp, num_segments=10)  # Öneri 3: 20 yerine 10 segment

            alt_tasks = {}
            alt_inputs = {}

            if len(schedules) > 1:
                thick_inp = inputs.copy(); thick_inp['D_inner'] = schedules[1]['D_inner_mm']
                alt_inputs['thicker'] = thick_inp

            current_nd_idx = sorted_nds.index(nd)
            if current_nd_idx > 0:
                prev_nd = sorted_nds[current_nd_idx - 1]
                prev_schedules = sorted(grouped_pipes[prev_nd], key=lambda x: x['t_mm'])
                thin_inp = inputs.copy(); thin_inp['D_inner'] = prev_schedules[0]['D_inner_mm']
                alt_inputs['thinner'] = thin_inp

            if not optimize_weight and len(valid_candidates) > 1:
                lightest_tuple = min(valid_candidates, key=lambda x: x[0]['weight_per_m'])
                lightest = lightest_tuple[0]
                if lightest['nominal'] != selected_pipe['nominal'] or lightest['schedule'] != selected_pipe['schedule']:
                    light_inp = inputs.copy(); light_inp['D_inner'] = lightest['D_inner_mm']
                    alt_inputs['lowest_weight'] = light_inp

            # Alternatifleri ThreadPoolExecutor ile paralel çalıştır
            with ThreadPoolExecutor(max_workers=min(len(alt_inputs), 3)) as executor:
                futures = {key: executor.submit(run_alt_sim, inp) for key, inp in alt_inputs.items()}

            # Sonuçları topla
            thicker_cand = schedules[1] if len(schedules) > 1 else None
            if 'thicker' in futures and thicker_cand:
                res_thick = futures['thicker'].result()
                thicker_cand['weight_per_m'] = calculate_pipe_weight_api5l(thicker_cand['OD_mm'], thicker_cand['t_mm'])
                alternatives['thicker'] = {'pipe': thicker_cand, 'result': res_thick, 'note': 'Daha Kalın Etli (Aynı Çap)'}

            if current_nd_idx > 0 and 'thinner' in futures:
                prev_schedules = sorted(grouped_pipes[sorted_nds[current_nd_idx - 1]], key=lambda x: x['t_mm'])
                thinner_cand = prev_schedules[0]
                res_thin = futures['thinner'].result()
                thinner_cand['weight_per_m'] = calculate_pipe_weight_api5l(thinner_cand['OD_mm'], thinner_cand['t_mm'])
                alternatives['thinner'] = {'pipe': thinner_cand, 'result': res_thin, 'note': 'Bir Alt Çap (Hız Limiti Aşıldı)'}

            if 'lowest_weight' in futures:
                lightest_tuple = min(valid_candidates, key=lambda x: x[0]['weight_per_m'])
                lightest = lightest_tuple[0]
                res_light = futures['lowest_weight'].result()
                alternatives['lowest_weight'] = {'pipe': lightest, 'result': res_light, 'note': 'En Düşük Ağırlıklı Boru'}
        
        if selected_pipe is None:
             # Hiçbiri uymadı, en büyüğü al
            if sorted_nds:
                last_nd = sorted_nds[-1]
                selected_pipe = grouped_pipes[last_nd][0]
                sim_inputs = inputs.copy(); sim_inputs['D_inner'] = selected_pipe['D_inner_mm']
                final_result = self.calculate_pressure_drop(sim_inputs, num_segments=20)
                final_result['velocity_status'] = "Hız Limiti Aşıldı"
            else:
                return {"error": "Uygun boru standardı bulunamadı."}

        # Sonuçları birleştir
        result = {
            "gas_props_in": gas_props_in,
            "gas_props_out": final_result.get("gas_props_out", gas_props_in),
            "m_dot": m_dot,
            "flow_rate_actual": flow_rate_actual_in, 
            "D_min_inner_mm": D_min_inner_mm, 
            "selected_pipe": selected_pipe,
            "P_design": P_design,
            "max_vel": max_vel,
            "velocity_selected": final_result['velocity_out'],
            "velocity_in": final_result['velocity_in'],
            "velocity_out": final_result['velocity_out'],
            "velocity_status": final_result['velocity_status'],
            "P_out": final_result['P_out'],
            "profile_data": final_result['profile_data'],
            "alternatives": alternatives,
            "phase_info": final_result.get('phase_info'),
            "flow_mode": flow_mode,
        }
        
        return result

    def get_sorted_pipes(self, P_design_pa, SMYS_mpa, F, E, T):
        SMYS = SMYS_mpa * 1e6  # MPa -> Pa
        all_pipes = []
        for nominal, data in ASME_B36_10M_DATA.items():
            OD = data["OD_mm"]
            t_required = (P_design_pa * (OD / 1000)) / (2 * SMYS * F * E * T) * 1000
            for schedule, t in data["schedules"].items():
                D_inner = OD - 2 * t
                if t >= t_required:
                    all_pipes.append({
                        "nominal": nominal, "OD_mm": OD, "schedule": schedule, "t_mm": t,
                        "D_inner_mm": D_inner, "t_required_mm": t_required
                    })
        
        # Sıralama
        def sort_key(pipe):
            return pipe['D_inner_mm'] # İç çapa göre sırala
        all_pipes.sort(key=sort_key)
        return all_pipes

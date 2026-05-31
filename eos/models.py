import math
import CoolProp.CoolProp as CP
from data import COOLPROP_GASES
from constants import R_J_MOL_K, STD_PRESSURE_PA, STD_TEMP_K, G_PER_MOL_TO_KG_PER_MOL, BAR_TO_PA
from thermo.utils import cp_propssi, cp_abstract_state, get_pure_component_props, calculate_standard_density, ideal_gas_sonic_velocity
from flow.utils import lee_gonzalez_eakin_viscosity
from eos.solver import solve_cubic


def calculate_cubic_eos_props(P, T, mole_fractions, EOS_type, log_callback=None, normalize_fn=None):
    if log_callback:
        log_callback(f"Hesaplama: {EOS_type} modeli kullaniliyor.")
    A_c, B_c = (0.45724, 0.07780) if EOS_type == "PR" else (0.42748, 0.08664)
    kappa_coeffs = (0.37464, 1.54226, -0.26992) if EOS_type == "PR" else (0.48, 1.574, -0.176)

    components = []
    for gas, y in mole_fractions.items():
        props = get_pure_component_props(gas)
        Tr = T / props["Tc"]
        kappa = kappa_coeffs[0] + kappa_coeffs[1] * props["omega"] + kappa_coeffs[2] * props["omega"] ** 2
        alpha = (1.0 + kappa * (1.0 - math.sqrt(Tr))) ** 2
        a_i = A_c * (alpha * (R_J_MOL_K ** 2) * (props["Tc"] ** 2)) / props["Pc"]
        b_i = B_c * (R_J_MOL_K * props["Tc"]) / props["Pc"]
        components.append({
            "gas": gas, "y": y, "Tc": props["Tc"], "Pc": props["Pc"],
            "MW": props["MW"], "a_i": a_i, "b_i": b_i, "omega": props["omega"],
        })

    a_mix = 0.0
    b_mix = 0.0
    n = len(components)
    for i in range(n):
        b_mix += components[i]["y"] * components[i]["b_i"]
        for j in range(n):
            a_mix += components[i]["y"] * components[j]["y"] * math.sqrt(components[i]["a_i"] * components[j]["a_i"])

    A = a_mix * P / (R_J_MOL_K ** 2 * T ** 2)
    B = b_mix * P / (R_J_MOL_K * T)
    a2 = B - 1
    a1 = A - 3 * B ** 2 - 2 * B
    a0 = -A * B + B ** 2 + B ** 3
    roots = solve_cubic(a2, a1, a0)
    Z = max(roots)
    if Z <= 0:
        raise ValueError(
            f"{EOS_type} modelinde P={P / BAR_TO_PA:.1f} bara, T={T:.1f} K noktasinda gercek kok bulunamadi."
        )

    MW_mix = sum(c["y"] * c["MW"] for c in components)
    density = (P * MW_mix * G_PER_MOL_TO_KG_PER_MOL) / (Z * R_J_MOL_K * T)
    standard_density = calculate_standard_density(MW_mix)
    viscosity = lee_gonzalez_eakin_viscosity(T, density, MW_mix)

    Cp_mix = 0.0
    Cv_mix = 0.0
    for c in components:
        try:
            gas_id = COOLPROP_GASES.get(c["gas"], {}).get("id", c["gas"])
            cp_i = cp_propssi("CP0MASS", "T", T, "P", STD_PRESSURE_PA, gas_id) / 1000
            cv_i = cp_propssi("CV0MASS", "T", T, "P", STD_PRESSURE_PA, gas_id) / 1000
        except Exception:
            cp_i = 2.0
            cv_i = 1.6
        Cp_mix += c["y"] * cp_i
        Cv_mix += c["y"] * cv_i

    gamma = Cp_mix / Cv_mix if Cv_mix > 0 else 1.3
    sonic_velocity = ideal_gas_sonic_velocity(gamma, Z, T, MW_mix)

    return {
        "MW": MW_mix, "Cp": Cp_mix, "Cv": Cv_mix, "Z": Z,
        "density": density, "viscosity": viscosity,
        "standard_density": standard_density,
        "viscosity_fallback": True, "thermo_fallback": True,
        "sonic_velocity": sonic_velocity,
    }

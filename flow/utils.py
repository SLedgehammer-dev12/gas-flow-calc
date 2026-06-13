import math
from constants import R_J_MOL_K, STD_PRESSURE_PA, STD_TEMP_K

# Phase labels
PHASE_LABEL_GAS = "Tek Fazli Gaz"
PHASE_LABEL_LIQUID = "Tek Fazli Sivi"
PHASE_LABEL_TWO_PHASE = "Iki Fazli (Gaz + Sivi Karisimi)"
PHASE_LABEL_SUPERCRITICAL = "Superkritik"
PHASE_LABEL_UNKNOWN = "Belirsiz"

# Formula labels
FORMULA_LABEL_LM = "Lockhart-Martinelli Iki Fazli Korelasyon"
FORMULA_LABEL_DW_CHURCHILL = "Darcy-Weisbach + Churchill f + Ivmelenme Duzeltmesi"
FORMULA_LABEL_DW_INCOMPRESSIBLE = "Darcy-Weisbach (Sabit Yogunluk)"
FORMULA_LABEL_DW_COMPRESSIBLE = "Darcy-Weisbach (Sikistirilabilir Gaz)"

# Phase warning messages
WARN_LIQUID_DETECTED = (
    "Sivi faz tespit edildi. Darcy-Weisbach, Churchill surtunme faktoru ve "
    "yogunluk degisimine bagli ivmelenme duzeltmesi kullanildi. "
    "Kot farki girdisi olmadigi icin yercekimi terimi hesaba dahil edilmedi."
)
WARN_CRYOGENIC_RISK = (
    "Kriyojenik bolgede sivi/kati riski var ({component_text}). "
    "CoolProp PT flash bu bolgede kararsiz olabilir; sonuc yaklasiktir."
)
WARN_TWO_PHASE = "Iki fazli bolge tespit edildi. Faz-ozgul basinc kaybi korelasyonu henuz devrede degil."
WARN_TWO_PHASE_ENVELOPE = (
    "CoolProp PT flash dogrudan cozulmedi; faz zarfi kullanilarak iki fazli bolge tespit edildi."
)
WARN_LOW_TEMP_SOLID = (
    "Bazi bilesenler uclu nokta sicakliginin altinda ({component_text}); "
    "kati faz riski nedeniyle CoolProp faz flash'i desteklenmedi."
)
WARN_PT_NOT_SOLVED = (
    "CoolProp faz flash'i bu PT noktasinda cozulmedi. "
    "Faz zarfi disi veya metastabil bolge nedeniyle sonuc tek-faz varsayimiyla yorumlanmalidir."
)
WARN_PHASE_UNKNOWN = "Faz belirlenemedi. Hesap tek faz varsayimlariyla yorumlanmalidir."


def churchill_friction_factor(Re, relative_roughness, log_callback=None):
    if Re <= 0:
        if log_callback:
            log_callback(f"Churchill: Gecersiz Reynolds sayisi ({Re}).", level="WARNING")
        return 0.02
    if Re < 2000:
        return 64.0 / Re
    A = (2.457 * math.log(1.0 / ((7.0 / Re) ** 0.9 + 0.27 * relative_roughness))) ** 16
    B = (37530.0 / Re) ** 16
    f_churchill = 8.0 * ((8.0 / Re) ** 12.0 + 1.0 / (A + B) ** 1.5) ** (1.0 / 12.0)
    return f_churchill


def lee_gonzalez_eakin_viscosity(T, density_kg_m3, MW_kg_kmol):
    from constants import MICROPOISE_TO_PA_S
    if density_kg_m3 <= 0:
        return 1e-6
    T_R = T * 1.8
    rho_gcc = density_kg_m3 / 1000.0
    X = 3.5 + 986.0 / T_R + 0.01 * MW_kg_kmol
    Y = max(0.1, 2.4 - 0.2 * X)
    K = ((9.4 + 0.02 * MW_kg_kmol) * T_R ** 1.5) / (209.0 + 19.0 * MW_kg_kmol + T_R)
    viscosity_micropoise = K * math.exp(X * (rho_gcc ** Y))
    return viscosity_micropoise * MICROPOISE_TO_PA_S


def single_phase_segment_loss(
    mass_flow, density, viscosity, dL, D_m, area,
    relative_roughness, K_seg, log_callback=None,
):
    velocity = mass_flow / (density * area) if density > 0 else 0.0
    if density <= 0 and log_callback:
        log_callback("_single_phase_segment_loss: Yogunluk <= 0, segment atlaniyor.", level="WARNING")
    if velocity <= 0 or viscosity <= 0:
        return {
            "dp_total": 0.0, "dp_friction": 0.0, "dp_fitting": 0.0,
            "dp_acceleration": 0.0, "velocity": velocity, "Re": 0.0, "f": 0.0,
        }
    Re = (density * velocity * D_m) / viscosity
    f = churchill_friction_factor(Re, relative_roughness, log_callback)
    dp_friction = f * (dL / D_m) * (density * velocity ** 2) / 2
    dp_fitting = K_seg * (density * velocity ** 2) / 2
    return {
        "dp_total": dp_friction + dp_fitting,
        "dp_friction": dp_friction,
        "dp_fitting": dp_fitting,
        "dp_acceleration": 0.0,
        "velocity": velocity, "Re": Re, "f": f,
    }


def liquid_acceleration_loss(mass_flow, area, density_in, density_out):
    if area <= 0 or density_in <= 0 or density_out <= 0:
        return 0.0
    mass_flux = mass_flow / area
    return mass_flux * mass_flux * ((1.0 / density_out) - (1.0 / density_in))


def two_phase_segment_loss(
    m_dot, dL, D_m, area, relative_roughness, K_seg, split_props, log_callback=None,
):
    quality_mass = min(max(split_props["quality_mass"], 1e-6), 1.0 - 1e-6)

    liquid_loss = single_phase_segment_loss(
        m_dot * (1.0 - quality_mass),
        split_props["rho_liquid"], split_props["mu_liquid"],
        dL, D_m, area, relative_roughness, K_seg, log_callback,
    )
    vapor_loss = single_phase_segment_loss(
        m_dot * quality_mass,
        split_props["rho_vapor"], split_props["mu_vapor"],
        dL, D_m, area, relative_roughness, K_seg, log_callback,
    )

    dp_liquid = max(liquid_loss["dp_total"], 1e-9)
    dp_vapor = max(vapor_loss["dp_total"], 1e-9)
    X = math.sqrt(dp_liquid / dp_vapor)

    ReL = liquid_loss["Re"]
    ReV = vapor_loss["Re"]
    lam_L = ReL < 2000
    lam_V = ReV < 2000
    if lam_L and lam_V:
        C = 5
    elif lam_L and not lam_V:
        C = 12
    elif not lam_L and lam_V:
        C = 10
    else:
        C = 20

    phi_l_sq = 1.0 + C / max(X, 1e-6) + 1.0 / max(X * X, 1e-6)
    dp_total = phi_l_sq * dp_liquid

    bulk_density = 1.0 / (
        quality_mass / split_props["rho_vapor"]
        + (1.0 - quality_mass) / split_props["rho_liquid"]
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


# --- API RP 14E Erosion Velocity ---
EROSION_C_FACTORS = {
    "ASTM A312 TP316L": 180.0,
    "ASTM A312 TP304L": 180.0,
    "API 5L Grade B": 122.0,
    "API 5L Grade X42": 122.0,
    "API 5L Grade X52": 122.0,
    "API 5L Grade X60": 122.0,
    "API 5L Grade X65": 122.0,
    "API 5L Grade X70": 122.0,
    "API 5L Grade X80": 122.0,
}


def erosion_velocity_c_metric(material):
    return EROSION_C_FACTORS.get(material, 122.0)


def compute_erosion_limit(density_kg_m3, material):
    C = erosion_velocity_c_metric(material)
    if density_kg_m3 <= 0:
        return float("inf")
    return C / math.sqrt(density_kg_m3)


# --- Empirical Gas Flow Models (Weymouth, Panhandle A, Panhandle B) ---
def weymouth_flow_rate(P_in_pa, P_out_pa, D_m, L, T_K, MW_kg_kmol, Z_avg):
    if L <= 0 or D_m <= 0:
        return 0.0
    base = (P_in_pa ** 2 - P_out_pa ** 2) * (D_m ** (16.0 / 3.0))
    denom = L * T_K * Z_avg * MW_kg_kmol
    if denom <= 0:
        return 0.0
    C_w = 0.0183  # Weymouth constant (metric)
    q_scmh = C_w * math.sqrt(base / denom)
    return q_scmh * STD_PRESSURE_PA * MW_kg_kmol / (R_J_MOL_K * STD_TEMP_K) / 3600.0


def panhandle_a_flow_rate(P_in_pa, P_out_pa, D_m, L, T_K, MW_kg_kmol, Z_avg, efficiency=0.92):
    if L <= 0 or D_m <= 0:
        return 0.0
    exponent = 1.0 / 1.0788  # n = 0.5394 → 1/n ≈ 1.8539
    base = (P_in_pa ** 2 - P_out_pa ** 2) * (D_m ** 2.6182)
    denom = (L * efficiency) ** 0.5394 * Z_avg ** 0.5394 * T_K ** 0.5394 * MW_kg_kmol ** 0.4606
    if denom <= 0:
        return 0.0
    C_pa = 0.1432  # Panhandle A constant (metric)
    q_scmh = C_pa * (base / denom) ** exponent
    return q_scmh * STD_PRESSURE_PA * MW_kg_kmol / (R_J_MOL_K * STD_TEMP_K) / 3600.0


def panhandle_b_flow_rate(P_in_pa, P_out_pa, D_m, L, T_K, MW_kg_kmol, Z_avg, efficiency=0.95):
    if L <= 0 or D_m <= 0:
        return 0.0
    base = (P_in_pa ** 2 - P_out_pa ** 2) * (D_m ** 2.53)
    denom = (L * efficiency) ** 0.51 * Z_avg ** 0.51 * T_K ** 0.51 * MW_kg_kmol ** 0.49
    if denom <= 0:
        return 0.0
    C_pb = 0.1986  # Panhandle B constant (metric)
    q_scmh = C_pb * (base / denom) ** (1.0 / 0.51)
    return q_scmh * STD_PRESSURE_PA * MW_kg_kmol / (R_J_MOL_K * STD_TEMP_K) / 3600.0


def compute_empirical_pressure_drop(P_in_pa, P_out_pa, D_m, L, T_K, MW_kg_kmol, Z_avg, m_dot):
    def solve_p_out(flow_fn):
        if L <= 0 or D_m <= 0:
            return P_out_pa, 0.0
        P_low = 1e5
        P_high = P_in_pa
        for _ in range(30):
            P_mid = (P_low + P_high) / 2.0
            q = flow_fn(P_in_pa, P_mid, D_m, L, T_K, MW_kg_kmol, Z_avg)
            if q > m_dot:
                P_low = P_mid
            else:
                P_high = P_mid
        return (P_low + P_high) / 2.0, abs(P_in_pa - (P_low + P_high) / 2.0)

    P_wey, dp_wey = solve_p_out(weymouth_flow_rate)
    P_pa, dp_pa = solve_p_out(panhandle_a_flow_rate)
    P_pb, dp_pb = solve_p_out(panhandle_b_flow_rate)
    return {
        "weymouth": {"P_out": P_wey, "delta_p": dp_wey},
        "panhandle_a": {"P_out": P_pa, "delta_p": dp_pa},
        "panhandle_b": {"P_out": P_pb, "delta_p": dp_pb},
    }

import math

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
    A = (2.457 * math.log(1.0 / ((7.0 / Re) ** 0.9 + 0.27 * relative_roughness))) ** 16
    B = (37530.0 / Re) ** 16
    f_churchill = 8.0 * ((8.0 / Re) ** 12.0 + 1.0 / (A + B) ** 1.5) ** (1.0 / 12.0)
    return f_churchill


def lee_gonzalez_eakin_viscosity(T, density_kg_m3, MW_kg_kmol):
    from constants import MICROPOISE_TO_PA_S
    T_R = T * 1.8
    rho_gcc = density_kg_m3 / 1000.0
    X = 3.5 + 986.0 / T_R + 0.01 * MW_kg_kmol
    Y = 2.4 - 0.2 * X
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

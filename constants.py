import math

# Physical constants
R_J_MOL_K = 8.314462618
STD_PRESSURE_PA = 101325.0
STD_TEMP_K = 288.15
MIN_PRESSURE_PA = 1000.0

# Unit conversions
BAR_TO_PA = 1e5
MPA_TO_PA = 1e6
KPA_TO_PA = 1000.0
PSI_TO_PA = 6894.76
ATM_PRESSURE_BAR = 1.01325
ATM_PRESSURE_PSI = 14.696
CELSIUS_TO_KELVIN = 273.15
SM3H_TO_M3S = 3600.0
G_PER_MOL_TO_KG_PER_MOL = 1e-3
KG_PER_MOL_TO_G_PER_MOL = 1000.0
KELVIN_TO_RANKINE = 1.8
KG_M3_TO_G_PER_CC = 1e-3
MICROPOISE_TO_PA_S = 1e-7
MM_TO_M = 1e-3


def convert_pressure_to_pa(value, unit):
    unit_str = str(unit).strip().casefold()
    if unit_str in ("barg",):
        return (value + ATM_PRESSURE_BAR) * BAR_TO_PA
    elif unit_str in ("bara", "bar"):
        return value * BAR_TO_PA
    elif unit_str in ("psig",):
        return (value + ATM_PRESSURE_PSI) * PSI_TO_PA
    elif unit_str in ("psia", "psi"):
        return value * PSI_TO_PA
    elif unit_str in ("mpa",):
        return value * MPA_TO_PA
    elif unit_str in ("kpa",):
        return value * KPA_TO_PA
    elif unit_str in ("pa",):
        return value
    return value


def convert_temperature_to_k(value, unit):
    unit_str = str(unit).strip()
    if unit_str in ("°C", "C"):
        return value + CELSIUS_TO_KELVIN
    elif unit_str in ("°F", "F"):
        return (value - 32.0) * 5.0 / 9.0 + CELSIUS_TO_KELVIN
    elif unit_str in ("K",):
        return value
    return value

# Friction / convergence defaults
FRICTION_INIT_GUESS = 0.02
FRICTION_CONVERGENCE = 1e-6
FRICTION_SQRT_MIN = 1e-10
BINARY_SEARCH_ITER = 40
DAK_NR_MAX_ITER = 50
DAK_RHO_R_CONVERGENCE = 1e-8

# Thread pool
THREAD_POOL_MAX_WORKERS = 3
FUTURE_TIMEOUT_SEC = 30

# Cache
THERMO_CACHE_MAXSIZE = 1000

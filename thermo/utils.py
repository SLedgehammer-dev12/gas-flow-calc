import math
import CoolProp.CoolProp as CP

from constants import (
    R_J_MOL_K, STD_PRESSURE_PA, STD_TEMP_K, G_PER_MOL_TO_KG_PER_MOL,
    BAR_TO_PA, CELSIUS_TO_KELVIN,
)
from data import COOLPROP_GASES
from flow.utils import lee_gonzalez_eakin_viscosity


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


def build_gas_name_lookup(coolprop_gases):
    lookup = {}
    for gas_key, gas_props in coolprop_gases.items():
        canonical_name = gas_props["id"]
        lookup[gas_key.casefold()] = canonical_name
        lookup[canonical_name.casefold()] = canonical_name
        lookup[gas_props["name"].casefold()] = canonical_name
    return lookup


def normalize_gas_name(gas, lookup):
    key = str(gas).strip().casefold()
    canonical = lookup.get(key)
    if canonical is None:
        unicode_sub_map = str.maketrans(
            "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089",
            "0123456789",
        )
        key = key.translate(unicode_sub_map)
        for k, v in lookup.items():
            if k.translate(unicode_sub_map) == key:
                return v
    if canonical is None:
        raise ValueError(f"Desteklenmeyen gaz tanimi: {gas}")
    return canonical


def get_pure_component_props(gas_id):
    try:
        props = {
            "Tc": cp_propssi("Tcrit", gas_id),
            "Pc": cp_propssi("Pcrit", gas_id),
            "omega": cp_propssi("ACENTRIC", gas_id),
            "MW": cp_propssi("M", gas_id) * 1000,
        }
        return props
    except Exception as e:
        raise ValueError(
            f"CoolProp hatasi ({gas_id}): Kritik ozellikler alinamadi. {str(e)}"
        ) from e


def calculate_standard_density(MW_mix):
    return (STD_PRESSURE_PA * MW_mix * G_PER_MOL_TO_KG_PER_MOL) / (
        1.0 * R_J_MOL_K * STD_TEMP_K
    )


def ideal_gas_sonic_velocity(gamma, Z, T, MW_mix):
    return math.sqrt(gamma * Z * R_J_MOL_K * T / (MW_mix * G_PER_MOL_TO_KG_PER_MOL))

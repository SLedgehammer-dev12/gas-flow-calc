FLOW_MODE_COMPRESSIBLE = "compressible"
FLOW_MODE_INCOMPRESSIBLE = "incompressible"

_FLOW_MODE_ALIASES = {
    FLOW_MODE_COMPRESSIBLE: FLOW_MODE_COMPRESSIBLE,
    FLOW_MODE_INCOMPRESSIBLE: FLOW_MODE_INCOMPRESSIBLE,
    "compressible": FLOW_MODE_COMPRESSIBLE,
    "incompressible": FLOW_MODE_INCOMPRESSIBLE,
    "sıkıştırılabilir": FLOW_MODE_COMPRESSIBLE,
    "sıkıştırılamaz": FLOW_MODE_INCOMPRESSIBLE,
    "sÄ±kÄ±ÅŸtÄ±rÄ±labilir": FLOW_MODE_COMPRESSIBLE,
    "sÄ±kÄ±ÅŸtÄ±rÄ±lamaz": FLOW_MODE_INCOMPRESSIBLE,
}


def normalize_flow_mode(value, default=FLOW_MODE_COMPRESSIBLE):
    key = str(value or "").strip().casefold()
    return _FLOW_MODE_ALIASES.get(key, default)


def is_compressible_flow(value):
    return normalize_flow_mode(value) == FLOW_MODE_COMPRESSIBLE


def is_incompressible_flow(value):
    return normalize_flow_mode(value) == FLOW_MODE_INCOMPRESSIBLE


def get_flow_mode_label(mode, compressible_label, incompressible_label):
    if normalize_flow_mode(mode) == FLOW_MODE_INCOMPRESSIBLE:
        return incompressible_label
    return compressible_label

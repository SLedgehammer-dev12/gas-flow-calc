TARGET_PRESSURE_DROP = "pressure_drop"
TARGET_MAX_LENGTH = "max_length"
TARGET_MIN_DIAMETER = "min_diameter"

_TARGET_ALIASES = {
    TARGET_PRESSURE_DROP: TARGET_PRESSURE_DROP,
    TARGET_MAX_LENGTH: TARGET_MAX_LENGTH,
    TARGET_MIN_DIAMETER: TARGET_MIN_DIAMETER,
    "çıkış basıncı": TARGET_PRESSURE_DROP,
    "cikis basinci": TARGET_PRESSURE_DROP,
    "outlet pressure": TARGET_PRESSURE_DROP,
    "maksimum uzunluk": TARGET_MAX_LENGTH,
    "maximum length": TARGET_MAX_LENGTH,
    "minimum çap": TARGET_MIN_DIAMETER,
    "minimum cap": TARGET_MIN_DIAMETER,
    "minimum diameter": TARGET_MIN_DIAMETER,
}


def normalize_calc_target(value, default=TARGET_MIN_DIAMETER):
    key = str(value or "").strip().casefold()
    return _TARGET_ALIASES.get(key, default)


def get_calc_target_label(mode, pressure_drop_label, max_length_label, min_diameter_label):
    normalized = normalize_calc_target(mode)
    if normalized == TARGET_PRESSURE_DROP:
        return pressure_drop_label
    if normalized == TARGET_MAX_LENGTH:
        return max_length_label
    return min_diameter_label

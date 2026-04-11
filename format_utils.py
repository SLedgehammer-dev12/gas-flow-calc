def _normalize_scalar(value):
    if hasattr(value, "item") and callable(getattr(value, "item")):
        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.decode("latin-1", errors="replace")

    return value


def safe_text(value, default="-"):
    value = _normalize_scalar(value)
    if value is None:
        return default
    return str(value)


def safe_number(value, default=None):
    value = _normalize_scalar(value)
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_format(value, spec, default="-"):
    value = _normalize_scalar(value)
    if value is None:
        return default

    try:
        return format(value, spec)
    except (TypeError, ValueError):
        try:
            return format(float(value), spec)
        except (TypeError, ValueError):
            return safe_text(value, default=default)

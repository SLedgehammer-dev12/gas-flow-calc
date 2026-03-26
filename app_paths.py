import json
import os
import sys


APP_DIR_NAME = "Gas Flow Calc V6.1"


def get_install_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_app_data_dir():
    base_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or get_install_dir()
    path = os.path.join(base_dir, APP_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def get_config_path():
    return os.path.join(get_app_data_dir(), "config.json")


def get_legacy_config_path():
    return os.path.join(get_install_dir(), "config.json")


def get_session_file_path():
    return os.path.join(get_app_data_dir(), ".lang_change_session.json")


def load_config(defaults=None):
    config = dict(defaults or {})
    config_path = get_config_path()
    candidates = [config_path, get_legacy_config_path()]
    seen = set()

    for candidate in candidates:
        normalized = os.path.normcase(os.path.abspath(candidate))
        if normalized in seen or not os.path.exists(candidate):
            continue
        seen.add(normalized)

        try:
            with open(candidate, "r", encoding="utf-8-sig") as f:
                loaded = json.load(f)
        except Exception:
            continue

        if not isinstance(loaded, dict):
            continue

        config.update(loaded)

        if normalized != os.path.normcase(os.path.abspath(config_path)):
            try:
                save_config(config)
            except Exception:
                pass

        return config

    return config


def save_config(config):
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return config_path

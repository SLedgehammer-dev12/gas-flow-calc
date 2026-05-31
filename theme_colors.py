"""Centralized theme color palette helper.
Provides a single source of truth for theme colors across all UI modules.
Use instead of duplicating palette dicts in schematic.py, graphs.py, widgets.py.
"""

from theme_manager import THEMES


def get_theme_colors(theme_name="light"):
    return THEMES.get(theme_name, THEMES["light"])


def get_color(theme_name, key, default="#000000"):
    palette = get_theme_colors(theme_name)
    return palette.get(key, default)


def resolve_colors(theme_name, card_key="card", text_key="txt_dark"):
    palette = get_theme_colors(theme_name)
    return {
        "card_bg": palette.get(card_key, "#ffffff"),
        "card_fg": palette.get(text_key, "#1c2032"),
        "accent": palette.get("accent", "#1a237e"),
        "accent_light": palette.get("accent_light", "#e8eaf6"),
        "success": palette.get("success", "#2e7d32"),
        "warn": palette.get("warn", "#e65100"),
        "err": palette.get("err", "#c62828"),
        "bg": palette.get("bg", "#f0f3f8"),
        "txt_dark": palette.get("txt_dark", "#1c2032"),
        "txt_mid": palette.get("txt_mid", "#455a64"),
        "txt_light": palette.get("txt_light", "#78909c"),
    }

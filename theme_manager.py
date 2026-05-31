import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from app_paths import load_config, save_config

FONT_FAMILY = "Segoe UI"


def initialize_font_family(root=None):
    global FONT_FAMILY
    try:
        available = tkfont.families(root)
        candidates = ["Outfit", "Inter", "SF Pro Text", "Helvetica Neue", "Segoe UI", "Arial"]
        for c in candidates:
            if c in available:
                FONT_FAMILY = c
                break
    except Exception:
        pass


THEMES = {
    "light": {
        "bg": "#f0f3f8",
        "card": "#ffffff",
        "accent": "#1a237e",
        "accent2": "#283593",
        "accent_light": "#e8eaf6",
        "txt_dark": "#1c2032",
        "txt_mid": "#455a64",
        "txt_light": "#78909c",
        "success": "#2e7d32",
        "warn": "#e65100",
        "err": "#c62828",
        "entry_bg": "white",
        "entry_fg": "black"
    },
    "dark": {
        "bg": "#121214",
        "card": "#1e1e24",
        "accent": "#8c9eff",
        "accent2": "#b388ff",
        "accent_light": "#2c2c38",
        "txt_dark": "#e2e2e9",
        "txt_mid": "#a5a5b2",
        "txt_light": "#707080",
        "success": "#81c784",
        "warn": "#ffb74d",
        "err": "#e57373",
        "entry_bg": "#1e1e24",
        "entry_fg": "#e2e2e9"
    },
    "contrast": {
        "bg": "#000000",
        "card": "#000000",
        "accent": "#ffff00",
        "accent2": "#00ffff",
        "accent_light": "#333333",
        "txt_dark": "#ffffff",
        "txt_mid": "#ffffff",
        "txt_light": "#dddddd",
        "success": "#00ff00",
        "warn": "#ffaa00",
        "err": "#ff0000",
        "entry_bg": "#000000",
        "entry_fg": "#ffffff"
    }
}


class ThemeManager:
    def __init__(self, app):
        self.app = app

    @property
    def current_theme(self):
        return self.app.current_theme

    @current_theme.setter
    def current_theme(self, value):
        self.app.current_theme = value

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        theme_colors = THEMES.get(self.current_theme, THEMES["light"])
        BG          = theme_colors["bg"]
        CARD        = theme_colors["card"]
        ACCENT      = theme_colors["accent"]
        ACCENT2     = theme_colors["accent2"]
        ACCENT_LIGHT= theme_colors["accent_light"]
        TXT_DARK    = theme_colors["txt_dark"]
        TXT_MID     = theme_colors["txt_mid"]
        TXT_LIGHT   = theme_colors["txt_light"]
        SUCCESS     = theme_colors["success"]
        WARN        = theme_colors["warn"]
        ERR         = theme_colors["err"]

        style.configure(".",
                        background=BG,
                        foreground=TXT_DARK,
                        font=(FONT_FAMILY, 10),
                        focuscolor=ACCENT2)

        style.configure("TFrame",  background=BG)
        style.configure("Card.TFrame", background=CARD, relief="flat")

        style.configure("TLabelframe",
                        background=CARD,
                        relief="flat",
                        borderwidth=1,
                        bordercolor=ACCENT_LIGHT if self.current_theme != "light" else "#dee2e6")
        style.configure("TLabelframe.Label",
                        background=CARD,
                        foreground=ACCENT,
                        font=(FONT_FAMILY, 10, "bold"))
        style.configure("Bold.TLabelframe.Label",
                        background=CARD,
                        foreground=ACCENT,
                        font=(FONT_FAMILY, 10, "bold"))

        style.configure("TNotebook",
                        background=BG,
                        tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab",
                        background=ACCENT_LIGHT if self.current_theme != "light" else "#d1d8e6",
                        foreground=TXT_MID,
                        padding=[10, 5],
                        font=(FONT_FAMILY, 9))
        style.map("TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", ACCENT)],
                  font=[("selected", (FONT_FAMILY, 9, "bold"))])

        style.configure("TButton",
                        font=(FONT_FAMILY, 10),
                        padding=[8, 5],
                        background=ACCENT_LIGHT if self.current_theme != "light" else "#dde3ef",
                        foreground=TXT_DARK,
                        relief="flat")
        style.map("TButton",
                  background=[("active", ACCENT), ("pressed", ACCENT2)],
                  foreground=[("active", "#ffffff")])

        style.configure("SegBtn.TButton",
                        font=(FONT_FAMILY, 9),
                        padding=[8, 4],
                        background=ACCENT_LIGHT if self.current_theme != "light" else "#dde3ef",
                        foreground=TXT_MID,
                        relief="flat")
        style.map("SegBtn.TButton",
                  background=[("active", ACCENT_LIGHT)])

        style.configure("SegBtnActive.TButton",
                        font=(FONT_FAMILY, 9, "bold"),
                        padding=[8, 4],
                        background=ACCENT,
                        foreground="#ffffff",
                        relief="flat")
        style.map("SegBtnActive.TButton",
                  background=[("active", ACCENT2)])

        style.configure("TLabel",    background=CARD, foreground=TXT_DARK, font=(FONT_FAMILY, 10))
        style.configure("Header.TLabel",
                        font=(FONT_FAMILY, 14, "bold"),
                        foreground=ACCENT,
                        background=CARD)
        style.configure("Sub.TLabel",
                        font=(FONT_FAMILY, 9),
                        foreground=TXT_LIGHT,
                        background=CARD)
        style.configure("Hint.TLabel",
                        font=(FONT_FAMILY, 9, "italic"),
                        foreground=TXT_LIGHT,
                        background=CARD)

        style.configure("Treeview",
                        font=(FONT_FAMILY, 9),
                        rowheight=26,
                        background=CARD,
                        fieldbackground=CARD,
                        foreground=TXT_DARK)
        style.configure("Treeview.Heading",
                        font=(FONT_FAMILY, 9, "bold"),
                        background=ACCENT_LIGHT,
                        foreground=ACCENT)
        style.map("Treeview",
                  background=[("selected", ACCENT_LIGHT)],
                  foreground=[("selected", ACCENT)])

        style.configure("TEntry",
                        padding=[4, 3],
                        relief="flat",
                        foreground=TXT_DARK,
                        fieldbackground=CARD)
        style.map("TEntry",
                  fieldbackground=[("focus", ACCENT_LIGHT)])

        style.configure("TCombobox", padding=[4, 3], relief="flat", background=CARD, fieldbackground=CARD, foreground=TXT_DARK)

        style.configure("TScrollbar", background=ACCENT_LIGHT, troughcolor=BG, relief="flat")
        style.map("TScrollbar", background=[("active", ACCENT)])

        self.app.root.configure(bg=BG)

        self.app._colors = theme_colors
        self.app.root._colors = theme_colors

    def change_theme(self, theme_name):
        if theme_name not in THEMES:
            return

        self.current_theme = theme_name
        self.app.root.current_theme = theme_name

        try:
            cfg = load_config()
            cfg["theme"] = theme_name
            save_config(cfg)
        except Exception as e:
            self.app.log_message(f"Tema ayari kaydedilemedi: {e}", level="WARNING")

        self.setup_styles()
        self.app.refresh_schematic()

        if hasattr(self.app, 'charts_container') and getattr(self.app, 'last_result', None):
            from ui.graphs import show_graphs
            show_graphs(self.app.charts_container, self.app.last_result, app=self.app)

        self.app.log_message(f"Tema '{theme_name}' olarak degistirildi.", level="INFO")

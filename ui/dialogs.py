import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from translations import t


def _show_scrolled_dialog(parent, title_key, content_key, geometry="700x600"):
    window = tk.Toplevel(parent)
    window.title(t(title_key))
    window.geometry(geometry)
    window.resizable(True, True)

    try:
        window.iconbitmap(parent.iconbitmap())
    except Exception:
        pass

    font_family = getattr(parent, "font_family", "Segoe UI")
    title_frame = ttk.Frame(window)
    title_frame.pack(fill="x", padx=15, pady=(15, 5))
    ttk.Label(title_frame, text=t(title_key), font=(font_family, 14, "bold")).pack(anchor="w")

    content_frame = ttk.Frame(window)
    content_frame.pack(fill="both", expand=True, padx=15, pady=10)

    text_widget = ScrolledText(content_frame, wrap="word", font=("Consolas", 10),
                               padx=10, pady=10, bg="#fafafa")
    text_widget.pack(fill="both", expand=True)
    text_widget.insert("1.0", t(content_key))
    text_widget.config(state="disabled")

    btn_frame = ttk.Frame(window)
    btn_frame.pack(fill="x", padx=15, pady=(5, 15))
    ttk.Button(btn_frame, text="OK", command=window.destroy, width=10).pack(side="right")

    window.transient(parent)
    window.grab_set()
    window.focus_set()


def show_about(parent, app_version):
    about_text = f"""{t("app_title")}

{t("msg_version")}: {app_version}

{t("about_description")}

© 2024"""
    messagebox.showinfo(t("about_title"), about_text)


def show_user_guide(parent):
    _show_scrolled_dialog(parent, "guide_title", "guide_content", "700x600")


def show_program_details(parent):
    _show_scrolled_dialog(parent, "program_details_title", "program_details_content", "800x700")

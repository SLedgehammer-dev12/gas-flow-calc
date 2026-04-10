import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from translations import t

def show_about(parent, app_version):
    """Hakkında dialogu."""
    about_text = f"""{t("app_title")}

{t("msg_version")}: {app_version}

{t("about_description")}

© 2024"""
    messagebox.showinfo(t("about_title"), about_text)

def show_user_guide(parent):
    """Kullanım kılavuzunu gösteren pencere."""
    guide_window = tk.Toplevel(parent)
    guide_window.title(t("guide_title"))
    guide_window.geometry("700x600")
    guide_window.resizable(True, True)
    
    try:
        guide_window.iconbitmap(parent.iconbitmap())
    except Exception:
        pass
    
    title_frame = ttk.Frame(guide_window)
    title_frame.pack(fill="x", padx=15, pady=(15, 5))
    ttk.Label(title_frame, text=t("guide_title"), font=("Segoe UI", 14, "bold")).pack(anchor="w")
    
    content_frame = ttk.Frame(guide_window)
    content_frame.pack(fill="both", expand=True, padx=15, pady=10)
    
    guide_text = ScrolledText(content_frame, wrap="word", font=("Consolas", 10), 
                               padx=10, pady=10, bg="#fafafa")
    guide_text.pack(fill="both", expand=True)
    guide_text.insert("1.0", t("guide_content"))
    guide_text.config(state="disabled")
    
    btn_frame = ttk.Frame(guide_window)
    btn_frame.pack(fill="x", padx=15, pady=(5, 15))
    ttk.Button(btn_frame, text="OK", command=guide_window.destroy, width=10).pack(side="right")
    
    guide_window.transient(parent)
    guide_window.grab_set()
    guide_window.focus_set()

def show_program_details(parent):
    """Program detayları ve referanslar penceresini göster."""
    details_window = tk.Toplevel(parent)
    details_window.title(t("program_details_title"))
    details_window.geometry("800x700")
    details_window.resizable(True, True)
    
    try:
        details_window.iconbitmap(parent.iconbitmap())
    except Exception:
        pass
    
    title_frame = ttk.Frame(details_window)
    title_frame.pack(fill="x", padx=15, pady=(15, 5))
    ttk.Label(title_frame, text=t("program_details_title"), font=("Segoe UI", 14, "bold")).pack(anchor="w")
    
    content_frame = ttk.Frame(details_window)
    content_frame.pack(fill="both", expand=True, padx=15, pady=10)
    
    details_text = ScrolledText(content_frame, wrap="word", font=("Consolas", 10), 
                                 padx=10, pady=10, bg="#fafafa")
    details_text.pack(fill="both", expand=True)
    details_text.insert("1.0", t("program_details_content"))
    details_text.config(state="disabled")
    
    btn_frame = ttk.Frame(details_window)
    btn_frame.pack(fill="x", padx=15, pady=(5, 15))
    ttk.Button(btn_frame, text="OK", command=details_window.destroy, width=10).pack(side="right")
    
    details_window.transient(parent)
    details_window.grab_set()
    details_window.focus_set()

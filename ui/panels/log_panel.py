import tkinter as tk
from tkinter import ttk
import time
from translations import t

class LogPanel(ttk.Frame):
    def __init__(self, parent, app_context, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_context
        self.widgets = {}
        self.setup_ui()

    def register(self, app):
        vars(app).update(self.widgets)

    def setup_ui(self):
        # Kontrol Paneli
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(ctrl_frame, text=t("log_filter")).pack(side="left")
        self.widgets['log_filter_var'] = tk.StringVar(value=t("log_all"))
        filter_combo = ttk.Combobox(ctrl_frame, textvariable=self.widgets['log_filter_var'], values=[t("log_all"), "INFO", "WARNING", "ERROR"], state="readonly", width=10)
        filter_combo.pack(side="left", padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.apply_log_filter)

        ttk.Button(ctrl_frame, text=t("btn_clear_logs"), command=self.clear_logs).pack(side="right")

        # Log Tablosu (Treeview)
        cols = ("time", "level", "message")
        self.widgets['log_tree'] = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")

        self.widgets['log_tree'].heading("time", text=t("log_time"))
        self.widgets['log_tree'].heading("level", text=t("log_level"))
        self.widgets['log_tree'].heading("message", text=t("log_message"))

        self.widgets['log_tree'].column("time", width=80, anchor="center")
        self.widgets['log_tree'].column("level", width=80, anchor="center")
        self.widgets['log_tree'].column("message", width=600, anchor="w")

        # Renkler (Tags)
        self.widgets['log_tree'].tag_configure("INFO", foreground="black")
        self.widgets['log_tree'].tag_configure("WARNING", foreground="#f57c00")
        self.widgets['log_tree'].tag_configure("ERROR", foreground="red")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.widgets['log_tree'].yview)
        self.widgets['log_tree'].configure(yscrollcommand=scrollbar.set)

        self.widgets['log_tree'].pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)
        scrollbar.pack(side="right", fill="y", padx=5, pady=5)

        self.widgets['all_logs'] = []

    # ── Log Panel Methods ──

    def apply_log_filter(self, event=None):
        from translations import t
        for item in self.app.log_tree.get_children():
            self.app.log_tree.delete(item)

        current_filter = self.app.log_filter_var.get()

        for entry in self.app.all_logs:
            if current_filter == t("log_all") or entry["level"] == current_filter:
                self.app.log_tree.insert("", "end", values=(entry["time"], entry["level"], entry["message"]), tags=(entry["level"],))

        self.app.log_tree.yview_moveto(1)

    def clear_logs(self):
        self.app.all_logs.clear()
        for item in self.app.log_tree.get_children():
            self.app.log_tree.delete(item)

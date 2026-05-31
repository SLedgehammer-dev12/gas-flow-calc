import tkinter as tk
from tkinter import ttk
from translations import t
from data import COOLPROP_GASES, GAS_PRESETS


class GasPanel(ttk.LabelFrame):
    def __init__(self, parent, app_context, **kwargs):
        super().__init__(parent,
                         text="⚗  " + t("section_gas_mixture"),
                         style="Bold.TLabelframe",
                         padding=(12, 8),
                         **kwargs)
        self.app = app_context
        self.widgets = {}
        self.setup_ui()

    def register(self, app):
        vars(app).update(self.widgets)

    def setup_ui(self):
        # ── Üst Kısım: Arama + Seçim + Ekle ─────────────────
        top = ttk.Frame(self)
        top.pack(fill="x")

        ttk.Label(top, text=t("gas_search")).pack(side="left")
        self.widgets['gas_search_var'] = tk.StringVar()
        self.widgets['gas_search_var'].trace_add("write", self.filter_gas_list)
        ttk.Entry(top, textvariable=self.widgets['gas_search_var'], width=16).pack(
            side="left", padx=5)

        self.widgets['gas_combo'] = ttk.Combobox(
            top,
            values=[g["name"] for g in COOLPROP_GASES.values()],
            width=22, state="readonly")
        self.widgets['gas_combo'].set(t("select_gas"))
        self.widgets['gas_combo'].pack(side="left", padx=5)

        ttk.Button(top, text="＋ " + t("btn_add_gas"),
                   command=self.add_gas_component).pack(side="left")

        # ── Preset Satırı ────────────────────────────────────
        preset = ttk.Frame(self)
        preset.pack(fill="x", pady=(5, 0))
        ttk.Label(preset, text=t("gas_preset")).pack(side="left")
        preset_names = [t("gas_preset_select")] + list(GAS_PRESETS.keys())
        self.widgets['gas_preset_combo'] = ttk.Combobox(
            preset, values=preset_names, width=18, state="readonly")
        self.widgets['gas_preset_combo'].set(t("gas_preset_select"))
        self.widgets['gas_preset_combo'].pack(side="left", padx=5)
        self.widgets['gas_preset_combo'].bind(
            "<<ComboboxSelected>>", self._on_preset_selected)

        # ── Bileşen Listesi (Canvas + Scrollbar) ─────────────
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="x", pady=(6, 0))

        self.widgets['gas_list_canvas'] = tk.Canvas(
            list_frame, height=168, highlightthickness=0,
            bg="#ffffff")
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical",
            command=self.widgets['gas_list_canvas'].yview)
        self.widgets['gas_list_inner'] = ttk.Frame(self.widgets['gas_list_canvas'])

        self.widgets['gas_list_inner'].bind(
            "<Configure>",
            lambda e: self.widgets['gas_list_canvas'].configure(
                scrollregion=self.widgets['gas_list_canvas'].bbox("all")))
        self.widgets['gas_list_canvas'].create_window(
            (0, 0), window=self.widgets['gas_list_inner'], anchor="nw")
        self.widgets['gas_list_canvas'].configure(
            yscrollcommand=scrollbar.set)

        self.widgets['gas_list_canvas'].pack(side="left", fill="x", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── Alt Bar: Bileşim Türü + Yüzde Progress Bar ───────
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(6, 0))

        ttk.Label(bottom, text=t("composition_type")).pack(side="left")
        self.widgets['comp_type'] = ttk.Combobox(
            bottom,
            values=[t("mol_percent"), t("mass_percent")],
            width=10, state="readonly")
        self.widgets['comp_type'].set(t("mol_percent"))
        self.widgets['comp_type'].pack(side="left", padx=5)

        ttk.Separator(bottom, orient="vertical").pack(
            side="left", fill="y", padx=8)

        ttk.Label(bottom, text=t("gas_total") + ":").pack(side="left")
        self.widgets['gas_total_label'] = tk.Label(
            bottom, text="0.00 %",
            font=(self.app.font_family, 10, "bold"),
            bg="#ffffff", fg="#78909c")
        self.widgets['gas_total_label'].pack(side="left", padx=(4, 2))

        self.widgets['gas_status_label'] = tk.Label(
            bottom, text="",
            font=(self.app.font_family, 10),
            bg="#ffffff", fg="#78909c")
        self.widgets['gas_status_label'].pack(side="left", padx=2)

        # Renkli doluluk çubuğu (toplam % görsel)
        bar_frame = tk.Frame(bottom, bg="#e0e0e0", height=8, width=80,
                             relief="flat")
        bar_frame.pack(side="left", padx=(8, 0), pady=4)
        bar_frame.pack_propagate(False)
        self.widgets['gas_total_bar'] = tk.Frame(bar_frame, bg="#43a047", height=8)
        self.widgets['gas_total_bar'].place(x=0, y=0, relheight=1.0, width=0)
        self.widgets['_gas_bar_frame'] = bar_frame

    # ── Gas Panel Methods ──

    def filter_gas_list(self, *args):
        search = self.app.gas_search_var.get().lower()
        filtered = [g["name"] for g in COOLPROP_GASES.values() if search in g["name"].lower()]
        self.app.gas_combo['values'] = filtered
        if filtered:
            self.app.gas_combo.current(0)

    def add_gas_component(self):
        from ui.widgets import ValidationHelper
        gas_name = self.app.gas_combo.get()
        if not gas_name or gas_name == t("select_gas"):
            return

        gas_id = next(k for k, v in COOLPROP_GASES.items() if v["name"] == gas_name)
        if gas_id in self.app.gas_components:
            return

        var = tk.StringVar(value="0")
        self.app.gas_components[gas_id] = var

        row_frame = ttk.Frame(self.app.gas_list_inner)
        row_frame.pack(fill="x", pady=2)
        ttk.Label(row_frame, text=gas_name, width=25).pack(side="left")

        entry = ttk.Entry(row_frame, textvariable=var, width=8)
        entry.pack(side="left", padx=5)

        entry.bind("<KeyRelease>", lambda e: self.update_gas_total())
        var.trace_add("write", lambda *args: self.update_gas_total())

        ttk.Button(row_frame, text="X", width=3, command=lambda: self.remove_gas(gas_id, row_frame)).pack(side="left")

        self.update_gas_total()

    def remove_gas(self, gas_id, widget):
        del self.app.gas_components[gas_id]
        widget.destroy()
        self.update_gas_total()

    def update_gas_total(self, *args):
        from ui.widgets import ValidationHelper
        total = 0.0
        for var in self.app.gas_components.values():
            try:
                val_str = var.get()
                normalized = ValidationHelper.normalize_number(val_str)
                if normalized:
                    val = float(normalized)
                    total += val
            except (ValueError, AttributeError, tk.TclError):
                pass

        self.app.gas_total_label.config(text=f"{total:.2f} %")

        try:
            bar_w = self.app.gas_total_bar.master.winfo_width()
            if bar_w > 2:
                fill_px = int(min(1.0, total / 100.0) * bar_w)
                self.app.gas_total_bar.place(x=0, y=0, relheight=1.0, width=fill_px)
                if abs(total - 100.0) <= 0.01:
                    self.app.gas_total_bar.config(bg="#2e7d32")
                elif total > 100:
                    self.app.gas_total_bar.config(bg="#c62828")
                else:
                    self.app.gas_total_bar.config(bg="#43a047")
        except Exception:
            pass

        tolerance = 0.01
        if abs(total - 100.0) <= tolerance:
            self.app.gas_total_label.config(fg="#2e7d32")
            self.app.gas_status_label.config(text="\u2713", fg="#2e7d32")
        elif total == 0:
            self.app.gas_total_label.config(fg="#666")
            self.app.gas_status_label.config(text="", fg="#666")
        else:
            diff = total - 100.0
            sign = "+" if diff > 0 else ""
            self.app.gas_total_label.config(fg="#e65100")
            self.app.gas_status_label.config(text=f"({sign}{diff:.2f}%)", fg="#e65100")

    def check_gas_composition(self):
        from tkinter import messagebox
        total = 0.0
        raw_values = {}

        for gas_id, var in self.app.gas_components.items():
            try:
                val = float(var.get())
            except (ValueError, tk.TclError):
                val = 0.0
            if val > 0:
                raw_values[gas_id] = val
                total += val

        if total <= 0:
            return (False, 0, {}, False, "Gaz bilesenleri toplami 0'dan buyuk olmalidir.")

        tolerance = 0.01

        if abs(total - 100.0) <= tolerance:
            normalized = {k: v / total for k, v in raw_values.items()}
            return (True, total, normalized, True, None)

        diff = total - 100.0
        sign = "+" if diff > 0 else ""

        msg = t("gas_composition_warning",
            f"\u26a0\ufe0f GAZ BILESIMI UYARISI\n\n"
            f"Girilen gaz bilesimi toplami: {total:.2f}%\n"
            f"Fark: {sign}{diff:.2f}%\n\n"
            f"Hesaplamaya devam etmek ister misiniz?\n\n"
            f"'Evet' secerseniz:\n"
            f"  \u2022 Bilesenler agirlikli ortalamalarina gore\n"
            f"    %100'e normalize edilecek.\n"
            f"  \u2022 Orijinal oranlar korunacak.\n\n"
            f"'Hayir' secerseniz:\n"
            f"  \u2022 Hesaplama iptal edilecek.\n"
            f"  \u2022 Degerleri manuel duzeltebilirsiniz."
        )

        user_choice = messagebox.askyesno(t("gas_composition_check_title", "Gaz Bilesimi Kontrolu"), msg, icon="warning")

        if user_choice:
            normalized = {k: v / total for k, v in raw_values.items()}
            return (False, total, normalized, True, None)
        else:
            return (False, total, {}, False, t("calc_cancelled_by_user", "Hesaplama kullanici tarafindan iptal edildi."))

    def _on_preset_selected(self, event=None):
        preset_name = self.app.gas_preset_combo.get()
        if preset_name == t("gas_preset_select") or preset_name not in GAS_PRESETS:
            return

        for widget in self.app.gas_list_inner.winfo_children():
            widget.destroy()
        self.app.gas_components.clear()

        preset = GAS_PRESETS[preset_name]
        for gas_id, percentage in preset.items():
            gas_name = COOLPROP_GASES.get(gas_id, {}).get("name", gas_id)
            var = tk.StringVar(value=str(percentage))
            self.app.gas_components[gas_id] = var

            row_frame = ttk.Frame(self.app.gas_list_inner)
            row_frame.pack(fill="x", pady=2)
            ttk.Label(row_frame, text=gas_name, width=25).pack(side="left")

            entry = ttk.Entry(row_frame, textvariable=var, width=8)
            entry.pack(side="left", padx=5)
            entry.bind("<KeyRelease>", lambda e: self.update_gas_total())
            var.trace_add("write", lambda *args: self.update_gas_total())

            ttk.Button(row_frame, text="X", width=3, command=lambda gid=gas_id, w=row_frame: self.remove_gas(gid, w)).pack(side="left")

        self.update_gas_total()

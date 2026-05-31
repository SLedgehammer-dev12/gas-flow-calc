import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from app_paths import get_session_file_path
from data import COOLPROP_GASES
from translations import t
from target_utils import TARGET_PRESSURE_DROP, TARGET_MIN_DIAMETER
from flow_utils import FLOW_MODE_INCOMPRESSIBLE


class StateManager:
    def __init__(self, app):
        self.app = app

    def setup_default_state(self):
        self.app.calc_target.set(TARGET_MIN_DIAMETER)

        defaults = {
            "METHANE": "98.0",
            "ETHANE": "1.0",
            "NITROGEN": "0.5",
            "CARBONDIOXIDE": "0.5"
        }

        for gas_id, value in defaults.items():
            self.app.gas_combo.set(COOLPROP_GASES[gas_id]["name"])
            self.app.add_gas_component()
            self.app.gas_components[gas_id].set(value)

        self.app.gas_combo.set(t("select_gas"))
        self.app.update_gas_total()

    def save_project(self):
        try:
            data = self.get_ui_state()
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                messagebox.showinfo(t("dialog_success"), t("project_saved"))
        except Exception as e:
            messagebox.showerror(t("dialog_error"), f"{t('save_error')}: {str(e)}")

    def load_project(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
            if path:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.set_ui_state(data)
                messagebox.showinfo(t("dialog_success"), t("project_loaded"))
        except Exception as e:
            messagebox.showerror(t("dialog_error"), f"{t('load_error')}: {str(e)}")

    def get_ui_state(self):
        gas_data = {gas_id: var.get() for gas_id, var in self.app.gas_components.items()}
        fitting_data = {name: var.get() for name, var in self.app.fitting_counts.items()}

        return {
            "gas_components": gas_data,
            "comp_type": self.app.comp_type.get(),
            "p_in": self.app.p_in_var.get(), "p_unit": self.app.p_unit.get(),
            "t_val": self.app.t_var.get(), "t_unit": self.app.t_unit.get(),
            "flow_val": self.app.flow_var.get(), "flow_unit": self.app.flow_unit.get(),
            "calc_target": self.app.calc_target.get(),
            "thermo_model": self.app.thermo_model.get(),
            "flow_type": self.app.flow_type.get(),
            "material": self.app.material_combo.get(),
            "opt_weight": self.app.opt_weight_var.get(),
            "fast_calc": self.app.fast_calc_var.get(),
            "len_val": self.app.len_var.get(),
            "diam_val": self.app.diam_var.get(),
            "thick_val": self.app.thick_var.get(),
            "nps_val": self.app.nps_combo.get(),
            "schedule_val": self.app.schedule_combo.get(),
            "smys_val": self.app.smys_var.get(),
            "target_p_val": self.app.target_p_var.get(), "target_p_unit": self.app.target_p_unit.get(),
            "max_vel_val": self.app.max_vel_var.get(),
            "p_design_val": self.app.p_design_var.get(), "p_design_unit": self.app.p_design_unit.get(),
            "factor_f": self.app.factor_f.get(), "factor_e": self.app.factor_e.get(), "factor_t": self.app.factor_t.get(),
            "fitting_counts": fitting_data,
            "ball_valve_kv": self.app.ball_valve_kv.get()
        }

    def set_ui_state(self, data):
        for widget in self.app.gas_list_inner.winfo_children():
            widget.destroy()
        self.app.gas_components.clear()

        for gas_id, val in data.get("gas_components", {}).items():
            var = tk.StringVar(value=str(val))
            self.app.gas_components[gas_id] = var

            gas_name = next((v for k, v in COOLPROP_GASES.items() if k == gas_id), gas_id)

            row_frame = ttk.Frame(self.app.gas_list_inner)
            row_frame.pack(fill="x", pady=2)
            ttk.Label(row_frame, text=gas_name, width=25).pack(side="left")

            entry = ttk.Entry(row_frame, textvariable=var, width=8)
            entry.pack(side="left", padx=5)
            entry.bind("<KeyRelease>", lambda e: self.app.update_gas_total())
            var.trace_add("write", lambda *args: self.app.update_gas_total())

            ttk.Button(row_frame, text="X", width=3, command=lambda gid=gas_id, w=row_frame: self.app.remove_gas(gid, w)).pack(side="left")

        self.app.update_gas_total()

        self.app.comp_type.set(data.get("comp_type", "Mol %"))
        self.app.p_in_var.set(data.get("p_in", 0))
        self.app.p_unit.set(data.get("p_unit", "Barg"))
        self.app.t_var.set(data.get("t_val", 25))
        self.app.t_unit.set(data.get("t_unit", "°C"))
        self.app.flow_var.set(data.get("flow_val", 0))
        self.app.flow_unit.set(data.get("flow_unit", "Sm³/h"))
        self.app.calc_target.set(data.get("calc_target", TARGET_PRESSURE_DROP))
        self.app.thermo_model.set(data.get("thermo_model", "CoolProp (High Accuracy EOS)"))
        self.app.flow_type.set(data.get("flow_type", FLOW_MODE_INCOMPRESSIBLE))
        self.app.material_combo.set(data.get("material", "API 5L Grade B"))
        self.app._on_material_changed()
        if "smys_val" in data:
            self.app.smys_var.set(data["smys_val"])
        nps_val = data.get("nps_val", "")
        if nps_val:
            self.app.nps_combo.set(nps_val)
            self.app._on_nps_changed()
            schedule_val = data.get("schedule_val", "")
            if schedule_val:
                self.app.schedule_combo.set(schedule_val)
        self.app.len_var.set(data.get("len_val", 100))
        self.app.diam_var.set(data.get("diam_val", 0))
        self.app.thick_var.set(data.get("thick_val", 0))
        self.app.target_p_var.set(data.get("target_p_val", 0))
        self.app.target_p_unit.set(data.get("target_p_unit", "Barg"))
        self.app.max_vel_var.set(data.get("max_vel_val", 20))
        self.app.p_design_var.set(data.get("p_design_val", 0))
        self.app.p_design_unit.set(data.get("p_design_unit", "Barg"))
        self.app.factor_f.set(data.get("factor_f", 0.72))
        self.app.factor_e.set(data.get("factor_e", 1.0))
        self.app.factor_t.set(data.get("factor_t", 1.0))
        self.app.ball_valve_kv.set(data.get("ball_valve_kv", 0))

        fit_data = data.get("fitting_counts", {})
        for name, val in fit_data.items():
            if name in self.app.fitting_counts:
                self.app.fitting_counts[name].set(val)

        self.app.update_ui_visibility()

    def _get_session_file_path(self):
        return get_session_file_path()

    def _save_session_for_lang_change(self):
        try:
            session_data = self.get_ui_state()
            session_path = self._get_session_file_path()
            with open(session_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.app.log_message(f"Oturum kaydetme hatasi: {e}", level="WARNING")

    def _restore_session_after_lang_change(self):
        session_path = self._get_session_file_path()
        if not os.path.exists(session_path):
            return
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            self.set_ui_state(session_data)
            os.remove(session_path)
            self.app.log_message(t("msg_program_started") + " - " + "Session restored after language change.", level="INFO")
        except Exception as e:
            self.app.log_message(f"Oturum geri yukleme hatasi: {e}", level="WARNING")
            try:
                os.remove(session_path)
            except OSError:
                pass

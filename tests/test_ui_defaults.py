import tkinter as tk
import unittest

import main
from main import GasFlowCalculatorApp
from translations import t


class TestUIDefaults(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = GasFlowCalculatorApp(self.root)
        self.root.update_idletasks()

    def tearDown(self):
        for after_id in self.root.tk.call("after", "info"):
            try:
                self.root.after_cancel(after_id)
            except tk.TclError:
                pass
        self.root.destroy()

    def test_default_calc_target_and_button_style_are_in_sync(self):
        expected_target = t("target_min_diameter")
        self.assertEqual(self.app.calc_target.get(), expected_target)

        for target, button in self.app._seg_buttons.items():
            expected_style = "SegBtnActive.TButton" if target == expected_target else "SegBtn.TButton"
            self.assertEqual(str(button.cget("style")), expected_style)

    def test_gas_list_shows_at_least_six_rows(self):
        self.assertGreaterEqual(int(self.app.gas_list_canvas.cget("height")), 160)

    def test_theme_switch_updates_theme_state(self):
        self.app.apply_theme("dark", persist=False)
        self.assertEqual(self.app.ui_theme.get(), "dark")
        self.assertEqual(self.app._colors["bg"], "#16202a")

    def test_min_diameter_mode_only_keeps_required_inputs_active(self):
        self.assertEqual(str(self.app.ent_max_vel.cget("state")), "normal")
        self.assertEqual(str(self.app.ent_target_p.cget("state")), "disabled")
        self.assertEqual(str(self.app.nps_combo.cget("state")), "disabled")
        self.assertEqual(str(self.app.schedule_combo.cget("state")), "disabled")
        self.assertEqual(str(self.app.ent_diam.cget("state")), "disabled")
        self.assertEqual(str(self.app.ent_thick.cget("state")), "disabled")
        self.assertEqual(str(self.app.ent_p_design.cget("state")), "normal")
        self.assertEqual(str(self.app.p_design_unit.cget("state")), "readonly")
        self.assertEqual(str(self.app.ent_len.cget("state")), "normal")

        self.app.flow_type.set(t("flow_incompressible"))
        self.app.update_ui_visibility()

        self.assertEqual(str(self.app.ent_len.cget("state")), "disabled")

    def test_pressure_drop_mode_enables_length_and_geometry_inputs(self):
        self.app.calc_target.set(t("target_pressure_drop"))
        self.app.update_ui_visibility()

        self.assertEqual(str(self.app.ent_len.cget("state")), "normal")
        self.assertEqual(str(self.app.ent_target_p.cget("state")), "disabled")
        self.assertEqual(str(self.app.ent_max_vel.cget("state")), "disabled")
        self.assertEqual(str(self.app.nps_combo.cget("state")), "readonly")
        self.assertEqual(str(self.app.schedule_combo.cget("state")), "readonly")
        self.assertEqual(str(self.app.ent_diam.cget("state")), "normal")
        self.assertEqual(str(self.app.ent_thick.cget("state")), "normal")
        self.assertEqual(str(self.app.ent_p_design.cget("state")), "disabled")

    def test_max_length_mode_enables_target_pressure_and_geometry_inputs(self):
        self.app.calc_target.set(t("target_max_length"))
        self.app.update_ui_visibility()

        self.assertEqual(str(self.app.ent_len.cget("state")), "disabled")
        self.assertEqual(str(self.app.ent_target_p.cget("state")), "normal")
        self.assertEqual(str(self.app.target_p_unit.cget("state")), "readonly")
        self.assertEqual(str(self.app.ent_max_vel.cget("state")), "disabled")
        self.assertEqual(str(self.app.nps_combo.cget("state")), "readonly")
        self.assertEqual(str(self.app.schedule_combo.cget("state")), "readonly")
        self.assertEqual(str(self.app.ent_diam.cget("state")), "normal")
        self.assertEqual(str(self.app.ent_thick.cget("state")), "normal")

    def test_startup_update_check_prompts_download_when_update_exists(self):
        calls = {"download": 0}

        self.app._startup_update_check_done = False
        self.app.updater.private_repo = False
        self.app.updater.github_token = ""
        self.app.updater.check_for_update = lambda current_version: {
            "has_update": True,
            "latest_version": "9.9.9",
            "body": "test release",
        }
        self.app.download_latest_release = lambda: calls.__setitem__("download", calls["download"] + 1)

        original_askyesno = main.messagebox.askyesno
        try:
            main.messagebox.askyesno = lambda *args, **kwargs: True
            self.app.silent_update_check()
            self.root.update()
        finally:
            main.messagebox.askyesno = original_askyesno

        self.assertEqual(calls["download"], 1)

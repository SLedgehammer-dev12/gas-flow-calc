import tkinter as tk
import unittest
import sys

from flow_utils import FLOW_MODE_COMPRESSIBLE
from target_utils import TARGET_PRESSURE_DROP, TARGET_MAX_LENGTH, TARGET_MIN_DIAMETER
from translations import t


class TestUIDefaults(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            raise unittest.SkipTest("Tk not available")
        self.app = __import__("main").GasFlowCalculatorApp(self.root)
        self.root.update_idletasks()

    def tearDown(self):
        for after_id in self.root.tk.call("after", "info"):
            try:
                self.root.after_cancel(after_id)
            except (tk.TclError, RuntimeError):
                pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_default_calc_target_and_button_style_are_in_sync(self):
        expected_target = TARGET_MIN_DIAMETER
        self.assertEqual(self.app.calc_target.get(), expected_target)

        for target, button in self.app._seg_buttons.items():
            expected_style = "SegBtnActive.TButton" if target == expected_target else "SegBtn.TButton"
            self.assertEqual(str(button.cget("style")), expected_style)

    def test_gas_list_shows_at_least_six_rows(self):
        self.assertGreaterEqual(int(self.app.gas_list_canvas.cget("height")), 160)

    def test_target_mode_hides_and_shows_widgets_via_grid(self):
        self.app.calc_target.set(TARGET_MIN_DIAMETER)
        self.app.update_ui_visibility()
        self.root.update_idletasks()
        self.assertTrue(self.app.ent_max_vel.grid_info())

        self.app.calc_target.set(TARGET_PRESSURE_DROP)
        self.app.update_ui_visibility()
        self.root.update_idletasks()
        self.assertTrue(self.app.ent_len.grid_info())
        self.assertFalse(self.app.ent_target_p.grid_info())

        self.app.calc_target.set(TARGET_MAX_LENGTH)
        self.app.update_ui_visibility()
        self.root.update_idletasks()
        self.assertTrue(self.app.ent_target_p.grid_info())

    def test_min_diameter_mode_toggles_design_frame(self):
        self.app.calc_target.set(TARGET_MIN_DIAMETER)
        self.app.update_ui_visibility()
        self.root.update_idletasks()
        info = self.app.design_frame.pack_info()
        self.assertIn("fill", info)

        self.app.calc_target.set(TARGET_PRESSURE_DROP)
        self.app.update_ui_visibility()
        self.root.update_idletasks()
        with self.assertRaises(tk.TclError):
            self.app.design_frame.pack_info()

    def test_min_diameter_compressible_shows_length(self):
        self.app.calc_target.set(TARGET_MIN_DIAMETER)
        from calculations import normalize_flow_mode
        self.app.flow_type.set(t("flow_compressible"))
        self.app.update_ui_visibility()
        self.root.update_idletasks()
        self.assertTrue(self.app.ent_len.grid_info())

    def test_silent_update_check_does_not_crash_when_disabled(self):
        self.app._startup_update_check_done = False
        self.app.updater.private_repo = False
        self.app.updater.github_token = ""
        self.app.updater.check_for_update = lambda current_version: {
            "has_update": False,
            "latest_version": "0.0.0",
        }
        try:
            self.app.silent_update_check()
        except Exception as e:
            self.fail(f"silent_update_check raised {e}")

    def test_min_diameter_mode_disables_pipe_fields(self):
        self.app.calc_target.set(TARGET_MIN_DIAMETER)
        self.app.update_ui_visibility()
        self.root.update_idletasks()
        
        self.assertEqual(str(self.app.nps_combo.cget("state")), "disabled")
        self.assertEqual(str(self.app.schedule_combo.cget("state")), "disabled")
        self.assertEqual(str(self.app.ent_diam.cget("state")), "disabled")
        self.assertEqual(str(self.app.ent_thick.cget("state")), "disabled")

        self.app.calc_target.set(TARGET_PRESSURE_DROP)
        self.app.update_ui_visibility()
        self.root.update_idletasks()

        self.assertEqual(str(self.app.nps_combo.cget("state")), "readonly")
        self.assertEqual(str(self.app.schedule_combo.cget("state")), "readonly")

    def test_min_diameter_result_synchronization(self):
        import queue
        self.app.calc_target.set(TARGET_MIN_DIAMETER)
        self.app.update_ui_visibility()
        self.root.update_idletasks()

        result = {
            "selected_pipe": {
                "nominal": "4",
                "schedule": "40",
                "OD_mm": 114.3,
                "t_mm": 6.02,
                "D_inner_mm": 102.26,
                "t_required_mm": 3.2,
            },
            "max_vel": 20.0,
            "velocity_in": 12.5,
            "velocity_out": 14.2,
            "P_out": 15e5,
            "velocity_status": "Uygun",
            "alternatives": {}
        }
        mock_data = {
            "result": result,
            "report": "MOCK REPORT CONTENT"
        }
        
        self.app.calc_queue.put(("SUCCESS", mock_data))
        self.app.check_calc_queue()
        
        self.assertEqual(self.app.nps_combo.get(), "4")
        self.assertEqual(self.app.schedule_combo.get(), "40")
        self.assertEqual(self.app.diam_var.get(), 114.3)
        self.assertEqual(self.app.thick_var.get(), 6.02)
        
        self.assertEqual(str(self.app.nps_combo.cget("state")), "disabled")
        self.assertEqual(str(self.app.schedule_combo.cget("state")), "disabled")
        self.assertEqual(str(self.app.ent_diam.cget("state")), "disabled")
        self.assertEqual(str(self.app.ent_thick.cget("state")), "disabled")

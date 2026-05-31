import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock
from target_utils import TARGET_PRESSURE_DROP, TARGET_MIN_DIAMETER
from flow_utils import FLOW_MODE_INCOMPRESSIBLE


class MockApp:
    """Minimal mock app with the attributes state_manager needs."""
    def __init__(self):
        from tkinter import StringVar, IntVar, DoubleVar, BooleanVar, Tk
        self.root = Tk()
        self.root.withdraw()
        self.font_family = "Segoe UI"

        self.gas_components = {}
        self.fitting_counts = {}
        self.gas_list_inner = MagicMock()
        self.gas_list_inner.winfo_children = MagicMock(return_value=[])

        def _make_var(vtype, default):
            v = vtype(master=self.root, value=default)
            return v

        self.calc_target = _make_var(StringVar, TARGET_MIN_DIAMETER)
        self.p_in_var = _make_var(DoubleVar, 20.0)
        self.p_unit = _make_var(StringVar, "Barg")
        self.t_var = _make_var(DoubleVar, 25.0)
        self.t_unit = _make_var(StringVar, "°C")
        self.flow_var = _make_var(DoubleVar, 5000.0)
        self.flow_unit = _make_var(StringVar, "Sm\u00b3/h")
        self.thermo_model = _make_var(StringVar, "CoolProp (High Accuracy EOS)")
        self.flow_type = _make_var(StringVar, FLOW_MODE_INCOMPRESSIBLE)
        self.material_combo = _make_var(StringVar, "API 5L Grade B")
        self.opt_weight_var = _make_var(BooleanVar, False)
        self.fast_calc_var = _make_var(BooleanVar, True)
        self.len_var = _make_var(DoubleVar, 100.0)
        self.diam_var = _make_var(DoubleVar, 0.0)
        self.thick_var = _make_var(DoubleVar, 0.0)
        self.nps_combo = _make_var(StringVar, "")
        self.schedule_combo = _make_var(StringVar, "")
        self.smys_var = _make_var(DoubleVar, 0.0)
        self.target_p_var = _make_var(DoubleVar, 0.0)
        self.target_p_unit = _make_var(StringVar, "Barg")
        self.max_vel_var = _make_var(DoubleVar, 20.0)
        self.p_design_var = _make_var(DoubleVar, 0.0)
        self.p_design_unit = _make_var(StringVar, "Barg")
        self.factor_f = _make_var(DoubleVar, 0.72)
        self.factor_e = _make_var(DoubleVar, 1.0)
        self.factor_t = _make_var(DoubleVar, 1.0)
        self.ball_valve_kv = _make_var(DoubleVar, 0.0)
        self.comp_type = _make_var(StringVar, "Mol %")
        self.gas_combo = MagicMock()
        self.gas_combo.set = MagicMock()
        self._log_messages = []

        self.fitting_counts = {}

    def add_gas_component(self):
        pass

    def update_gas_total(self, *args):
        pass

    def update_ui_visibility(self):
        pass

    def remove_gas(self, gid, w):
        pass

    def log_message(self, msg, level="INFO"):
        self._log_messages.append((level, msg))

    def _on_material_changed(self):
        pass

    def _on_nps_changed(self):
        pass

    def destroy(self):
        self.root.destroy()


class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.app = MockApp()
        from state_manager import StateManager
        self.sm = StateManager(self.app)

    def tearDown(self):
        self.app.destroy()

    def test_initial_calc_target_is_min_diameter(self):
        self.assertEqual(self.app.calc_target.get(), TARGET_MIN_DIAMETER)

    def test_get_ui_state_returns_dict(self):
        state = self.sm.get_ui_state()
        self.assertIsInstance(state, dict)
        self.assertIn("gas_components", state)
        self.assertIn("p_in", state)
        self.assertIn("p_unit", state)
        self.assertIn("t_val", state)
        self.assertIn("flow_val", state)
        self.assertIn("calc_target", state)
        self.assertIn("flow_type", state)
        self.assertIn("material", state)
        self.assertIn("fitting_counts", state)
        self.assertIn("ball_valve_kv", state)

    def test_get_ui_state_values_match_vars(self):
        self.app.p_in_var.set(42.5)
        self.app.flow_var.set(10000)
        self.app.calc_target.set(TARGET_PRESSURE_DROP)
        state = self.sm.get_ui_state()
        self.assertEqual(state["p_in"], 42.5)
        self.assertEqual(state["flow_val"], 10000)
        self.assertEqual(state["calc_target"], TARGET_PRESSURE_DROP)

    def test_set_ui_state_restores_values(self):
        data = {
            "gas_components": {"METHANE": "95.0", "ETHANE": "5.0"},
            "comp_type": "Mol %",
            "p_in": 30.0, "p_unit": "Barg",
            "t_val": 50.0, "t_unit": "°C",
            "flow_val": 8000, "flow_unit": "Sm\u00b3/h",
            "calc_target": TARGET_PRESSURE_DROP,
            "thermo_model": "CoolProp (High Accuracy EOS)",
            "flow_type": FLOW_MODE_INCOMPRESSIBLE,
            "material": "API 5L Grade B",
            "opt_weight": False,
            "fast_calc": True,
            "len_val": 200.0,
            "diam_val": 150.0,
            "thick_val": 5.0,
            "nps_val": "6",
            "schedule_val": "40",
            "smys_val": 450.0,
            "target_p_val": 10.0, "target_p_unit": "Barg",
            "max_vel_val": 25.0,
            "p_design_val": 50.0, "p_design_unit": "Barg",
            "factor_f": 0.6, "factor_e": 0.8, "factor_t": 0.9,
            "fitting_counts": {},
            "ball_valve_kv": 0.0,
        }
        self.sm.set_ui_state(data)
        self.assertEqual(self.app.p_in_var.get(), 30.0)
        self.assertEqual(self.app.t_var.get(), 50.0)
        self.assertEqual(self.app.flow_var.get(), 8000)
        self.assertEqual(self.app.flow_unit.get(), "Sm\u00b3/h")
        self.assertEqual(self.app.calc_target.get(), TARGET_PRESSURE_DROP)
        self.assertEqual(self.app.len_var.get(), 200.0)
        self.assertEqual(self.app.diam_var.get(), 150.0)
        self.assertEqual(self.app.thick_var.get(), 5.0)
        self.assertEqual(self.app.max_vel_var.get(), 25.0)
        self.assertEqual(self.app.factor_f.get(), 0.6)
        self.assertEqual(self.app.factor_e.get(), 0.8)
        self.assertEqual(self.app.factor_t.get(), 0.9)

    def test_ui_state_round_trip(self):
        self.app.p_in_var.set(55.0)
        self.app.flow_var.set(20000)
        self.app.len_var.set(500.0)
        state1 = self.sm.get_ui_state()
        self.sm.set_ui_state(state1)
        state2 = self.sm.get_ui_state()
        self.assertEqual(state1["p_in"], state2["p_in"])
        self.assertEqual(state1["flow_val"], state2["flow_val"])
        self.assertEqual(state1["len_val"], state2["len_val"])

    def test_session_save_restore_round_trip(self):
        self.app.p_in_var.set(60.0)
        session_dir = tempfile.mkdtemp()
        try:
            from app_paths import get_session_file_path
            original_get_path = get_session_file_path
            with unittest.mock.patch("app_paths.get_session_file_path") as mock_path:
                session_file = os.path.join(session_dir, "session.json")
                mock_path.return_value = session_file
                self.sm._save_session_for_lang_change()
                self.assertTrue(os.path.exists(session_file))
                with open(session_file, "r") as f:
                    data = json.load(f)
                self.assertEqual(data["p_in"], 60.0)
        finally:
            import shutil
            shutil.rmtree(session_dir, ignore_errors=True)

    def test_default_setup_creates_gas_components(self):
        from data import COOLPROP_GASES
        old_components = dict(self.app.gas_components)
        self.app.gas_components.clear()

        real_gas_combo = MagicMock()
        gas_names = [v["name"] for v in COOLPROP_GASES.values()]
        real_gas_combo.set = MagicMock()
        real_gas_combo.current = MagicMock(return_value=0)
        self.app.gas_combo = real_gas_combo
        self.app.add_gas_component = lambda gid=None: self.app.gas_components.update(
            {gas_id: MagicMock() for gas_id in ["METHANE", "ETHANE", "NITROGEN", "CARBONDIOXIDE"]}
        )

        self.sm.setup_default_state()
        self.assertGreater(len(self.app.gas_components), 0)

    def test_session_save_restore_round_trip(self):
        self.app.p_in_var.set(60.0)
        import tempfile
        session_dir = tempfile.mkdtemp()
        try:
            import state_manager
            session_file = os.path.join(session_dir, "session.json")
            with unittest.mock.patch.object(state_manager, "get_session_file_path", return_value=session_file):
                self.sm._save_session_for_lang_change()
                self.assertTrue(os.path.exists(session_file), f"Session file not created at {session_file}")
                with open(session_file, "r") as f:
                    data = json.load(f)
                self.assertEqual(data["p_in"], 60.0)
        finally:
            import shutil
            shutil.rmtree(session_dir, ignore_errors=True)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from controllers import GasFlowController
from target_utils import TARGET_PRESSURE_DROP, TARGET_MAX_LENGTH, TARGET_MIN_DIAMETER


class TestGasFlowController(unittest.TestCase):
    def setUp(self):
        self.controller = GasFlowController()

    def _base_ui_state(self, **overrides):
        state = {
            "gas_components": {"METHANE": 0.92, "ETHANE": 0.05, "PROPANE": 0.03},
            "comp_type": "Mol %",
            "p_in": 20, "p_unit": "Barg",
            "t_val": 25, "t_unit": "°C",
            "flow_val": 5000, "flow_unit": "Sm3/h",
            "calc_target": TARGET_PRESSURE_DROP,
            "thermo_model": "CoolProp (High Accuracy EOS)",
            "flow_type": "Sıkıştırılabilir",
            "material": "API 5L Grade B",
            "opt_weight": False,
            "fast_calc": False,
            "len_val": 5000,
            "diam_val": 100,
            "thick_val": 5,
            "smys_val": 241,
            "target_p_val": 10, "target_p_unit": "Barg",
            "max_vel_val": 20,
            "p_design_val": 50, "p_design_unit": "Barg",
            "factor_f": 0.72, "factor_e": 1.0, "factor_t": 1.0,
            "fitting_counts": {},
        }
        state.update(overrides)
        return state

    def test_parse_float_returns_value(self):
        self.assertEqual(self.controller._parse_float(42), 42.0)
        self.assertEqual(self.controller._parse_float("3.14"), 3.14)
        self.assertEqual(self.controller._parse_float(None), 0.0)
        self.assertEqual(self.controller._parse_float("abc"), 0.0)

    def test_parse_int_returns_value(self):
        self.assertEqual(self.controller._parse_int(7), 7)
        self.assertEqual(self.controller._parse_int("7"), 7)
        self.assertEqual(self.controller._parse_int(None), 0)

    def test_prepare_inputs_pressure_drop_valid(self):
        state = self._base_ui_state()
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNone(errors)
        self.assertIsNotNone(inputs)
        self.assertGreater(inputs["P_in"], 0)
        self.assertEqual(inputs["target"], TARGET_PRESSURE_DROP)
        self.assertIn("mole_fractions", inputs)
        self.assertGreater(len(inputs["mole_fractions"]), 0)

    def test_prepare_inputs_returns_errors_for_empty_gas(self):
        state = self._base_ui_state(gas_components={})
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNotNone(errors)
        self.assertIsNone(inputs)
        self.assertGreater(len(errors), 0)

    def test_prepare_inputs_returns_errors_for_negative_pressure(self):
        state = self._base_ui_state(p_in=-5)
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNotNone(errors)
        self.assertIsNone(inputs)

    def test_prepare_inputs_returns_errors_for_zero_flow(self):
        state = self._base_ui_state(flow_val=0)
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNotNone(errors)
        self.assertIsNone(inputs)

    def test_prepare_inputs_max_length_target(self):
        state = self._base_ui_state(calc_target=TARGET_MAX_LENGTH)
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNone(errors)
        self.assertEqual(inputs["target"], TARGET_MAX_LENGTH)

    def test_prepare_inputs_min_diameter_target(self):
        state = self._base_ui_state(calc_target=TARGET_MIN_DIAMETER)
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNone(errors)
        self.assertEqual(inputs["target"], TARGET_MIN_DIAMETER)
        self.assertEqual(inputs["max_velocity"], 20)
        self.assertGreater(inputs["P_design"], 0)

    def test_prepare_inputs_max_length_missing_target_pressure(self):
        state = self._base_ui_state(calc_target=TARGET_MAX_LENGTH, target_p_val=0)
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNotNone(errors)
        self.assertIsNone(inputs)

    def test_prepare_inputs_min_diameter_negative_max_vel(self):
        state = self._base_ui_state(calc_target=TARGET_MIN_DIAMETER, max_vel_val=-1)
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNotNone(errors)
        self.assertIsNone(inputs)

    def test_prepare_inputs_with_mole_fractions_override(self):
        state = self._base_ui_state()
        override = {"METHANE": 1.0}
        inputs, errors = self.controller.prepare_inputs(state, mole_fractions_override=override)
        self.assertIsNone(errors)
        self.assertIn("METHANE", inputs["mole_fractions"])

    def test_prepare_inputs_with_fittings(self):
        state = self._base_ui_state(
            fitting_counts={"90° Dirsek": 4, "Gate Valf": 2}
        )
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNone(errors)
        self.assertGreater(inputs["total_k"], 0)

    def test_get_results_table_data_pressure_drop(self):
        result = {
            "P_out": 18e5, "delta_p_total": 3e5,
            "velocity_in": 15.0, "velocity_out": 17.0,
        }
        state = self._base_ui_state()
        rows = self.controller.get_results_table_data(result, TARGET_PRESSURE_DROP, state)
        self.assertGreater(len(rows), 0)

    def test_get_results_table_data_max_length_error(self):
        result = {"error": "Test error message"}
        state = self._base_ui_state()
        rows = self.controller.get_results_table_data(result, TARGET_MAX_LENGTH, state)
        self.assertGreater(len(rows), 0)

    def test_get_results_table_data_max_length_success(self):
        result = {
            "L_max": 250.0,
            "Re": 120000,
            "f": 0.0185,
            "velocity_in": 12.5,
            "velocity_out": 14.2,
            "P_out": 15e5,
        }
        state = self._base_ui_state()
        rows = self.controller.get_results_table_data(result, TARGET_MAX_LENGTH, state)
        
        # Verify specific fields are in the result rows
        param_names = [row[0] for row in rows]
        self.assertIn("Maksimum Uzunluk", param_names)
        self.assertIn("Reynolds", param_names)
        self.assertIn("Surtunme Faktoru (f)", param_names)
        self.assertIn("Giris Hizi", param_names)
        self.assertIn("Cikis Hizi", param_names)
        self.assertIn("Cikis Basinci", param_names)

    def test_get_results_table_data_empty_result(self):
        rows = self.controller.get_results_table_data(None, TARGET_PRESSURE_DROP, {})
        self.assertEqual(rows, [])

    def test_prepare_inputs_negative_pressure_errors(self):
        state = self._base_ui_state(p_in=-5)
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNotNone(errors)
        self.assertIsNone(inputs)

    def test_prepare_inputs_zero_flow_errors(self):
        state = self._base_ui_state(flow_val=0)
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNotNone(errors)
        self.assertIsNone(inputs)

    def test_prepare_inputs_extreme_pressure_errors(self):
        state = self._base_ui_state(p_in=1500)
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNotNone(errors)
        self.assertIsNone(inputs)

    def test_prepare_inputs_mass_percent_conversion(self):
        state = self._base_ui_state(
            comp_type="Kütle %",
            gas_components={"METHANE": 0.9, "ETHANE": 0.1},
        )
        inputs, errors = self.controller.prepare_inputs(state)
        self.assertIsNone(errors)
        self.assertIsNotNone(inputs)
        self.assertGreater(len(inputs["mole_fractions"]), 0)

    def test_prepare_inputs_pressure_unit_conversions(self):
        for p_unit, p_in_val in [("Barg", 10), ("Bara", 10), ("Psig", 100), ("Psia", 100)]:
            state = self._base_ui_state(p_in=p_in_val, p_unit=p_unit)
            inputs, errors = self.controller.prepare_inputs(state)
            self.assertIsNone(errors)
            self.assertGreater(inputs["P_in"], 0)

    def test_prepare_inputs_temperature_unit_conversions(self):
        for t_unit, t_val in [("°C", 25), ("°F", 77), ("K", 300)]:
            state = self._base_ui_state(t_val=t_val, t_unit=t_unit)
            inputs, errors = self.controller.prepare_inputs(state)
            self.assertIsNone(errors)
            self.assertGreater(inputs["T"], 0)

    def test_get_results_table_data_with_phase_info(self):
        result = {
            "phase_info": {
                "phase_label_tr": "Iki Fazli (Gaz + Sivi Karisimi)",
                "warning_level": "critical",
                "vapor_quality": 0.75,
                "formula_label_tr": "Lockhart-Martinelli Iki Fazli Korelasyon",
                "transition_to_two_phase_m": 150.0,
            },
            "P_out": 15e5,
            "delta_p_total": 5e5,
            "velocity_in": 10.0,
            "velocity_out": 12.0,
            "m_dot": 2.5,
        }
        state = self._base_ui_state()
        rows = self.controller.get_results_table_data(result, TARGET_PRESSURE_DROP, state)
        param_names = [row[0] for row in rows]
        self.assertIn("Akiskan Fazi", param_names)
        self.assertIn("Buhar Kalitesi (Q)", param_names)
        self.assertIn("Kütlesel Debi", param_names)

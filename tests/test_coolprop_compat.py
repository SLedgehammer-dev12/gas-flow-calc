import math
import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations import GasFlowCalculator


class TestCoolPropCompatibility(unittest.TestCase):
    def setUp(self):
        self.calc = GasFlowCalculator()

    def test_coolprop_accepts_internal_ids(self):
        props = self.calc.calculate_thermo_properties(
            5e5,
            288.15,
            {"METHANE": 0.98, "ETHANE": 0.01, "NITROGEN": 0.005, "CARBONDIOXIDE": 0.005},
            "CoolProp (High Accuracy EOS)",
        )
        self.assertGreater(props["density"], 0)
        self.assertGreater(props["Z"], 0)

    def test_coolprop_accepts_display_names(self):
        props = self.calc.calculate_thermo_properties(
            5e5,
            288.15,
            {"Methane (CH4)": 0.9, "Ethane (C2H6)": 0.1},
            "CoolProp (High Accuracy EOS)",
        )
        self.assertGreater(props["density"], 0)
        self.assertGreater(props["Cp"], props["Cv"])

    def test_standard_flow_unit_label_is_handled(self):
        result = self.calc.calculate_pressure_drop(
            {
                "P_in": 50e5,
                "T": 293.15,
                "mole_fractions": {"Methane": 0.9, "Ethane": 0.1},
                "library_choice": "CoolProp (High Accuracy EOS)",
                "flow_rate": 1000,
                "flow_unit": "Sm³/h",
                "D_inner": 200,
                "L": 1000,
                "roughness": 4.57e-5,
                "total_k": 0.0,
                "flow_property": "Sıkıştırılabilir",
            }
        )
        self.assertGreater(result["P_out"], 0)
        self.assertLess(result["P_out"], 50e5)
        self.assertTrue(math.isfinite(result["velocity_in"]))
        self.assertLess(result["velocity_in"], 10)

    def test_cryogenic_pt_flash_uses_envelope_phase_fallback(self):
        phase = self.calc.detect_phase(
            113993.3329,
            113.15,
            {"METHANE": 0.95, "ETHANE": 0.03, "NITROGEN": 0.02},
        )
        props = self.calc.calculate_thermo_properties(
            113993.3329,
            113.15,
            {"METHANE": 0.95, "ETHANE": 0.03, "NITROGEN": 0.02},
            "CoolProp (High Accuracy EOS)",
            state=self.calc.create_coolprop_state({"METHANE": 0.95, "ETHANE": 0.03, "NITROGEN": 0.02}),
        )
        self.assertEqual(phase["phase"], "two_phase")
        self.assertEqual(phase.get("phase_detection_source"), "envelope")
        self.assertGreater(props["density"], 0)
        self.assertTrue(math.isfinite(props["density"]))

    def test_cryogenic_solid_risk_point_falls_back_without_crashing(self):
        phase = self.calc.detect_phase(
            801325.0,
            108.15,
            {
                "METHANE": 0.80,
                "ETHANE": 0.10,
                "PROPANE": 0.05,
                "BUTANE": 0.03,
                "CARBONDIOXIDE": 0.02,
            },
        )
        props = self.calc.calculate_thermo_properties(
            801325.0,
            108.15,
            {
                "METHANE": 0.80,
                "ETHANE": 0.10,
                "PROPANE": 0.05,
                "BUTANE": 0.03,
                "CARBONDIOXIDE": 0.02,
            },
            "CoolProp (High Accuracy EOS)",
            state=self.calc.create_coolprop_state(
                {
                    "METHANE": 0.80,
                    "ETHANE": 0.10,
                    "PROPANE": 0.05,
                    "BUTANE": 0.03,
                    "CARBONDIOXIDE": 0.02,
                }
            ),
        )
        self.assertEqual(phase["phase"], "liquid")
        self.assertEqual(phase["warning_level"], "critical")
        self.assertIn("kati", phase["warning_msg_tr"].lower())
        self.assertGreater(props["density"], 0)
        self.assertTrue(math.isfinite(props["density"]))


if __name__ == "__main__":
    unittest.main()

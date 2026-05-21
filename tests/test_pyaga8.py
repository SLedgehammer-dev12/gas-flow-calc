import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from calculations import GasFlowCalculator


class TestPYAGA8Integration(unittest.TestCase):
    def setUp(self):
        self.calc = GasFlowCalculator()

    def test_aga8_gerg2008_returns_all_keys(self):
        props = self.calc.calculate_thermo_properties(
            5e6, 300,
            {"METHANE": 0.90, "ETHANE": 0.05, "PROPANE": 0.03, "NITROGEN": 0.02},
            "AGA-8 GERG-2008",
        )
        for key in ("MW", "Cp", "Cv", "Z", "density", "viscosity", "standard_density", "sonic_velocity"):
            self.assertIn(key, props, f"Missing key: {key}")
        self.assertGreater(props["density"], 0)
        self.assertGreater(props["Z"], 0.1)
        self.assertLess(props["Z"], 5.0)
        self.assertGreater(props["MW"], 10)
        self.assertGreater(props["Cp"], 0)
        self.assertGreater(props["Cv"], 0)
        self.assertGreater(props["sonic_velocity"], 200)

    def test_aga8_detail_returns_valid_z(self):
        props = self.calc.calculate_thermo_properties(
            1e6, 288.15,
            {"METHANE": 1.0},
            "AGA-8 DETAIL",
        )
        self.assertIn("Z", props)
        self.assertAlmostEqual(props["Z"], 0.95, delta=0.15)

    def test_aga8_pressure_drop_runs(self):
        inputs = {
            "P_in": 50e5, "T": 300,
            "mole_fractions": {"METHANE": 0.92, "ETHANE": 0.05, "PROPANE": 0.03},
            "library_choice": "AGA-8 GERG-2008",
            "flow_rate": 5000, "flow_unit": "Sm3/h",
            "D_inner": 100, "L": 5000,
            "roughness": 4.57e-5, "total_k": 2.5,
            "flow_property": "Compressible", "flow_mode": "compressible",
        }
        result = self.calc.calculate_pressure_drop(inputs)
        self.assertIn("P_out", result)
        self.assertLess(result["P_out"], inputs["P_in"])
        self.assertGreater(result["delta_p_total"], 0)

    def test_aga8_max_length_runs(self):
        inputs = {
            "P_in": 50e5, "T": 300,
            "mole_fractions": {"METHANE": 0.92, "ETHANE": 0.05, "PROPANE": 0.03},
            "library_choice": "AGA-8 DETAIL",
            "flow_rate": 5000, "flow_unit": "Sm3/h",
            "D_inner": 100, "L": 5000,
            "roughness": 4.57e-5, "total_k": 2.5,
            "flow_property": "Compressible", "flow_mode": "compressible",
            "P_out_target": 10e5,
        }
        result = self.calc.calculate_max_length(inputs)
        self.assertIn("L_max", result)
        self.assertGreater(result["L_max"], 0)

    def test_aga8_invalid_composition_raises(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_thermo_properties(
                5e6, 300,
                {"KRYPTON": 1.0},
                "AGA-8 GERG-2008",
            )

    def test_aga8_compares_to_coolprop_z(self):
        mole = {"METHANE": 0.92, "ETHANE": 0.05, "PROPANE": 0.03}
        cp = self.calc.calculate_thermo_properties(5e6, 300, mole, "CoolProp (High Accuracy EOS)")
        aga8 = self.calc.calculate_thermo_properties(5e6, 300, mole, "AGA-8 GERG-2008")
        # Z values should be close
        self.assertAlmostEqual(cp["Z"], aga8["Z"], delta=0.1)


class TestThermoModelDispatch(unittest.TestCase):
    def setUp(self):
        self.calc = GasFlowCalculator()
        self.mole = {"METHANE": 0.92, "ETHANE": 0.05, "PROPANE": 0.03}

    def test_all_models_return_props(self):
        models = [
            "CoolProp (High Accuracy EOS)",
            "AGA-8 GERG-2008",
            "AGA-8 DETAIL",
            "Peng-Robinson (PR EOS)",
            "Soave-Redlich-Kwong (SRK EOS)",
            "Pseudo-Critical (Kay's Rule)",
        ]
        for model in models:
            with self.subTest(model=model):
                props = self.calc.calculate_thermo_properties(5e6, 300, self.mole, model)
                self.assertGreater(props["density"], 0, f"Model {model} returned invalid density")
                self.assertGreater(props["Z"], 0, f"Model {model} returned invalid Z")

    def test_invalid_model_raises(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_thermo_properties(5e6, 300, self.mole, "Invalid Model Name")

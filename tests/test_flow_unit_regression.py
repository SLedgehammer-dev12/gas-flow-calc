import unittest

from calculations import GasFlowCalculator
from translations import t


class TestFlowUnitRegression(unittest.TestCase):
    def setUp(self):
        self.calc = GasFlowCalculator()
        self.calc.calculate_thermo_properties = lambda *args, **kwargs: {
            "density": 10.0,
            "viscosity": 1e-5,
            "standard_density": 2.0,
            "sonic_velocity": 400.0,
        }
        self.calc.create_coolprop_state = lambda *args, **kwargs: None

    def test_pressure_drop_uses_standard_density_for_standard_volumetric_flow(self):
        volumetric_inputs = {
            "P_in": 1_000_000.0,
            "T": 293.15,
            "mole_fractions": {"METHANE": 1.0},
            "library_choice": "CoolProp (High Accuracy EOS)",
            "flow_rate": 3600.0,
            "flow_unit": "Sm\u00b3/h",
            "D_inner": 500.0,
            "L": 100.0,
            "roughness": 4.57e-5,
            "total_k": 0.0,
            "flow_property": t("flow_incompressible"),
        }
        mass_inputs = dict(volumetric_inputs, flow_rate=2.0, flow_unit="kg/s")

        volumetric_result = self.calc.calculate_pressure_drop(volumetric_inputs)
        mass_result = self.calc.calculate_pressure_drop(mass_inputs)

        self.assertAlmostEqual(volumetric_result["m_dot"], 2.0)
        self.assertAlmostEqual(volumetric_result["m_dot"], mass_result["m_dot"])
        self.assertAlmostEqual(volumetric_result["velocity_in"], mass_result["velocity_in"])

    def test_max_length_matches_equivalent_mass_flow_for_standard_volumetric_input(self):
        base_inputs = {
            "P_in": 1_000_000.0,
            "P_out_target": 900_000.0,
            "T": 293.15,
            "mole_fractions": {"METHANE": 1.0},
            "library_choice": "CoolProp (High Accuracy EOS)",
            "D_inner": 500.0,
            "roughness": 4.57e-5,
            "total_k": 0.0,
            "flow_property": t("flow_compressible"),
        }
        volumetric_inputs = dict(base_inputs, flow_rate=3600.0, flow_unit="Sm\u00b3/h")
        mass_inputs = dict(base_inputs, flow_rate=2.0, flow_unit="kg/s")

        volumetric_result = self.calc.calculate_max_length(volumetric_inputs)
        mass_result = self.calc.calculate_max_length(mass_inputs)

        self.assertAlmostEqual(volumetric_result["m_dot"], 2.0)
        self.assertAlmostEqual(volumetric_result["L_max"], mass_result["L_max"])
        self.assertAlmostEqual(volumetric_result["delta_p_pipe"], mass_result["delta_p_pipe"])

    def test_max_length_returns_explicit_error_when_fittings_alone_exceed_target(self):
        result = self.calc.calculate_max_length(
            {
                "P_in": 1_000_000.0,
                "P_out_target": 990_000.0,
                "T": 293.15,
                "mole_fractions": {"METHANE": 1.0},
                "library_choice": "CoolProp (High Accuracy EOS)",
                "flow_rate": 50.0,
                "flow_unit": "kg/s",
                "D_inner": 100.0,
                "roughness": 4.57e-5,
                "total_k": 10.0,
                "flow_property": t("flow_compressible"),
            }
        )

        self.assertEqual(result["L_max"], 0)
        self.assertIn("error", result)
        self.assertGreater(result["delta_p_fittings"], 0)


if __name__ == "__main__":
    unittest.main()

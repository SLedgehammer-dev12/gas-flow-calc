import unittest
import pytest
import math
from calculations import GasFlowCalculator
from flow_utils import (
    normalize_flow_mode,
    is_compressible_flow,
    is_incompressible_flow,
    get_flow_mode_label,
    FLOW_MODE_COMPRESSIBLE,
    FLOW_MODE_INCOMPRESSIBLE,
)
from target_utils import (
    normalize_calc_target,
    get_calc_target_label,
    TARGET_PRESSURE_DROP,
    TARGET_MAX_LENGTH,
    TARGET_MIN_DIAMETER,
)
from translations import (
    set_language,
    get_language,
    t,
    t_fitting,
    get_fitting_name_tr,
)
from release_metadata import (
    get_release_notes,
    get_release_notes_title,
    get_versioned_exe_stem,
    get_versioned_exe_name,
    APP_VERSION,
    APP_NAME,
)

class TestFlowUtilsGaps(unittest.TestCase):
    def test_normalize_flow_mode(self):
        self.assertEqual(normalize_flow_mode("compressible"), FLOW_MODE_COMPRESSIBLE)
        self.assertEqual(normalize_flow_mode("incompressible"), FLOW_MODE_INCOMPRESSIBLE)
        self.assertEqual(normalize_flow_mode("sıkıştırılabilir"), FLOW_MODE_COMPRESSIBLE)
        self.assertEqual(normalize_flow_mode("sıkıştırılamaz"), FLOW_MODE_INCOMPRESSIBLE)
        self.assertEqual(normalize_flow_mode("sÄ±kÄ±ÅŸtÄ±rÄ±labilir"), FLOW_MODE_COMPRESSIBLE)
        self.assertEqual(normalize_flow_mode("sÄ±kÄ±ÅŸtÄ±rÄ±lamaz"), FLOW_MODE_INCOMPRESSIBLE)
        self.assertEqual(normalize_flow_mode(None), FLOW_MODE_COMPRESSIBLE)
        self.assertEqual(normalize_flow_mode("unknown", default="fallback"), "fallback")

    def test_flow_mode_helpers(self):
        self.assertTrue(is_compressible_flow("compressible"))
        self.assertFalse(is_compressible_flow("incompressible"))
        self.assertTrue(is_incompressible_flow("incompressible"))
        self.assertFalse(is_incompressible_flow("compressible"))

    def test_get_flow_mode_label(self):
        self.assertEqual(get_flow_mode_label("compressible", "Comp", "Incomp"), "Comp")
        self.assertEqual(get_flow_mode_label("incompressible", "Comp", "Incomp"), "Incomp")

class TestTargetUtilsGaps(unittest.TestCase):
    def test_normalize_calc_target(self):
        self.assertEqual(normalize_calc_target("pressure_drop"), TARGET_PRESSURE_DROP)
        self.assertEqual(normalize_calc_target("çıkış basıncı"), TARGET_PRESSURE_DROP)
        self.assertEqual(normalize_calc_target("cikis basinci"), TARGET_PRESSURE_DROP)
        self.assertEqual(normalize_calc_target("outlet pressure"), TARGET_PRESSURE_DROP)
        self.assertEqual(normalize_calc_target("maksimum uzunluk"), TARGET_MAX_LENGTH)
        self.assertEqual(normalize_calc_target("maximum length"), TARGET_MAX_LENGTH)
        self.assertEqual(normalize_calc_target("minimum çap"), TARGET_MIN_DIAMETER)
        self.assertEqual(normalize_calc_target("minimum cap"), TARGET_MIN_DIAMETER)
        self.assertEqual(normalize_calc_target("minimum diameter"), TARGET_MIN_DIAMETER)
        self.assertEqual(normalize_calc_target(None), TARGET_MIN_DIAMETER)

    def test_get_calc_target_label(self):
        self.assertEqual(get_calc_target_label("pressure_drop", "P", "L", "D"), "P")
        self.assertEqual(get_calc_target_label("max_length", "P", "L", "D"), "L")
        self.assertEqual(get_calc_target_label("min_diameter", "P", "L", "D"), "D")

class TestTranslationsGaps(unittest.TestCase):
    def setUp(self):
        self.original_lang = get_language()

    def tearDown(self):
        set_language(self.original_lang)

    def test_language_get_set(self):
        set_language("en")
        self.assertEqual(get_language(), "en")
        set_language("tr")
        self.assertEqual(get_language(), "tr")
        set_language("invalid_lang") # should ignore invalid lang
        self.assertEqual(get_language(), "tr")

    def test_t_function(self):
        set_language("tr")
        self.assertEqual(t("app_title"), "Doğal Gaz Hesaplayıcı")
        set_language("en")
        self.assertEqual(t("app_title"), "Natural Gas Calculator")
        self.assertEqual(t("non_existent_key", "default_val"), "default_val")
        self.assertEqual(t("non_existent_key"), "non_existent_key")

    def test_fitting_translations(self):
        set_language("tr")
        self.assertEqual(t_fitting("90° Dirsek"), "90° Dirsek")
        set_language("en")
        self.assertEqual(t_fitting("90° Dirsek"), "90° Elbow")
        self.assertEqual(t_fitting("Unknown Fitting"), "Unknown Fitting")

    def test_get_fitting_name_tr(self):
        set_language("tr")
        self.assertEqual(get_fitting_name_tr("90° Dirsek"), "90° Dirsek")
        set_language("en")
        self.assertEqual(get_fitting_name_tr("90° Elbow"), "90° Dirsek")
        self.assertEqual(get_fitting_name_tr("Unknown"), "Unknown")

class TestReleaseMetadataGaps(unittest.TestCase):
    def test_release_notes(self):
        self.assertIn("6.1.0", get_release_notes("6.1.0", "tr"))
        self.assertIn("6.1.0", get_release_notes("6.1.0", "en"))
        self.assertEqual(get_release_notes("non_existent_version", "en"), "")

    def test_release_notes_title(self):
        self.assertEqual(get_release_notes_title("6.1.0", "tr"), "Guncelleme Notlari (Versiyon 6.1.0)")
        self.assertEqual(get_release_notes_title("6.1.0", "en"), "Update Notes (Version 6.1.0)")

    def test_versioned_exe(self):
        self.assertEqual(get_versioned_exe_stem("1.0.0"), f"{APP_NAME} V1.0.0")
        self.assertEqual(get_versioned_exe_name("1.0.0"), f"{APP_NAME} V1.0.0.exe")
        self.assertEqual(get_versioned_exe_name(), f"{APP_NAME} V{APP_VERSION}.exe")

class TestCalculationEdgeCases(unittest.TestCase):
    def setUp(self):
        self.calc = GasFlowCalculator()

    def test_input_validation_empty_mole_fractions(self):
        with self.assertRaises(ValueError):
            self.calc.validate_inputs({"P_in": 1e5, "T": 300, "flow_rate": 100})

    def test_input_validation_negative_pressure(self):
        with self.assertRaises(ValueError):
            self.calc.validate_inputs({"mole_fractions": {"METHANE": 1.0}, "P_in": -1e5, "T": 300, "flow_rate": 100})

    def test_input_validation_negative_temperature(self):
        with self.assertRaises(ValueError):
            self.calc.validate_inputs({"mole_fractions": {"METHANE": 1.0}, "P_in": 1e5, "T": -10, "flow_rate": 100})

    def test_input_validation_negative_flow_rate(self):
        with self.assertRaises(ValueError):
            self.calc.validate_inputs({"mole_fractions": {"METHANE": 1.0}, "P_in": 1e5, "T": 300, "flow_rate": -10})

    def test_normalize_mole_fractions_zero_moles(self):
        with self.assertRaises(ValueError):
            self.calc.normalize_mole_fractions({"METHANE": 0.0})

    def test_normalize_gas_name_unsupported(self):
        with self.assertRaises(ValueError):
            self.calc.normalize_gas_name("UNSUPPORTED_GAS_NAME")

    def test_churchill_friction_factor_zero_reynolds(self):
        # Should log warning and return default value 0.02
        self.assertEqual(self.calc.get_churchill_friction_factor(0, 0.001), 0.02)
        self.assertEqual(self.calc.get_churchill_friction_factor(-100, 0.001), 0.02)

    def test_pure_component_props_unsupported_fluid(self):
        with self.assertRaises(ValueError):
            self.calc.get_pure_component_props("UNSUPPORTED_FLUID")

    def test_calculate_cubic_eos_props_invalid_roots(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_thermo_properties(1e5, 300, {"METHANE": 1.0}, "INVALID_MODEL")

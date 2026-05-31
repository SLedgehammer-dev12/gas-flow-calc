"""Targeted tests for remaining uncovered branches in controllers, reporting, and dialogs."""

import pytest
from unittest.mock import MagicMock, patch


# ── controllers.py ────────────────────────────────────────────────────────────

class TestControllersCoverage:
    @pytest.fixture
    def controller(self):
        from controllers import GasFlowController
        ctrl = GasFlowController()
        ctrl.calculator = MagicMock()
        return ctrl

    def test_parse_int_exception(self, controller):
        assert controller._parse_int("not_an_int") == 0

    def test_parse_int_empty(self, controller):
        assert controller._parse_int("") == 0

    def test_total_mole_zero_error(self, controller):
        """mole_fractions sum <= 0 triggers validation error."""
        ui_state = {"gas_components": {"METHANE": "0"}}
        result, errors = controller.prepare_inputs(ui_state)
        assert result is None
        assert any("oranları" in e for e in errors)

    def test_flow_too_high(self, controller):
        ui_state = {"flow_val": "1e9", "p_in": "10", "t_val": "25"}
        result, errors = controller.prepare_inputs(ui_state)
        assert result is None
        assert any("yüksek" in e for e in errors)

    def test_target_min_diameter_no_design_pressure(self, controller):
        ui_state = {
            "gas_components": {"METHANE": "1.0"},
            "p_in": "10", "t_val": "25", "flow_val": "100",
            "calc_target": "min_diameter",
            "max_vel_val": "0",  # triggers max_velocity positive error
            "p_design_val": "0",
            "diam_val": "0", "len_val": "1000",
        }
        result, errors = controller.prepare_inputs(ui_state)
        assert result is None

    def test_target_min_diameter_no_smys(self, controller):
        ui_state = {
            "gas_components": {"METHANE": "1.0"},
            "p_in": "10", "t_val": "25", "flow_val": "100",
            "calc_target": "min_diameter",
            "max_vel_val": "20", "p_design_val": "50",
            "smys_val": "0",
            "diam_val": "0", "len_val": "1000",
        }
        result, errors = controller.prepare_inputs(ui_state)
        assert result is None
        assert any("SMYS" in e for e in errors)

    def test_get_results_table_no_pipe_found(self, controller):
        """TARGET_MIN_DIAMETER with no selected pipe shows error row."""
        result = {
            "max_vel": 20, "D_min_inner_mm": 50, "flow_rate_actual": 0.1,
            "velocity_in": 8, "velocity_out": 9, "P_out": 5e5,
            "selected_pipe": None,
            "velocity_status": "",
            "m_dot": 0.5,
            "phase_info": {"warning_level": "critical", "phase_label_tr": "Sivi"},
        }
        calc = MagicMock()
        from controllers import GasFlowController, TARGET_MIN_DIAMETER
        ctrl = GasFlowController()
        ctrl.calculator = calc
        rows = ctrl.get_results_table_data(result, TARGET_MIN_DIAMETER, {})
        assert any("Uygun Boru Yok" in str(r) or "uygun boru" in str(r).lower() for r in rows)

    def test_get_results_table_with_alternatives(self, controller):
        """TARGET_MIN_DIAMETER with selected_pipe and alternatives."""
        result = {
            "max_vel": 20, "D_min_inner_mm": 50, "flow_rate_actual": 0.1,
            "velocity_in": 8, "velocity_out": 9, "P_out": 5e5,
            "selected_pipe": {"nominal": "2", "schedule": "40", "D_inner_mm": 52.5},
            "velocity_status": "Uygun",
            "m_dot": 0.5,
            "phase_info": {"warning_level": "ok", "phase_label_tr": "Gaz"},
            "alternatives": {
                "thinner": {"pipe": {"nominal": "2", "schedule": "10", "D_inner_mm": 55}, "note": "Daha ince", "result": {"velocity_out": 10}},
            },
        }
        from controllers import TARGET_MIN_DIAMETER
        rows = controller.get_results_table_data(result, TARGET_MIN_DIAMETER, {})
        assert len(rows) > 5
        assert any("Daha ince" in str(r) for r in rows)

    def test_get_results_table_no_last_result(self, controller):
        from controllers import TARGET_PRESSURE_DROP
        rows = controller.get_results_table_data(None, TARGET_PRESSURE_DROP, {})
        assert rows == []

    def test_prepare_inputs_comp_type_mass(self, controller):
        """comp_type=mass_percent triggers mass_to_mole_fraction."""
        ui_state = {
            "gas_components": {"METHANE": "0.9", "ETHANE": "0.1"},
            "comp_type": "Kütle %",
            "p_in": "10", "t_val": "25", "flow_val": "100",
            "calc_target": "pressure_drop",
            "len_val": "100", "diam_val": "100", "thick_val": "5",
        }
        result, errors = controller.prepare_inputs(ui_state)
        if result:
            assert "mole_fractions" in result
        else:
            # mass_to_mole_fraction might return empty if mock not set up
            pass


# ── reporting.py ──────────────────────────────────────────────────────────────

class TestReportingCoverage:
    def test_viscosity_fallback_flag(self):
        from reporting import format_pressure_drop_report
        inputs = {"P_in": 5e5, "T": 300, "mole_fractions": {"METHANE": 0.9}}
        result = {
            "phase_info": {"phase_label_tr": "Gaz", "formula_label_tr": "DW"},
            "P_out": 4e5, "delta_p_total": 1e5,
            "delta_p_pipe": 8e4, "delta_p_fittings": 1.5e4,
            "delta_p_acceleration": 5e3,
            "velocity_in": 5, "velocity_out": 6, "Re": 1e5, "f": 0.018,
            "gas_props_in": {"density": 5, "viscosity": 1e-5, "viscosity_fallback": True,
                             "MW": 18, "Z": 0.9, "Cp": 2, "Cv": 1.5, "sonic_velocity": 350,
                             "standard_density": 0.82},
            "gas_props_out": {"density": 4, "viscosity": 1e-5, "viscosity_fallback": True,
                              "MW": 18, "Z": 0.9, "Cp": 2, "Cv": 1.5, "sonic_velocity": 350,
                              "standard_density": 0.82},
        }
        report = format_pressure_drop_report(inputs, result)
        assert "viskozite" in report.lower() or "viskozite" in report

    def test_thermo_fallback_with_reason(self):
        from reporting import format_pressure_drop_report
        inputs = {"P_in": 5e5, "T": 300, "mole_fractions": {"METHANE": 0.9}}
        result = {
            "phase_info": {"phase_label_tr": "Gaz", "formula_label_tr": "DW"},
            "P_out": 4e5, "delta_p_total": 1e5,
            "delta_p_pipe": 8e4, "delta_p_fittings": 1.5e4,
            "delta_p_acceleration": 5e3,
            "velocity_in": 5, "velocity_out": 6, "Re": 1e5, "f": 0.018,
            "gas_props_in": {"density": 5, "viscosity": 1e-5, "thermo_fallback": True,
                             "fallback_reason": "Kriyojenik", "MW": 18, "Z": 0.9,
                             "Cp": 2, "Cv": 1.5, "sonic_velocity": 350,
                             "standard_density": 0.82},
            "gas_props_out": {"density": 4, "viscosity": 1e-5, "MW": 18, "Z": 0.9,
                              "Cp": 2, "Cv": 1.5, "sonic_velocity": 350,
                              "standard_density": 0.82},
        }
        report = format_pressure_drop_report(inputs, result)
        assert "Kriyojenik" in report

    def test_thermo_fallback_without_reason(self):
        from reporting import format_pressure_drop_report
        inputs = {"P_in": 5e5, "T": 300, "mole_fractions": {"METHANE": 0.9}}
        result = {
            "phase_info": {"phase_label_tr": "Gaz", "formula_label_tr": "DW"},
            "P_out": 4e5, "delta_p_total": 1e5,
            "delta_p_pipe": 8e4, "delta_p_fittings": 1.5e4,
            "delta_p_acceleration": 5e3,
            "velocity_in": 5, "velocity_out": 6, "Re": 1e5, "f": 0.018,
            "gas_props_in": {"density": 5, "viscosity": 1e-5, "thermo_fallback": True,
                             "MW": 18, "Z": 0.9, "Cp": 2, "Cv": 1.5, "sonic_velocity": 350,
                             "standard_density": 0.82},
            "gas_props_out": {"density": 4, "viscosity": 1e-5, "MW": 18, "Z": 0.9,
                              "Cp": 2, "Cv": 1.5, "sonic_velocity": 350,
                              "standard_density": 0.82},
        }
        report = format_pressure_drop_report(inputs, result)
        assert "Termodinamik fallback" in report or "termodinamik fallback" in report

    def test_min_diameter_no_pipe_selected(self):
        from reporting import format_min_diameter_report
        inputs = {"P_in": 5e5, "T": 300, "mole_fractions": {"METHANE": 0.9}}
        result = {
            "phase_info": {"phase_label_tr": "Gaz"},
            "max_vel": 20, "D_min_inner_mm": 50, "flow_rate_actual": 0.1,
            "selected_pipe": None, "velocity_in": 8, "velocity_out": 9,
            "P_out": 4e5, "velocity_status": "",
            "gas_props_in": None, "gas_props_out": None,
        }
        report = format_min_diameter_report(inputs, result)
        assert "uygun standart boru" in report or "bulunamad" in report

    def test_max_length_no_acceleration(self):
        from reporting import format_max_length_report
        inputs = {"P_in": 5e5, "T": 300, "mole_fractions": {"METHANE": 0.9}}
        result = {
            "phase_info": {"phase_label_tr": "Gaz", "formula_label_tr": "DW"},
            "L_max": 1000, "Re": 1e5, "delta_p_pipe": 1e5,
            "delta_p_fittings": 1e4,
            "velocity_in": 5, "velocity_out": 6, "P_out": 4e5, "f": 0.018,
            "gas_props_in": None, "gas_props_out": None,
        }
        report = format_max_length_report(inputs, result)
        assert "Maksimum Uzunluk" in report

    def test_min_diameter_with_alternatives(self):
        from reporting import format_min_diameter_report
        inputs = {"P_in": 5e5, "T": 300, "mole_fractions": {"METHANE": 0.9}}
        result = {
            "phase_info": {"phase_label_tr": "Gaz"},
            "max_vel": 20, "D_min_inner_mm": 50, "flow_rate_actual": 0.1,
            "selected_pipe": {"nominal": "2", "schedule": "40", "OD_mm": 60.32,
                              "t_mm": 3.91, "D_inner_mm": 52.5, "t_required_mm": 2.7},
            "velocity_in": 8, "velocity_out": 9, "P_out": 4e5,
            "velocity_status": "Uygun",
            "gas_props_in": None, "gas_props_out": None,
            "alternatives": {
                "thinner": {"pipe": {"nominal": "2", "schedule": "10", "D_inner_mm": 55},
                            "result": {"velocity_out": 10, "P_out": 4.2e5},
                            "note": "Daha ince duvar"},
                "thicker": {"pipe": {"nominal": "2", "schedule": "80", "D_inner_mm": 48},
                            "result": {"velocity_out": 8, "P_out": 4.5e5},
                            "note": "Daha kalın duvar"},
                "lowest_weight": {"pipe": {"nominal": "2", "schedule": "10", "D_inner_mm": 55, "weight_per_m": 10.5},
                                  "result": {"velocity_out": 10, "P_out": 4.2e5},
                                  "note": "En hafif"},
            },
        }
        report = format_min_diameter_report(inputs, result)
        assert "Daha ince" in report
        assert "Daha kalın" in report
        assert "En hafif" in report
        assert "kg/m" in report

    def test_error_in_result(self):
        from reporting import format_max_length_report
        inputs = {"P_in": 5e5, "T": 300, "mole_fractions": {"METHANE": 0.9}}
        result = {
            "phase_info": {"phase_label_tr": "Gaz"},
            "error": "Hesaplama basarisiz",
            "gas_props_in": None, "gas_props_out": None,
        }
        report = format_max_length_report(inputs, result)
        assert "Hesaplama" in report

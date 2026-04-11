from reporting import (
    format_max_length_report,
    format_min_diameter_report,
    format_pressure_drop_report,
)


def _sample_props(density):
    return {
        "density": density,
        "standard_density": 0.82,
        "MW": 18.5,
        "viscosity": 1.1e-5,
        "Z": 0.94,
        "Cp": 2.35,
        "Cv": 1.82,
        "sonic_velocity": 360.0,
    }


def test_pressure_drop_report_includes_composition_and_properties():
    inputs = {
        "P_in": 5.0e5,
        "T": 288.15,
        "mole_fractions": {"METHANE": 0.9, "ETHANE": 0.1},
    }
    result = {
        "phase_info": {
            "phase_label_tr": "Tek Fazli Gaz",
            "warning_level": "ok",
            "formula_label_tr": "Darcy-Weisbach (Sikistirilabilir Gaz)",
        },
        "P_out": 4.5e5,
        "delta_p_total": 5.0e4,
        "delta_p_pipe": 4.0e4,
        "delta_p_fittings": 9.0e3,
        "delta_p_acceleration": 1.0e3,
        "velocity_in": 4.2,
        "velocity_out": 4.8,
        "Re": 120000,
        "f": 0.018,
        "gas_props_in": _sample_props(4.1),
        "gas_props_out": _sample_props(3.6),
    }

    report = format_pressure_drop_report(inputs, result)
    assert "=== GIRILEN KOMPOZISYON ===" in report
    assert "=== AKISKAN OZELLIKLERI (GIRIS PT) ===" in report
    assert "=== AKISKAN OZELLIKLERI (CIKIS PT) ===" in report
    assert "Molekuler Agirlik" in report
    assert "Methane" in report
    assert "Ivmelenme Terimi" in report


def test_max_length_report_includes_outlet_properties():
    inputs = {
        "P_in": 8.0e5,
        "T": 300.0,
        "mole_fractions": {"PROPANE": 1.0},
    }
    result = {
        "phase_info": {
            "phase_label_tr": "Tek Fazli Sivi",
            "warning_level": "warning",
            "formula_label_tr": "Darcy-Weisbach + Churchill f + Ivmelenme Duzeltmesi",
        },
        "L_max": 1240.0,
        "Re": 54000,
        "delta_p_pipe": 1.2e5,
        "delta_p_fittings": 2.5e4,
        "delta_p_acceleration": 1.4e3,
        "gas_props_in": _sample_props(510.0),
        "gas_props_out": _sample_props(503.0),
    }

    report = format_max_length_report(inputs, result)
    assert "Maksimum Uzunluk" in report
    assert "AKISKAN OZELLIKLERI (GIRIS PT)" in report
    assert "AKISKAN OZELLIKLERI (CIKIS PT)" in report


def test_min_diameter_report_includes_property_sections():
    inputs = {
        "P_in": 6.0e5,
        "T": 295.0,
        "mole_fractions": {"METHANE": 0.85, "ETHANE": 0.15},
    }
    result = {
        "phase_info": {
            "phase_label_tr": "Tek Fazli Gaz",
            "warning_level": "ok",
            "formula_label_tr": "Darcy-Weisbach (Sikistirilabilir Gaz)",
        },
        "max_vel": 20.0,
        "D_min_inner_mm": 48.0,
        "flow_rate_actual": 0.12,
        "selected_pipe": {
            "nominal": '2',
            "schedule": "40",
            "OD_mm": 60.32,
            "t_mm": 3.91,
            "D_inner_mm": 52.5,
            "t_required_mm": 2.7,
        },
        "velocity_in": 8.2,
        "velocity_out": 9.1,
        "P_out": 5.4e5,
        "velocity_status": "Uygun",
        "gas_props_in": _sample_props(5.0),
        "gas_props_out": _sample_props(4.4),
        "alternatives": {},
    }

    report = format_min_diameter_report(inputs, result)
    assert "SECILEN BORU" in report
    assert "AKISKAN OZELLIKLERI (GIRIS PT)" in report
    assert "AKISKAN OZELLIKLERI (CIKIS PT)" in report

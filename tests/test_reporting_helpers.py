import unittest

from reporting import format_max_length_report, format_min_diameter_report, format_pressure_drop_report


class TestReportingHelpers(unittest.TestCase):
    def test_pressure_drop_report_contains_core_values(self):
        report = format_pressure_drop_report(
            {"P_in": 50e5},
            {
                "P_out": 48e5,
                "delta_p_total": 2e5,
                "delta_p_pipe": 1.5e5,
                "delta_p_fittings": 0.5e5,
                "velocity_in": 8.2,
                "velocity_out": 9.1,
                "Re": 123456,
                "f": 0.01234,
                "phase_info": {
                    "phase_label_tr": "Tek Fazli Gaz",
                    "warning_level": "ok",
                    "warning_msg_tr": "",
                    "vapor_quality": None,
                    "formula_label_tr": "Darcy-Weisbach (Sikistirilabilir Gaz)",
                },
            },
        )
        self.assertIn("Cikis Basinci", report)
        self.assertIn("48.0000 bara", report)
        self.assertIn("123456", report)
        self.assertIn("FAZ DURUMU", report)

    def test_max_length_report_formats_error(self):
        report = format_max_length_report({}, {"error": "test hata"})
        self.assertIn("HATA", report)
        self.assertIn("test hata", report)

    def test_min_diameter_report_includes_selected_pipe(self):
        report = format_min_diameter_report(
            {},
            {
                "max_vel": 20.0,
                "D_min_inner_mm": 200.0,
                "flow_rate_actual": 1.2345,
                "selected_pipe": {
                    "nominal": "8",
                    "schedule": "40",
                    "OD_mm": 219.08,
                    "t_mm": 8.18,
                    "D_inner_mm": 202.72,
                    "t_required_mm": 5.20,
                },
                "velocity_in": 7.1,
                "velocity_out": 8.3,
                "P_out": b"4500000",
                "velocity_status": "Uygun",
                "alternatives": {},
                "phase_info": {
                    "phase_label_tr": "Iki Fazli (Gaz + Sivi Karisimi)",
                    "warning_level": "warning",
                    "warning_msg_tr": "Iki fazli bolge tespit edildi.",
                    "vapor_quality": 0.847,
                    "formula_label_tr": "Lockhart-Martinelli Iki Fazli Korelasyon",
                    "transition_to_two_phase_m": 12.5,
                },
            },
        )
        self.assertIn('Nominal Cap: 8"', report)
        self.assertIn("45.0000 bara", report)
        self.assertIn("Buhar Kalitesi (Q): 0.847", report)
        self.assertIn("Iki Faz Gecis Mesafesi: 12.50 m", report)

    def test_reports_tolerate_bytes_values(self):
        report = format_min_diameter_report(
            {},
            {
                "max_vel": b"20.0",
                "D_min_inner_mm": b"200.0",
                "flow_rate_actual": b"1.2345",
                "selected_pipe": {
                    "nominal": b"8",
                    "schedule": b"40",
                    "OD_mm": b"219.08",
                    "t_mm": b"8.18",
                    "D_inner_mm": b"202.72",
                    "t_required_mm": b"5.20",
                    "weight_per_m": b"36.7",
                },
                "velocity_in": b"7.1",
                "velocity_out": b"8.3",
                "P_out": 45e5,
                "velocity_status": b"Uygun",
                "alternatives": {},
                "phase_info": {
                    "phase_label_tr": b"Iki Fazli",
                    "warning_level": "warning",
                    "warning_msg_tr": b"Iki fazli bolge tespit edildi.",
                    "vapor_quality": b"0.847",
                    "formula_label_tr": b"Lockhart-Martinelli",
                    "transition_to_two_phase_m": b"12.5",
                },
            },
        )
        self.assertIn('Nominal Cap: 8"', report)
        self.assertIn("Buhar Kalitesi (Q): 0.847", report)
        self.assertIn("Lockhart-Martinelli", report)

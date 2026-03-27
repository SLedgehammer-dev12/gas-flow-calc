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
            },
        )
        self.assertIn("Cikis Basinci", report)
        self.assertIn("48.0000 bara", report)
        self.assertIn("123456", report)

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
                "P_out": 45e5,
                "velocity_status": "Uygun",
                "alternatives": {},
            },
        )
        self.assertIn('Nominal Cap: 8"', report)
        self.assertIn("45.0000 bara", report)

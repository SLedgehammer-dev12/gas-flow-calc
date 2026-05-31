import pytest
from constants import convert_pressure_to_pa, convert_temperature_to_k, BAR_TO_PA, PSI_TO_PA


class TestUnitConversions:
    def test_convert_pressure_barg_to_pa(self):
        assert convert_pressure_to_pa(10, "Barg") == pytest.approx((10 + 1.01325) * 1e5)

    def test_convert_pressure_bara_to_pa(self):
        assert convert_pressure_to_pa(10, "Bara") == pytest.approx(10 * 1e5)

    def test_convert_pressure_psig_to_pa(self):
        assert convert_pressure_to_pa(100, "Psig") == pytest.approx((100 + 14.696) * PSI_TO_PA)

    def test_convert_pressure_psia_to_pa(self):
        assert convert_pressure_to_pa(100, "Psia") == pytest.approx(100 * PSI_TO_PA)

    def test_convert_pressure_case_insensitive(self):
        p1 = convert_pressure_to_pa(10, "barg")
        p2 = convert_pressure_to_pa(10, "Barg")
        assert p1 == pytest.approx(p2)

    def test_convert_pressure_unknown_unit_passthrough(self):
        assert convert_pressure_to_pa(500, "XYZ") == 500

    def test_convert_temperature_celsius_to_k(self):
        assert convert_temperature_to_k(25, "°C") == pytest.approx(298.15)

    def test_convert_temperature_fahrenheit_to_k(self):
        assert convert_temperature_to_k(77, "°F") == pytest.approx(298.15)

    def test_convert_temperature_kelvin_passthrough(self):
        assert convert_temperature_to_k(300, "K") == 300

    def test_convert_temperature_unknown_unit_passthrough(self):
        assert convert_temperature_to_k(300, "X") == 300

    def test_temperature_below_absolute_zero_converts(self):
        t = convert_temperature_to_k(-300, "°C")
        assert t < 0

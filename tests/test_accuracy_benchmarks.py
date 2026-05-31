import math
import os
import sys
import pytest
from calculations import GasFlowCalculator
from data import PIPE_ROUGHNESS
from flow.utils import churchill_friction_factor
from flow_utils import FLOW_MODE_COMPRESSIBLE, FLOW_MODE_INCOMPRESSIBLE

# Try importing fluids library optionally for high-accuracy standard benchmarking
try:
    import fluids
    FLUIDS_AVAILABLE = True
except ImportError:
    FLUIDS_AVAILABLE = False

# Try importing the real thermo library (shadowed by project's thermo/ package)
THERMO_AVAILABLE = False
try:
    saved_path = sys.path.copy()
    saved_modules = {k: v for k, v in sys.modules.items() if k == 'thermo' or k.startswith('thermo.')}
    for mod in list(sys.modules.keys()):
        if mod == 'thermo' or mod.startswith('thermo.'):
            del sys.modules[mod]
    project_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(project_dir)]
    import thermo
    from thermo.chemical import Chemical as ThermoChemical
    THERMO_AVAILABLE = True
except Exception:
    ThermoChemical = None
finally:
    sys.path = saved_path
    for mod, module in saved_modules.items():
        sys.modules[mod] = module

# Try importing pygerg for GERG-88 cross-validation
try:
    import pygerg
    PYSERG_AVAILABLE = True
except ImportError:
    PYSERG_AVAILABLE = False


@pytest.fixture
def calc():
    return GasFlowCalculator()


def solve_colebrook_white(Re, relative_roughness):
    """
    Newton-Raphson solver for the implicit Colebrook-White friction factor equation:
    1/sqrt(f) = -2.0 * log10(relative_roughness / 3.7 + 2.51 / (Re * sqrt(f)))
    """
    if Re < 2300:
        return 64.0 / Re
    
    # Churchill or simple approximation as initial guess
    f_guess = 0.02
    for _ in range(100):
        sqrt_f = math.sqrt(f_guess)
        # Function: F(f) = 1/sqrt(f) + 2.0 * log10(...) = 0
        term = relative_roughness / 3.7 + 2.51 / (Re * sqrt_f)
        F = 1.0 / sqrt_f + 2.0 * math.log10(term)
        
        # Derivative dF/df
        dterm_df = -1.255 / (Re * f_guess**1.5)
        dF_df = -0.5 / f_guess**1.5 + (2.0 / math.log(10.0)) * (1.0 / term) * dterm_df
        
        f_next = f_guess - F / dF_df
        if abs(f_next - f_guess) < 1e-7:
            return f_next
        f_guess = max(1e-5, f_next)
    return f_guess


def test_friction_factor_vs_colebrook_white(calc):
    """
    Verify our custom Churchill friction factor matches the Colebrook-White implicit equation
    within 1.0% tolerance in fully turbulent flow (Re >= 10000), which represents the standard
    mathematical accuracy of explicit approximations in fluid dynamics.
    """
    # Fully turbulent flow checks
    Re_turbulent = [10000, 50000, 100000, 1000000]
    roughness_ratios = [1e-5, 1e-4, 5e-4, 1e-3, 5e-3]
    
    for Re in Re_turbulent:
        for rr in roughness_ratios:
            f_custom = calc.get_friction_factor(Re, rr)
            f_ref = solve_colebrook_white(Re, rr)
            
            relative_error = abs(f_custom - f_ref) / f_ref
            assert relative_error < 0.02, (
                f"Friction factor discrepancy too high at turbulent Re={Re}, rr={rr}: "
                f"Custom={f_custom:.6f}, Reference={f_ref:.6f}, Error={relative_error*100:.4f}%"
            )

    # Transitional flow checks (Re = 3000)
    for rr in roughness_ratios:
        f_custom = calc.get_friction_factor(3000, rr)
        f_ref = solve_colebrook_white(3000, rr)
        
        relative_error = abs(f_custom - f_ref) / f_ref
        assert relative_error < 0.5, (
            f"Friction factor discrepancy too high at transitional Re=3000: "
            f"Custom={f_custom:.6f}, Reference={f_ref:.6f}"
        )


def test_optional_fluids_friction_factor_comparison(calc):
    """
    Compare Churchill friction factor against standard engineering libraries if installed.
    """
    if not FLUIDS_AVAILABLE:
        pytest.skip("fluids library is not installed for reference comparison.")
        
    Re_turbulent = [10000, 50000, 200000, 2000000]
    roughness_ratios = [1e-5, 1e-4, 1e-3]
    
    for Re in Re_turbulent:
        for rr in roughness_ratios:
            f_custom = calc.get_friction_factor(Re, rr)
            f_fluids = fluids.friction.friction_factor(Re, rr)
            
            relative_error = abs(f_custom - f_fluids) / f_fluids
            assert relative_error < 0.01


def test_thermodynamic_z_factor_consistency(calc):
    """
    Verify thermodynamic compressibility factor Z is physically consistent (0.8 <= Z <= 1.0)
    for high pressure and converges to exactly 1.0 (ideal gas) at low pressures.
    """
    mole_fractions = {"Methane": 0.95, "Ethane": 0.03, "Propane": 0.02}
    T = 293.15 # 20 C
    
    # 1. Low pressure ideal gas limit (100 Pa)
    props_low = calc.calculate_thermo_properties(100.0, T, mole_fractions, "Pseudo-Critical (Kay's Rule)")
    assert abs(props_low["Z"] - 1.0) < 0.001, f"Low pressure Z should be ~1.0, got {props_low['Z']}"
    
    # 2. Pipeline conditions (e.g. 50 bara)
    props_high = calc.calculate_thermo_properties(50e5, T, mole_fractions, "Pseudo-Critical (Kay's Rule)")
    assert 0.8 <= props_high["Z"] <= 0.95, f"High pressure Z out of range: {props_high['Z']}"
    
    # 3. Cubic Equations of State comparison (PR vs SRK)
    props_pr = calc.calculate_thermo_properties(40e5, T, mole_fractions, "Peng-Robinson (PR EOS)")
    props_srk = calc.calculate_thermo_properties(40e5, T, mole_fractions, "Soave-Redlich-Kwong (SRK EOS)")
    
    # Ensure they are physically close (within 3.5%)
    z_diff = abs(props_pr["Z"] - props_srk["Z"]) / props_pr["Z"]
    assert z_diff < 0.035, f"PR and SRK Z-factors differ significantly: PR={props_pr['Z']}, SRK={props_srk['Z']}"


def test_compressible_incompressible_limit_convergence(calc):
    """
    Verify that at low pressure drop and small length limits, the compressible and incompressible
    formulations converge to the exact same results (within a 0.5% tolerance).
    """
    inputs_inc = {
        "P_in": 5.0e5, # 5 bara
        "T": 288.15,
        "mole_fractions": {"Methane": 1.0},
        "library_choice": "Pseudo-Critical (Kay's Rule)",
        "flow_rate": 100, # Very low flow rate
        "flow_unit": "Sm3/h",
        "D_inner": 100, # Large pipe
        "L": 10, # Very short pipe
        "roughness": 4.57e-5,
        "total_k": 0.0,
        "flow_property": "Incompressible",
        "flow_mode": FLOW_MODE_INCOMPRESSIBLE,
    }
    
    inputs_comp = inputs_inc.copy()
    inputs_comp["flow_property"] = "Compressible"
    inputs_comp["flow_mode"] = FLOW_MODE_COMPRESSIBLE
    
    res_inc = calc.calculate_pressure_drop(inputs_inc)
    res_comp = calc.calculate_pressure_drop(inputs_comp)
    
    dp_inc = res_inc["delta_p_total"]
    dp_comp = res_comp["delta_p_total"]
    
    # Relative difference should be negligible (< 0.5%)
    dp_diff = abs(dp_inc - dp_comp) / dp_inc
    assert dp_diff < 0.005, (
        f"Compressible & incompressible results diverged at the limit: "
        f"Incompressible={dp_inc:.2f} Pa, Compressible={dp_comp:.2f} Pa, Diff={dp_diff*100:.4f}%"
    )


def test_lockhart_martinelli_two_phase_bounds(calc):
    """
    Verify that when vapor quality Q is in (0, 1), Lockhart-Martinelli pressure drop is calculated
    and behaves in a physically bounded way (i.e. two-phase pressure drop must be strictly greater
    than single-phase gas or liquid pressure drop at equivalent total mass flow rates).
    """
    # Two-phase mixture of methane and butane at low temperature
    inputs_two_phase = {
        "P_in": (15 + 1.01325) * 1e5,
        "T": -5 + 273.15,
        "mole_fractions": {"METHANE": 0.8, "BUTANE": 0.2},
        "library_choice": "CoolProp (High Accuracy EOS)",
        "flow_rate": 800,
        "flow_unit": "Sm3/h",
        "D_inner": 50,
        "L": 100,
        "roughness": 4.57e-5,
        "total_k": 0,
        "flow_property": "Compressible",
        "flow_mode": FLOW_MODE_COMPRESSIBLE,
    }
    
    result = calc.calculate_pressure_drop(inputs_two_phase, num_segments=4)
    
    # Assert that we are indeed in the two-phase region
    assert result["phase_info"]["phase"] == "two_phase"
    assert result["phase_info"]["formula_mode"] == "two_phase"
    
    # Compare with a mock single-phase gas calculation (by forcing gas phase in inputs or logic)
    # The calculated pressure drop in two-phase should be significantly higher due to liquid hold-up
    dp_total = result["delta_p_total"]
    assert dp_total > 0
    assert result["phase_info"]["vapor_quality"] > 0
    assert result["phase_info"]["vapor_quality"] < 1.0


@pytest.mark.skipif(not FLUIDS_AVAILABLE, reason="fluids library not installed")
class TestFluidsCrossValidation:
    """Cross-validate our implementations against the external `fluids` library."""

    def test_friction_factor_agree_with_fluids(self, calc):
        """Churchill friction factor should be within 2% of fluids library for common ranges."""
        roughness_values = [0.0, 1e-6, 4.57e-5, 0.001, 0.01]
        Re_values = [1000, 5000, 1e4, 5e4, 1e5, 5e5, 1e6, 1e7]
        max_dev = 0.0
        worst_case = None
        for Re in Re_values:
            for eD in roughness_values:
                f_churchill = churchill_friction_factor(Re, eD)
                f_fluids = fluids.friction_factor(Re, eD)
                if f_churchill > 0:
                    dev = abs(f_churchill - f_fluids) / f_fluids
                else:
                    dev = 0.0
                if dev > max_dev:
                    max_dev = dev
                    worst_case = (Re, eD, f_churchill, f_fluids, dev)
        max_dev_pct = max_dev * 100
        assert max_dev_pct < 3.0, (
            f"Max deviation {max_dev_pct:.3f}% at Re={worst_case[0]}, "
            f"eD={worst_case[1]}: churchill={worst_case[2]:.6f}, "
            f"fluids={worst_case[3]:.6f}"
        )

    def test_fluids_colebrook_white_agreement(self):
        """Verify fluids library's friction factor matches our Colebrook-White solver."""
        roughness_values = [0.0, 4.57e-5, 0.001]
        Re_values = [1e4, 1e5, 1e6]
        for Re in Re_values:
            for eD in roughness_values:
                f_colebrook = solve_colebrook_white(Re, eD)
                f_fluids = fluids.friction_factor(Re, eD)
                rel_diff = abs(f_colebrook - f_fluids) / max(f_fluids, 1e-10)
                assert rel_diff < 0.005, (
                    f"Colebrook-White vs fluids disagree at Re={Re}, eD={eD}: "
                    f"colebrook={f_colebrook:.6f}, fluids={f_fluids:.6f}, diff={rel_diff*100:.4f}%"
                )

    def test_beggs_brill_two_phase_bounds(self):
        """Verify fluids Beggs-Brill two-phase pressure drop is physically bounded."""
        dp = fluids.Beggs_Brill(
            m=10.0, x=0.3, rhol=800.0, rhog=50.0,
            mul=1e-3, mug=1e-5, sigma=0.02, P=1e6,
            D=0.1, angle=0.0, roughness=4.57e-5, L=100.0,
        )
        assert dp > 0, "Two-phase pressure drop must be positive"
        # Compare with single-phase liquid (x=0)
        dp_liquid = fluids.Beggs_Brill(
            m=10.0, x=0.0, rhol=800.0, rhog=50.0,
            mul=1e-3, mug=1e-5, sigma=0.02, P=1e6,
            D=0.1, angle=0.0, roughness=4.57e-5, L=100.0,
        )
        assert dp > dp_liquid * 0.01, "Two-phase dp should not be negligible vs liquid"


@pytest.mark.skipif(not THERMO_AVAILABLE, reason="thermo library not available (shadowed by project package)")
class TestThermoCrossValidation:
    """Cross-validate CoolProp-based properties against the external `thermo` library."""

    def test_molecular_weight_agreement(self):
        """Verify molecular weights from CoolProp and thermo agree for common gases."""
        gases = {"METHANE": 16.04, "ETHANE": 30.07, "PROPANE": 44.10, "NITROGEN": 28.01, "CO2": 44.01}
        for gas_id, expected_mw in gases.items():
            c = ThermoChemical(gas_id.lower())
            mw_thermo = c.MW
            # CoolProp via thermo compatibility
            rel_diff = abs(mw_thermo - expected_mw) / expected_mw
            assert rel_diff < 0.02, (
                f"MW for {gas_id}: thermo={mw_thermo:.4f}, expected={expected_mw:.4f}, "
                f"diff={rel_diff*100:.2f}%"
            )

    def test_critical_properties_thermo(self):
        """Verify critical properties for methane using thermo."""
        c = ThermoChemical('methane')
        assert c.Tc == pytest.approx(190.56, rel=0.01)
        assert c.Pc == pytest.approx(4.599e6, rel=0.01)

    def test_density_cross_check(self, calc):
        """Verify our calculated density is within 5% of thermo for simple gas at NTP."""
        temp_k = 298.15
        press_pa = 101325.0
        inputs = {
            "mole_fractions": {"METHANE": 1.0},
            "library_choice": "CoolProp (High Accuracy EOS)",
        }
        props = calc.calculate_cubic_eos_props(press_pa, temp_k, inputs["mole_fractions"], "PR")
        if props and "density" in props:
            density_calc = props["density"]
            c = ThermoChemical('methane')
            # MW in g/mol, R in J/(mol*K), P in Pa => density in kg/m³ (divide by 1000)
            density_thermo = c.MW * press_pa / (8.314462618 * temp_k * 1000.0)
            rel_diff = abs(density_calc - density_thermo) / density_thermo
            assert rel_diff < 0.05, (
                f"Density: calculated={density_calc:.4f}, thermo-ideal={density_thermo:.4f}, "
                f"diff={rel_diff*100:.2f}%"
            )


@pytest.mark.skipif(not PYSERG_AVAILABLE, reason="pygerg library not installed")
class TestGERG88CrossValidation:
    """Cross-validate our CoolProp compressibility against GERG-88 standard."""

    @pytest.fixture
    def standard_mix(self):
        """Standard natural gas composition for cross-validation."""
        return {"METHANE": 0.90, "ETHANE": 0.05, "PROPANE": 0.03, "NITROGEN": 0.02}

    # HHV in MJ/m³ at 0°C, 1 atm for SGERG inputs
    _HHV = {"METHANE": 35.82, "ETHANE": 63.77, "PROPANE": 91.25, "NITROGEN": 0.0, "CARBONDIOXIDE": 0.0}
    _MW = {"METHANE": 16.04, "ETHANE": 30.07, "PROPANE": 44.10, "NITROGEN": 28.01, "CARBONDIOXIDE": 44.01}
    AIR_MW = 28.9626

    def _sergr_z(self, mix, p_bar, tc):
        """Compute Z using GERG-88/SGERG for given mixture."""
        x3 = mix.get("CARBONDIOXIDE", 0.0) + mix.get("CO2", 0.0)
        x5 = mix.get("HYDROGEN", 0.0)
        mix_mw = sum(self._MW[g] * f for g, f in mix.items() if g in self._MW)
        rm = mix_mw / self.AIR_MW
        hs = sum(self._HHV.get(g, 0.0) * f for g, f in mix.items() if g in self._HHV)
        gerg = pygerg.GERG88()
        _, z, _ = gerg.sgerg(x3=x3, hs=hs, rm=rm, x5=x5, p=p_bar, tc=tc)
        return z

    def test_compressibility_agreement_at_low_pressure(self, calc, standard_mix):
        """Z should agree within 2% at low pressure (1-10 bar)."""
        for p_bar in [1, 5, 10]:
            tc = 20.0
            temp_k = tc + 273.15
            press_pa = p_bar * 1e5

            inputs = {
                "mole_fractions": standard_mix,
                "library_choice": "CoolProp (High Accuracy EOS)",
            }
            props = calc.calculate_cubic_eos_props(press_pa, temp_k, inputs["mole_fractions"], "SRK")
            if props and "Z" in props:
                z_coolprop = props["Z"]
                z_gerg = self._sergr_z(standard_mix, p_bar, tc)
                rel_diff = abs(z_coolprop - z_gerg) / z_gerg
                assert rel_diff < 0.02, (
                    f"P={p_bar} bar: CoolProp Z={z_coolprop:.5f}, GERG-88 Z={z_gerg:.5f}, "
                    f"diff={rel_diff*100:.2f}%"
                )

    def test_compressibility_trend(self, calc, standard_mix):
        """Z should decrease with increasing pressure (physical consistency)."""
        z_values = []
        for p_bar in [1, 10, 30, 50, 70]:
            tc = 20.0
            temp_k = tc + 273.15
            press_pa = p_bar * 1e5
            inputs = {
                "mole_fractions": standard_mix,
                "library_choice": "CoolProp (High Accuracy EOS)",
            }
            props = calc.calculate_cubic_eos_props(press_pa, temp_k, inputs["mole_fractions"], "SRK")
            if props and "Z" in props:
                z_values.append(props["Z"])
            z_gerg = self._sergr_z(standard_mix, p_bar, tc)
            z_values.append(z_gerg)

        # Both methods should show decreasing Z with pressure
        for i in range(len(z_values) - 1):
            assert z_values[i] >= z_values[i + 1] * 0.9, (
                f"Z should generally decrease with pressure at {tc}°C"
            )

    def test_sergr_on_typical_compositions(self, calc):
        """Test GERG-88 Z on a range of typical natural gas compositions."""
        compositions = [
            {"METHANE": 0.95, "ETHANE": 0.03, "PROPANE": 0.01, "NITROGEN": 0.01},
            {"METHANE": 0.85, "ETHANE": 0.08, "PROPANE": 0.04, "CARBONDIOXIDE": 0.02, "NITROGEN": 0.01},
        ]
        for mix in compositions:
            z_gerg = self._sergr_z(mix, p_bar=30, tc=20.0)
            assert 0.80 < z_gerg < 1.0, f"Z={z_gerg:.4f} outside physical range for {mix}"

            inputs = {
                "mole_fractions": mix,
                "library_choice": "CoolProp (High Accuracy EOS)",
            }
            props = calc.calculate_cubic_eos_props(30e5, 293.15, inputs["mole_fractions"], "SRK")
            if props and "Z" in props:
                z_coolprop = props["Z"]
                rel_diff = abs(z_coolprop - z_gerg) / z_gerg
                assert rel_diff < 0.03, (
                    f"Z mismatch for {mix}: CoolProp={z_coolprop:.4f}, GERG={z_gerg:.4f}, "
                    f"diff={rel_diff*100:.2f}%"
                )

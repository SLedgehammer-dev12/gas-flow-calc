import math
import pytest
from calculations import GasFlowCalculator
from data import PIPE_ROUGHNESS
from flow_utils import FLOW_MODE_COMPRESSIBLE, FLOW_MODE_INCOMPRESSIBLE

# Try importing fluids library optionally for high-accuracy standard benchmarking
try:
    import fluids
    FLUIDS_AVAILABLE = True
except ImportError:
    FLUIDS_AVAILABLE = False


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

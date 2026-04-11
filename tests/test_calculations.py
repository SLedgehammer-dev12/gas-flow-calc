import math

import pytest

from calculations import GasFlowCalculator
from data import PIPE_ROUGHNESS
from flow_utils import (
    FLOW_MODE_COMPRESSIBLE,
    FLOW_MODE_INCOMPRESSIBLE,
    normalize_flow_mode,
)


@pytest.fixture
def calc():
    return GasFlowCalculator()


@pytest.fixture
def common_inputs():
    return {
        "P_in": 1_000_000,
        "T": 300,
        "mole_fractions": {"Methane": 0.9, "Ethane": 0.1},
        "library_choice": "Pseudo-Critical (Kay's Rule)",
        "flow_rate": 1000,
        "flow_unit": "Sm3/h",
        "D_inner": 50,
        "L": 1000,
        "roughness": PIPE_ROUGHNESS.get("API 5L Grade B", 4.57e-5),
        "total_k": 0,
        "flow_property": "Incompressible",
        "flow_mode": FLOW_MODE_INCOMPRESSIBLE,
    }


def test_normalize_flow_mode_accepts_english_and_turkish_labels():
    assert normalize_flow_mode("Incompressible") == FLOW_MODE_INCOMPRESSIBLE
    assert normalize_flow_mode("Compressible") == FLOW_MODE_COMPRESSIBLE
    assert normalize_flow_mode("Sıkıştırılamaz") == FLOW_MODE_INCOMPRESSIBLE
    assert normalize_flow_mode("Sıkıştırılabilir") == FLOW_MODE_COMPRESSIBLE


def test_calculate_pressure_drop_incompressible(calc, common_inputs):
    result = calc.calculate_pressure_drop(common_inputs)
    assert result["flow_mode"] == FLOW_MODE_INCOMPRESSIBLE
    assert "P_out" in result
    assert result["P_out"] < common_inputs["P_in"]
    assert result["delta_p_total"] > 0
    assert result["velocity_out"] == result["velocity_in"]
    assert result["phase_info"]["formula_mode"] in {
        "single_phase_incompressible_gas",
        "single_phase_liquid",
    }


def test_calculate_pressure_drop_incompressible_with_english_label_only(calc, common_inputs):
    inputs = common_inputs.copy()
    inputs.pop("flow_mode")
    inputs["flow_property"] = "Incompressible"
    result = calc.calculate_pressure_drop(inputs)
    assert result["flow_mode"] == FLOW_MODE_INCOMPRESSIBLE
    assert result["velocity_out"] == result["velocity_in"]


def test_calculate_pressure_drop_compressible(calc, common_inputs):
    inputs = common_inputs.copy()
    inputs["flow_property"] = "Compressible"
    inputs["flow_mode"] = FLOW_MODE_COMPRESSIBLE
    result = calc.calculate_pressure_drop(inputs)
    assert result["flow_mode"] == FLOW_MODE_COMPRESSIBLE
    assert "P_out" in result
    assert result["P_out"] < inputs["P_in"]
    assert result["delta_p_total"] > 0
    assert result["velocity_out"] > result["velocity_in"]
    assert result["phase_profile"]


def test_calculate_max_length(calc, common_inputs):
    inputs = common_inputs.copy()
    inputs["P_out_target"] = 800000
    result = calc.calculate_max_length(inputs)
    assert "L_max" in result
    assert "error" not in result
    assert "phase_info" in result
    assert "gas_props_in" in result
    assert "gas_props_out" in result

    inputs["P_out_target"] = 1100000
    with pytest.raises(ValueError, match="Çıkış basıncı giriş basıncından büyük olamaz."):
        calc.calculate_max_length(inputs)


def test_calculate_min_diameter(calc, common_inputs):
    inputs = common_inputs.copy()
    inputs["max_velocity"] = 20
    inputs["P_design"] = 1000000
    inputs["material"] = "API 5L Grade B"
    inputs["SMYS"] = 241
    inputs["F"] = 0.72
    inputs["E"] = 1.0
    inputs["T_factor"] = 1.0
    inputs["target"] = "Minimum Çap"
    inputs["optimize_weight"] = False
    inputs["fast_calculation"] = True

    result = calc.calculate_min_diameter(inputs)
    assert "selected_pipe" in result
    assert "phase_info" in result
    if "error" not in result["selected_pipe"]:
        assert result["selected_pipe"]["nominal"] is not None


def test_detect_phase_for_gas_liquid_and_two_phase(calc):
    gas_phase = calc.detect_phase((10 + 1.01325) * 1e5, 25 + 273.15, {"METHANE": 1.0})
    dry_mix_gas = calc.detect_phase(
        (10 + 1.01325) * 1e5,
        25 + 273.15,
        {"METHANE": 0.95, "ETHANE": 0.03, "NITROGEN": 0.02},
    )
    liquid_phase = calc.detect_phase((10 + 1.01325) * 1e5, 15 + 273.15, {"PROPANE": 1.0})
    two_phase = calc.detect_phase((15 + 1.01325) * 1e5, -5 + 273.15, {"METHANE": 0.8, "BUTANE": 0.2})

    assert gas_phase["phase"] == "gas"
    assert dry_mix_gas["phase"] == "gas"
    assert liquid_phase["phase"] == "liquid"
    assert two_phase["phase"] == "two_phase"
    assert two_phase["vapor_quality"] is not None


def test_calculate_pressure_drop_two_phase_builds_phase_profile(calc):
    inputs = {
        "P_in": (15 + 1.01325) * 1e5,
        "T": -5 + 273.15,
        "mole_fractions": {"METHANE": 0.8, "BUTANE": 0.2},
        "library_choice": "CoolProp (High Accuracy EOS)",
        "flow_rate": 500,
        "flow_unit": "Sm3/h",
        "D_inner": 50,
        "L": 200,
        "roughness": PIPE_ROUGHNESS.get("API 5L Grade B", 4.57e-5),
        "total_k": 0,
        "flow_property": "Compressible",
        "flow_mode": FLOW_MODE_COMPRESSIBLE,
    }

    result = calc.calculate_pressure_drop(inputs, num_segments=8)
    assert result["phase_info"]["phase"] == "two_phase"
    assert result["phase_info"]["formula_mode"] == "two_phase"
    assert result["transition_to_two_phase_m"] == 0.0
    assert len(result["phase_profile"]) == 9


def test_calculate_pressure_drop_liquid_uses_phase_specific_model(calc):
    inputs = {
        "P_in": (10 + 1.01325) * 1e5,
        "T": 15 + 273.15,
        "mole_fractions": {"PROPANE": 1.0},
        "library_choice": "CoolProp (High Accuracy EOS)",
        "flow_rate": 1.5,
        "flow_unit": "kg/s",
        "D_inner": 25,
        "L": 20,
        "roughness": PIPE_ROUGHNESS.get("API 5L Grade B", 4.57e-5),
        "total_k": 1.0,
        "flow_property": "Compressible",
        "flow_mode": FLOW_MODE_COMPRESSIBLE,
    }

    result = calc.calculate_pressure_drop(inputs, num_segments=8)
    assert result["phase_profile"][0]["phase"] == "liquid"
    assert result["phase_info"]["phase"] == "liquid"
    assert result["phase_info"]["formula_mode"] == "single_phase_liquid"
    assert result["delta_p_total"] > 0
    assert math.isfinite(result["delta_p_acceleration"])
    assert result["gas_props_out"]["density"] > 0

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def calc():
    from calculations import GasFlowCalculator
    return GasFlowCalculator()


@pytest.fixture
def common_inputs():
    return dict(
        P_in=(20 + 1.01325) * 1e5,
        T=25 + 273.15,
        mole_fractions={"METHANE": 0.92, "ETHANE": 0.05, "PROPANE": 0.03},
        library_choice="CoolProp (High Accuracy EOS)",
        flow_rate=5000,
        flow_unit="Sm3/h",
        D_inner=100,
        L=5000,
        roughness=4.57e-5,
        total_k=2.5,
        flow_property="Compressible",
        flow_mode="compressible",
        target="pressure_drop",
        P_out_target=0,
        max_velocity=20,
        optimize_weight=False,
        fast_calculation=False,
        P_design=0,
        material="API 5L Grade B",
        SMYS=0,
        F=0.72,
        E=1.0,
        T_factor=1.0,
    )


@pytest.fixture
def high_pressure_inputs():
    return dict(
        P_in=(80 + 1.01325) * 1e5,
        T=60 + 273.15,
        mole_fractions={"METHANE": 0.90, "ETHANE": 0.06, "PROPANE": 0.03, "NITROGEN": 0.01},
        library_choice="CoolProp (High Accuracy EOS)",
        flow_rate=50000,
        flow_unit="Sm3/h",
        D_inner=150,
        L=10000,
        roughness=4.57e-5,
        total_k=2.5,
        flow_property="Compressible",
        flow_mode="compressible",
        target="pressure_drop",
        P_out_target=0,
        max_velocity=20,
        optimize_weight=False,
        fast_calculation=False,
        P_design=0,
        material="API 5L Grade B",
        SMYS=0,
        F=0.72,
        E=1.0,
        T_factor=1.0,
    )


@pytest.fixture
def temp_config_dir():
    with tempfile.TemporaryDirectory() as d:
        old_local = os.environ.get("LOCALAPPDATA")
        old_appdata = os.environ.get("APPDATA")
        os.environ["LOCALAPPDATA"] = d
        os.environ["APPDATA"] = d
        try:
            yield d
        finally:
            if old_local is not None:
                os.environ["LOCALAPPDATA"] = old_local
            else:
                os.environ.pop("LOCALAPPDATA", None)
            if old_appdata is not None:
                os.environ["APPDATA"] = old_appdata
            else:
                os.environ.pop("APPDATA", None)

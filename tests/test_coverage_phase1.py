import pytest
from pipe.selector import get_sorted_pipes, calculate_pipe_weight_api5l, nd_sort_key
from theme_colors import get_theme_colors, get_color, resolve_colors
from flow.utils import (
    churchill_friction_factor, single_phase_segment_loss,
    liquid_acceleration_loss, two_phase_segment_loss,
)


# ── pipe/selector.py ──────────────────────────────────────────────────────────

def test_get_sorted_pipes_returns_sorted_by_diameter():
    pipes = get_sorted_pipes(P_design_pa=1e6, SMYS_mpa=245, F=0.72, E=1.0, T=1.0)
    assert len(pipes) > 0
    for i in range(len(pipes) - 1):
        assert pipes[i]["D_inner_mm"] <= pipes[i + 1]["D_inner_mm"]


def test_get_sorted_pipes_high_pressure_filters():
    """Very high design pressure should require thicker walls."""
    pipes = get_sorted_pipes(P_design_pa=50e6, SMYS_mpa=245, F=0.72, E=1.0, T=1.0)
    for p in pipes:
        assert p["t_mm"] >= p["t_required_mm"]


def test_get_sorted_pipes_zero_pressure():
    pipes = get_sorted_pipes(P_design_pa=0, SMYS_mpa=245, F=0.72, E=1.0, T=1.0)
    assert len(pipes) > 0


def test_calculate_pipe_weight_api5l():
    """Weight for a typical pipe: Sch 40 6\" pipe (OD=168.28mm, t=7.11mm)."""
    weight = calculate_pipe_weight_api5l(168.28, 7.11)
    assert weight == pytest.approx(28.26, abs=0.5)


def test_calculate_pipe_weight_zero():
    assert calculate_pipe_weight_api5l(0, 0) == 0.0


def test_nd_sort_key_fractional():
    assert nd_sort_key('1/2"') == pytest.approx(0.5)
    assert nd_sort_key('1 1/2"') == pytest.approx(1.5)
    assert nd_sort_key('2"') == pytest.approx(2.0)
    assert nd_sort_key('12"') == pytest.approx(12.0)
    assert nd_sort_key('invalid"') == pytest.approx(999.0)
    assert nd_sort_key("") == pytest.approx(999.0)
    assert nd_sort_key('1 1/0"') == pytest.approx(999.0)   # ZeroDivisionError in space-separated branch
    assert nd_sort_key('x"') == pytest.approx(999.0)       # ValueError in else branch
    assert nd_sort_key('2 "') == 2.0                        # space branch, no fraction


# ── theme_colors.py ───────────────────────────────────────────────────────────

def test_get_theme_colors_returns_light_by_default():
    colors = get_theme_colors()
    assert "bg" in colors


def test_get_theme_colors_fallback_to_light():
    colors = get_theme_colors("nonexistent_theme")
    assert "bg" in colors


def test_get_color_returns_value():
    c = get_color("light", "accent")
    assert isinstance(c, str)
    assert c.startswith("#")


def test_get_color_fallback_default():
    c = get_color("light", "nonexistent_key", "#123456")
    assert c == "#123456"


def test_get_theme_colors_dark():
    colors = get_theme_colors("dark")
    assert colors.get("bg", "").startswith("#")


def test_resolve_colors_light():
    resolved = resolve_colors("light")
    assert "card_bg" in resolved
    assert "card_fg" in resolved
    assert "accent" in resolved


def test_resolve_colors_dark():
    resolved = resolve_colors("dark")
    assert isinstance(resolved["card_bg"], str)


# ── flow/utils.py ─────────────────────────────────────────────────────────────

def test_churchill_negative_re():
    f = churchill_friction_factor(-100, 0.0)
    assert f == 0.02


def test_churchill_negative_re_with_log():
    logs = []
    f = churchill_friction_factor(-1, 0.0, log_callback=lambda msg, **kw: logs.append(msg))
    assert f == 0.02
    assert len(logs) > 0


def test_single_phase_zero_density_with_log():
    logs = []
    result = single_phase_segment_loss(10, 0, 1e-5, 100, 0.1, 0.01, 0.0, 0, log_callback=lambda msg, **kw: logs.append(msg))
    assert result["dp_total"] == 0.0
    assert len(logs) >= 0


def test_single_phase_zero_velocity():
    result = single_phase_segment_loss(0, 1.2, 1e-5, 100, 0.1, 0.01, 0.0, 0)
    assert result["dp_total"] == 0.0


def test_single_phase_happy_path():
    result = single_phase_segment_loss(10, 50, 1e-5, 100, 0.1, 0.01, 0.0, 0)
    assert result["dp_total"] > 0
    assert result["Re"] > 0
    assert result["f"] > 0


def test_liquid_acceleration_loss_zero_area():
    assert liquid_acceleration_loss(10, 0, 50, 40) == 0.0


def test_liquid_acceleration_loss_zero_density():
    assert liquid_acceleration_loss(10, 0.01, 0, 40) == 0.0


def test_liquid_acceleration_loss_happy():
    loss = liquid_acceleration_loss(10, 0.01, 50, 40)
    assert loss > 0


def test_two_phase_segment_loss_all_branches():
    """Test all four C-coefficient branches in Lockhart-Martinelli."""
    D = 0.1
    area = 3.14159 * (D / 2) ** 2
    dL = 10
    roughness = 4.57e-5
    K_seg = 0

    base_props = {
        "rho_liquid": 800, "mu_liquid": 1e-3,
        "rho_vapor": 50, "mu_vapor": 1e-5,
    }

    branches = [
        # (quality_mass, m_dot, expected_C)
        (0.3, 0.001, 5),     # both laminar
        (0.3, 0.01, 12),     # liquid laminar, vapor turbulent
        (0.005, 0.2, 10),    # liquid turbulent, vapor laminar
        (0.3, 10.0, 20),     # both turbulent
    ]
    for q, m_dot, _ in branches:
        props = {**base_props, "quality_mass": q}
        result = two_phase_segment_loss(m_dot, dL, D, area, roughness, K_seg, props)
        assert result["dp_total"] > 0
        assert result["quality_mass"] == pytest.approx(max(min(q, 1.0 - 1e-6), 1e-6), abs=0.01)


def test_two_phase_segment_loss_quality_extremes():
    D = 0.1
    area = 3.14159 * (D / 2) ** 2
    props = {
        "rho_liquid": 800, "mu_liquid": 1e-3,
        "rho_vapor": 50, "mu_vapor": 1e-5,
        "quality_mass": 0.0, "ReL": 100, "ReV": 100,
    }
    result = two_phase_segment_loss(10, 10, D, area, 4.57e-5, 0, props)
    assert result["dp_total"] > 0
    assert result["quality_mass"] > 0  # clamped to 1e-6

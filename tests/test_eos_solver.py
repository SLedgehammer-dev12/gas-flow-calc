import math
import pytest
from eos.solver import solve_cubic


def test_solve_cubic_three_real_roots():
    """x^3 - 6x^2 + 11x - 6 = 0 should return roots 1, 2, 3."""
    roots = sorted(solve_cubic(-6, 11, -6))
    assert len(roots) == 3
    assert roots[0] == pytest.approx(1.0, abs=1e-10)
    assert roots[1] == pytest.approx(2.0, abs=1e-10)
    assert roots[2] == pytest.approx(3.0, abs=1e-10)


def test_solve_cubic_double_root():
    """x^3 - 3x + 2 = 0 should have double root at 1 and single at -2."""
    roots = sorted(solve_cubic(0, -3, 2))
    assert len(roots) == 3
    assert roots[0] == pytest.approx(-2.0, abs=1e-10)
    assert roots[1] == pytest.approx(1.0, abs=1e-10)
    assert roots[2] == pytest.approx(1.0, abs=1e-10)


def test_solve_cubic_single_real_root():
    """x^3 - 2x^2 + 2x - 2 = 0 should have one real root (discriminant > 0)."""
    roots = solve_cubic(-2, 2, -2)
    assert len(roots) == 3
    assert all(r == pytest.approx(roots[0], abs=1e-10) for r in roots)


def test_solve_cubic_zero_coefficient():
    """x^3 - 1 = 0 should return root at 1 (triple)."""
    roots = solve_cubic(0, 0, -1)
    assert len(roots) == 3
    assert roots[0] == pytest.approx(1.0, abs=1e-10)


def test_solve_cubic_negative_discriminant_boundary():
    """Very small negative discriminant should still produce three roots."""
    roots = solve_cubic(-3, 3, -1)
    assert len(roots) == 3

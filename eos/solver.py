import math

def solve_cubic(a2, a1, a0):
    """Cubic equation solver using closed-form Cardano method."""
    p = (3.0 * a1 - a2 * a2) / 3.0
    q = (2.0 * a2 * a2 * a2 - 9.0 * a2 * a1 + 27.0 * a0) / 27.0
    discriminant = (q / 2.0) ** 2 + (p / 3.0) ** 3
    three = 3.0
    offset = a2 / three

    def _cube_root(val):
        if val < 0:
            return -((-val) ** (1.0 / 3.0))
        return val ** (1.0 / 3.0)

    if discriminant > 0:
        u = _cube_root(-q / 2.0 + math.sqrt(discriminant))
        v = _cube_root(-q / 2.0 - math.sqrt(discriminant))
        r0 = u + v - offset
        return [r0, r0, r0]
    elif discriminant == 0:
        u = _cube_root(-q / 2.0)
        r0 = 2.0 * u - offset
        r1 = -u - offset
        return [r0, r1, r1]
    else:
        phi = math.acos(-q / 2.0 / math.sqrt(-(p / three) ** 3))
        two_sqrt = 2.0 * math.sqrt(-p / three)
        r0 = two_sqrt * math.cos(phi / three) - offset
        r1 = two_sqrt * math.cos((phi + 2.0 * math.pi) / three) - offset
        r2 = two_sqrt * math.cos((phi + 4.0 * math.pi) / three) - offset
        return [r0, r1, r2]

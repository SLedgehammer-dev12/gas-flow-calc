from data import ASME_B36_10M_DATA, PIPE_MATERIALS


def get_sorted_pipes(P_design_pa, SMYS_mpa, F, E, T):
    """Get sorted list of ASME B36.10M pipes that satisfy design requirements."""
    SMYS = SMYS_mpa * 1e6
    all_pipes = []
    for nominal, data in ASME_B36_10M_DATA.items():
        OD = data["OD_mm"]
        t_required = (P_design_pa * (OD / 1000)) / (2 * SMYS * F * E * T) * 1000
        for schedule, t in data["schedules"].items():
            D_inner = OD - 2 * t
            if t >= t_required:
                all_pipes.append({
                    "nominal": nominal, "OD_mm": OD, "schedule": schedule, "t_mm": t,
                    "D_inner_mm": D_inner, "t_required_mm": t_required,
                })

    all_pipes.sort(key=lambda p: p["D_inner_mm"])
    return all_pipes


def calculate_pipe_weight_api5l(D_mm, t_mm):
    return t_mm * (D_mm - t_mm) * 0.02466


def nd_sort_key(nd_str):
    try:
        s = nd_str.strip().replace('"', '')
        if ' ' in s:
            parts = s.split(' ')
            val = float(parts[0])
            if '/' in parts[1]:
                num, den = map(float, parts[1].split('/'))
                val += num / den
        elif '/' in s:
            num, den = map(float, s.split('/'))
            val = num / den
        else:
            val = float(s)
    except (ValueError, IndexError, ZeroDivisionError):
        val = 999.0
    return val

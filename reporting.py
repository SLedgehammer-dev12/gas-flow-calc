from translations import t
from data import COOLPROP_GASES
from format_utils import safe_format, safe_number, safe_text

_GAS_LOOKUP = {
    v["id"].casefold(): v["name"] for v in COOLPROP_GASES.values()
}
for k, v in COOLPROP_GASES.items():
    _GAS_LOOKUP[k.casefold()] = v["name"]
    _GAS_LOOKUP[v["name"].casefold()] = v["name"]


def _format_phase_section(result):
    phase_info = result.get("phase_info")
    if not phase_info:
        return ""

    title = (
        t("report_phase_section_warn")
        if phase_info.get("warning_level") in {"warning", "critical"}
        else t("report_phase_section")
    )

    lines = [title, f"{t('label_fluid_phase')}: {safe_text(phase_info.get('phase_label_tr', '-'))}"]
    vapor_quality = phase_info.get("vapor_quality")
    if vapor_quality is not None:
        lines.append(f"{t('label_vapor_quality')}: {safe_format(vapor_quality, '.3f')}")
    formula_label = phase_info.get("formula_label_tr")
    if formula_label:
        lines.append(f"{t('label_formula_set')}: {safe_text(formula_label)}")
    transition_distance = phase_info.get("transition_to_two_phase_m")
    if transition_distance is not None:
        lines.append(f"{t('label_two_phase_transition')}: {safe_format(transition_distance, '.2f')} m")
    warning_msg = phase_info.get("warning_msg_tr")
    if warning_msg:
        lines.append(f"{t('label_warning')}: {safe_text(warning_msg)}")
    return "\n".join(lines) + "\n\n"


def _component_label(component_id):
    key = str(component_id).strip().casefold()
    name = _GAS_LOOKUP.get(key)
    if name:
        return safe_text(name)
    return safe_text(component_id)


def _format_composition_section(inputs):
    mole_fractions = inputs.get("mole_fractions") or {}
    if not mole_fractions:
        return ""

    items = sorted(mole_fractions.items(), key=lambda item: item[1], reverse=True)
    lines = [t("report_composition_section")]
    for gas, fraction in items:
        lines.append(f"{_component_label(gas)}: {safe_format(100.0 * safe_number(fraction, 0.0), '.3f')} mol %")
    return "\n".join(lines) + "\n\n"


def _format_property_section(title, pressure_pa, temperature_k, props):
    if not props:
        return ""

    temperature_c = safe_number(temperature_k, 0.0) - 273.15
    lines = [
        title,
        f"{t('label_pressure_bara')}: {safe_format(safe_number(pressure_pa, 0.0) / 1e5, '.4f')}",
        f"{t('label_temperature')}: {safe_format(temperature_k, '.2f')} K ({safe_format(temperature_c, '.2f')} C)",
        f"{t('label_density')}: {safe_format(props.get('density'), '.4f')} {t('unit_kg_m3')}",
        f"{t('label_standard_density')}: {safe_format(props.get('standard_density'), '.4f')} {t('unit_kg_m3')}",
        f"{t('label_molecular_weight')}: {safe_format(props.get('MW'), '.4f')} {t('unit_kg_kmol')}",
        f"{t('label_viscosity')}: {safe_format(props.get('viscosity'), '.6e')} {t('unit_pa_s')}",
        f"{t('label_compressibility')}: {safe_format(props.get('Z'), '.5f')}",
        f"{t('label_cp')}: {safe_format(props.get('Cp'), '.4f')} {t('unit_kj_kgk')}",
        f"{t('label_cv')}: {safe_format(props.get('Cv'), '.4f')} {t('unit_kj_kgk')}",
        f"{t('label_sonic_velocity')}: {safe_format(props.get('sonic_velocity'), '.3f')} m/s",
    ]

    if props.get("viscosity_fallback"):
        lines.append(t("label_note_viscosity_fallback"))
    if props.get("thermo_fallback"):
        reason = props.get("fallback_reason")
        if reason:
            lines.append(t("label_note_thermo_fallback_reason").format(reason=safe_text(reason)))
        else:
            lines.append(t("label_note_thermo_fallback"))

    return "\n".join(lines) + "\n\n"


def _format_fluid_sections(inputs, result):
    sections = [_format_composition_section(inputs)]
    sections.append(
        _format_property_section(
            t("report_props_inlet"),
            inputs.get("P_in"),
            inputs.get("T"),
            result.get("gas_props_in"),
        )
    )

    gas_props_out = result.get("gas_props_out")
    if gas_props_out:
        sections.append(
            _format_property_section(
                t("report_props_outlet"),
                result.get("P_out", inputs.get("P_in")),
                inputs.get("T"),
                gas_props_out,
            )
        )

    return "".join(section for section in sections if section)


def format_pressure_drop_report(inputs, result):
    report = t("report_title") + "\n"
    report += t("report_target_pressure_drop") + "\n"
    report += _format_phase_section(result)
    report += f"{t('label_inlet_pressure')}: {safe_format((safe_number(inputs['P_in'], 0.0) / 1e5), '.4f')} {t('label_pressure_bara')}\n"
    report += f"{t('label_outlet_pressure')}: {safe_format((safe_number(result['P_out'], 0.0) / 1e5), '.4f')} {t('label_pressure_bara')}\n"
    report += f"{t('label_total_pressure_drop')}: {safe_format((safe_number(result['delta_p_total'], 0.0) / 1e5), '.4f')} {t('label_pressure_bar')}\n"
    report += f"  - {t('label_pipe_loss')}: {safe_format((safe_number(result['delta_p_pipe'], 0.0) / 1e5), '.4f')} {t('label_pressure_bar')}\n"
    report += f"  - {t('label_fitting_loss')}: {safe_format((safe_number(result['delta_p_fittings'], 0.0) / 1e5), '.4f')} {t('label_pressure_bar')}\n"
    if safe_number(result.get("delta_p_acceleration")) is not None:
        report += f"  - {t('label_accel_term')}: {safe_format((safe_number(result.get('delta_p_acceleration'), 0.0) / 1e5), '.4f')} {t('label_pressure_bar')}\n"
    report += "\n"
    report += f"{t('label_inlet_velocity')}: {safe_format(result['velocity_in'], '.2f')} {t('label_velocity_ms')}\n"
    report += f"{t('label_outlet_velocity')}: {safe_format(result['velocity_out'], '.2f')} {t('label_velocity_ms')}\n"
    report += f"{t('label_reynolds')}: {safe_format(result['Re'], '.0f')}\n"
    report += f"{t('label_friction_factor')}: {safe_format(result['f'], '.5f')}\n\n"
    report += _format_fluid_sections(inputs, result)
    return report


def format_max_length_report(inputs, result):
    report = t("report_title") + "\n"
    report += t("report_target_max_length") + "\n"
    report += _format_phase_section(result)
    if "error" in result:
        report += f"{t('label_error')}: {safe_text(result['error'])}\n\n"
    else:
        report += f"{t('label_max_length')}: {safe_format(result['L_max'], '.2f')} m\n"
        report += f"{t('label_reynolds')}: {safe_format(result['Re'], '.0f')}\n"
        report += f"{t('label_pipe_loss')}: {safe_format((safe_number(result.get('delta_p_pipe'), 0.0) / 1e5), '.4f')} {t('label_pressure_bar')}\n"
        report += f"{t('label_fitting_loss')}: {safe_format((safe_number(result.get('delta_p_fittings'), 0.0) / 1e5), '.4f')} {t('label_pressure_bar')}\n"
        if safe_number(result.get("delta_p_acceleration")) is not None:
            report += f"{t('label_accel_term')}: {safe_format((safe_number(result.get('delta_p_acceleration'), 0.0) / 1e5), '.4f')} {t('label_pressure_bar')}\n"
        report += f"{t('label_inlet_velocity')}: {safe_format(result.get('velocity_in'), '.2f')} {t('label_velocity_ms')}\n"
        report += f"{t('label_outlet_velocity')}: {safe_format(result.get('velocity_out'), '.2f')} {t('label_velocity_ms')}\n"
        report += f"{t('label_outlet_pressure')}: {safe_format((safe_number(result.get('P_out'), 0.0) / 1e5), '.4f')} {t('label_pressure_bara')}\n"
        report += f"{t('label_friction_factor')}: {safe_format(result.get('f'), '.5f')}\n\n"
    report += _format_fluid_sections(inputs, result)
    return report


def format_min_diameter_report(inputs, result):
    report = t("report_title") + "\n"
    report += t("report_target_min_diameter") + "\n"
    report += _format_phase_section(result)
    report += f"{t('label_max_velocity_limit')}: {safe_format(result['max_vel'], '.2f')} m/s\n"
    report += f"{t('label_min_diameter_required')}: {safe_format(result['D_min_inner_mm'], '.2f')} {t('unit_mm')}\n"
    report += f"{t('label_actual_flow_rate')}: {safe_format(result['flow_rate_actual'], '.4f')} m3/s\n\n"

    if not result["selected_pipe"]:
        report += t("label_no_suitable_pipe") + "\n\n"
        report += _format_fluid_sections(inputs, result)
        return report

    pipe = result["selected_pipe"]
    report += t("report_selected_pipe") + "\n"
    report += f'{t("label_nominal_diameter")}: {safe_text(pipe["nominal"])}"\n'
    report += f'{t("label_schedule")}: {safe_text(pipe["schedule"])}\n'
    report += f'{t("label_outer_diameter")}: {safe_format(pipe["OD_mm"], ".2f")} {t("unit_mm")}\n'
    report += f'{t("label_wall_thickness")}: {safe_format(pipe["t_mm"], ".2f")} {t("unit_mm")}\n'
    report += f'{t("label_inner_diameter")}: {safe_format(pipe["D_inner_mm"], ".2f")} {t("unit_mm")}\n'
    report += f'{t("label_required_wall_thickness")}: {safe_format(pipe["t_required_mm"], ".2f")} {t("unit_mm")}\n\n'

    report += t("report_performance") + "\n"
    report += f'{t("label_inlet_velocity")}: {safe_format(result["velocity_in"], ".2f")} {t("label_velocity_ms")}\n'
    report += f'{t("label_outlet_velocity")}: {safe_format(result["velocity_out"], ".2f")} {t("label_velocity_ms")}\n'
    report += f'{t("label_outlet_pressure")}: {safe_format((safe_number(result["P_out"], 0.0) / 1e5), ".4f")} {t("label_pressure_bara")}\n'
    report += f'{t("label_status")}: {safe_text(result["velocity_status"])}\n\n'
    report += _format_fluid_sections(inputs, result)

    alternatives = result.get("alternatives") or {}
    if not alternatives:
        return report

    report += t("report_alternatives") + "\n"

    if "thinner" in alternatives:
        alt = alternatives["thinner"]
        pipe = alt["pipe"]
        alt_result = alt["result"]
        report += f'\n[1] {safe_text(alt["note"])}:\n'
        report += f'   {t("label_nominal_diameter")}: {safe_text(pipe["nominal"])}" {safe_text(pipe["schedule"])} (ID: {safe_format(pipe["D_inner_mm"], ".2f")} {t("unit_mm")})\n'
        report += f'   {t("alt_outlet_velocity")}: {safe_format(alt_result["velocity_out"], ".2f")} {t("label_velocity_ms")}\n'
        report += f'   {t("alt_outlet_pressure")}: {safe_format((safe_number(alt_result["P_out"], 0.0) / 1e5), ".4f")} {t("label_pressure_bara")}\n'

    if "thicker" in alternatives:
        alt = alternatives["thicker"]
        pipe = alt["pipe"]
        alt_result = alt["result"]
        report += f'\n[2] {safe_text(alt["note"])}:\n'
        report += f'   {t("label_nominal_diameter")}: {safe_text(pipe["nominal"])}" {safe_text(pipe["schedule"])} (ID: {safe_format(pipe["D_inner_mm"], ".2f")} {t("unit_mm")})\n'
        report += f'   {t("alt_outlet_velocity")}: {safe_format(alt_result["velocity_out"], ".2f")} {t("label_velocity_ms")}\n'
        report += f'   {t("alt_outlet_pressure")}: {safe_format((safe_number(alt_result["P_out"], 0.0) / 1e5), ".4f")} {t("label_pressure_bara")}\n'

    if "lowest_weight" in alternatives:
        alt = alternatives["lowest_weight"]
        pipe = alt["pipe"]
        alt_result = alt["result"]
        report += f'\n[*] {safe_text(alt["note"])}:\n'
        report += f'   {t("label_nominal_diameter")}: {safe_text(pipe["nominal"])}" {safe_text(pipe["schedule"])} (ID: {safe_format(pipe["D_inner_mm"], ".2f")} {t("unit_mm")})\n'
        report += f'   {t("alt_unit_weight")}: {safe_format(pipe.get("weight_per_m", 0), ".2f")} kg/m\n'
        report += f'   {t("alt_outlet_velocity")}: {safe_format(alt_result["velocity_out"], ".2f")} {t("label_velocity_ms")}\n'
        report += f'   {t("alt_outlet_pressure")}: {safe_format((safe_number(alt_result["P_out"], 0.0) / 1e5), ".4f")} {t("label_pressure_bara")}\n'

    return report

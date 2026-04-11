from data import COOLPROP_GASES
from format_utils import safe_format, safe_number, safe_text


def _format_phase_section(result):
    phase_info = result.get("phase_info")
    if not phase_info:
        return ""

    title = "=== FAZ DURUMU ==="
    if phase_info.get("warning_level") in {"warning", "critical"}:
        title = "=== FAZ DURUMU [UYARI] ==="

    lines = [title, f"Akiskan Fazi: {safe_text(phase_info.get('phase_label_tr', '-'))}"]
    vapor_quality = phase_info.get("vapor_quality")
    if vapor_quality is not None:
        lines.append(f"Buhar Kalitesi (Q): {safe_format(vapor_quality, '.3f')}")
    formula_label = phase_info.get("formula_label_tr")
    if formula_label:
        lines.append(f"Kullanilan Formul Seti: {safe_text(formula_label)}")
    transition_distance = phase_info.get("transition_to_two_phase_m")
    if transition_distance is not None:
        lines.append(f"Iki Faz Gecis Mesafesi: {safe_format(transition_distance, '.2f')} m")
    warning_msg = phase_info.get("warning_msg_tr")
    if warning_msg:
        lines.append(f"Uyari: {safe_text(warning_msg)}")
    return "\n".join(lines) + "\n\n"


def _component_label(component_id):
    entry = COOLPROP_GASES.get(str(component_id).strip())
    if entry:
        return safe_text(entry.get("name") or entry.get("id") or component_id)
    return safe_text(component_id)


def _format_composition_section(inputs):
    mole_fractions = inputs.get("mole_fractions") or {}
    if not mole_fractions:
        return ""

    items = sorted(mole_fractions.items(), key=lambda item: item[1], reverse=True)
    lines = ["=== GIRILEN KOMPOZISYON ==="]
    for gas, fraction in items:
        lines.append(f"{_component_label(gas)}: {safe_format(100.0 * safe_number(fraction, 0.0), '.3f')} mol %")
    return "\n".join(lines) + "\n\n"


def _format_property_section(title, pressure_pa, temperature_k, props):
    if not props:
        return ""

    temperature_c = safe_number(temperature_k, 0.0) - 273.15
    lines = [
        title,
        f"Basinc: {safe_format(safe_number(pressure_pa, 0.0) / 1e5, '.4f')} bara",
        f"Sicaklik: {safe_format(temperature_k, '.2f')} K ({safe_format(temperature_c, '.2f')} C)",
        f"Yogunluk: {safe_format(props.get('density'), '.4f')} kg/m3",
        f"Standart Yogunluk: {safe_format(props.get('standard_density'), '.4f')} kg/m3",
        f"Molekuler Agirlik: {safe_format(props.get('MW'), '.4f')} kg/kmol",
        f"Viskozite: {safe_format(props.get('viscosity'), '.6e')} Pa.s",
        f"Sikistirilabilirlik Faktoru (Z): {safe_format(props.get('Z'), '.5f')}",
        f"Cp: {safe_format(props.get('Cp'), '.4f')} kJ/kg.K",
        f"Cv: {safe_format(props.get('Cv'), '.4f')} kJ/kg.K",
        f"Ses Hizi: {safe_format(props.get('sonic_velocity'), '.3f')} m/s",
    ]

    if props.get("viscosity_fallback"):
        lines.append("Not: Viskozite degeri fallback tahmininden alindi.")
    if props.get("thermo_fallback"):
        reason = props.get("fallback_reason")
        if reason:
            lines.append(f"Not: Termodinamik fallback kullanildi ({safe_text(reason)}).")
        else:
            lines.append("Not: Termodinamik fallback kullanildi.")

    return "\n".join(lines) + "\n\n"


def _format_fluid_sections(inputs, result):
    sections = [_format_composition_section(inputs)]
    sections.append(
        _format_property_section(
            "=== AKISKAN OZELLIKLERI (GIRIS PT) ===",
            inputs.get("P_in"),
            inputs.get("T"),
            result.get("gas_props_in"),
        )
    )

    gas_props_out = result.get("gas_props_out")
    if gas_props_out:
        sections.append(
            _format_property_section(
                "=== AKISKAN OZELLIKLERI (CIKIS PT) ===",
                result.get("P_out", inputs.get("P_in")),
                inputs.get("T"),
                gas_props_out,
            )
        )

    return "".join(section for section in sections if section)


def format_pressure_drop_report(inputs, result):
    report = "=== HESAPLAMA SONUCU ===\n"
    report += "Hedef: Cikis Basinci\n"
    report += _format_phase_section(result)
    report += f"Giris Basinci: {safe_format((safe_number(inputs['P_in'], 0.0) / 1e5), '.4f')} bara\n"
    report += f"Cikis Basinci: {safe_format((safe_number(result['P_out'], 0.0) / 1e5), '.4f')} bara\n"
    report += f"Toplam Basinc Kaybi: {safe_format((safe_number(result['delta_p_total'], 0.0) / 1e5), '.4f')} bar\n"
    report += f"  - Boru Kaybi: {safe_format((safe_number(result['delta_p_pipe'], 0.0) / 1e5), '.4f')} bar\n"
    report += f"  - Fitting Kaybi: {safe_format((safe_number(result['delta_p_fittings'], 0.0) / 1e5), '.4f')} bar\n"
    if safe_number(result.get("delta_p_acceleration")) is not None:
        report += f"  - Ivmelenme Terimi: {safe_format((safe_number(result.get('delta_p_acceleration'), 0.0) / 1e5), '.4f')} bar\n"
    report += "\n"
    report += f"Akis Hizi (Giris): {safe_format(result['velocity_in'], '.2f')} m/s\n"
    report += f"Akis Hizi (Cikis): {safe_format(result['velocity_out'], '.2f')} m/s\n"
    report += f"Reynolds: {safe_format(result['Re'], '.0f')}\n"
    report += f"Surtunme Faktoru (f): {safe_format(result['f'], '.5f')}\n\n"
    report += _format_fluid_sections(inputs, result)
    return report


def format_max_length_report(inputs, result):
    report = "=== HESAPLAMA SONUCU ===\n"
    report += "Hedef: Maksimum Uzunluk\n"
    report += _format_phase_section(result)
    if "error" in result:
        report += f"HATA: {safe_text(result['error'])}\n\n"
    else:
        report += f"Maksimum Uzunluk: {safe_format(result['L_max'], '.2f')} m\n"
        report += f"Reynolds: {safe_format(result['Re'], '.0f')}\n"
        report += f"Boru Kaybi: {safe_format((safe_number(result.get('delta_p_pipe'), 0.0) / 1e5), '.4f')} bar\n"
        report += f"Fitting Kaybi: {safe_format((safe_number(result.get('delta_p_fittings'), 0.0) / 1e5), '.4f')} bar\n"
        if safe_number(result.get("delta_p_acceleration")) is not None:
            report += f"Ivmelenme Terimi: {safe_format((safe_number(result.get('delta_p_acceleration'), 0.0) / 1e5), '.4f')} bar\n"
        report += "\n"
    report += _format_fluid_sections(inputs, result)
    return report


def format_min_diameter_report(inputs, result):
    report = "=== HESAPLAMA SONUCU ===\n"
    report += "Hedef: Minimum Cap Secimi\n"
    report += _format_phase_section(result)
    report += f"Maksimum Hiz Limiti: {safe_format(result['max_vel'], '.2f')} m/s\n"
    report += f"Gerekli Min. Ic Cap (Tahmini): {safe_format(result['D_min_inner_mm'], '.2f')} mm\n"
    report += f"Gercek Akis Hizi (Giris): {safe_format(result['flow_rate_actual'], '.4f')} m3/s\n\n"

    if not result["selected_pipe"]:
        report += "UYARI: Kriterlere uygun standart boru bulunamadi!\n\n"
        report += _format_fluid_sections(inputs, result)
        return report

    pipe = result["selected_pipe"]
    report += "=== SECILEN BORU (ASME B36.10M) ===\n"
    report += f'Nominal Cap: {safe_text(pipe["nominal"])}"\n'
    report += f'Schedule: {safe_text(pipe["schedule"])}\n'
    report += f'Dis Cap: {safe_format(pipe["OD_mm"], ".2f")} mm\n'
    report += f'Et Kalinligi: {safe_format(pipe["t_mm"], ".2f")} mm\n'
    report += f'Ic Cap: {safe_format(pipe["D_inner_mm"], ".2f")} mm\n'
    report += f'Gerekli Et Kalinligi (Mukavemet): {safe_format(pipe["t_required_mm"], ".2f")} mm\n\n'

    report += "=== PERFORMANS (SECILEN) ===\n"
    report += f'Giris Hizi: {safe_format(result["velocity_in"], ".2f")} m/s\n'
    report += f'Cikis Hizi: {safe_format(result["velocity_out"], ".2f")} m/s\n'
    report += f'Cikis Basinci: {safe_format((safe_number(result["P_out"], 0.0) / 1e5), ".4f")} bara\n'
    report += f'Durum: {safe_text(result["velocity_status"])}\n\n'
    report += _format_fluid_sections(inputs, result)

    alternatives = result.get("alternatives") or {}
    if not alternatives:
        return report

    report += "=== ALTERNATIF SENARYOLAR ===\n"

    if "thinner" in alternatives:
        alt = alternatives["thinner"]
        pipe = alt["pipe"]
        alt_result = alt["result"]
        report += f'\n[1] {safe_text(alt["note"])}:\n'
        report += f'   Boru: {safe_text(pipe["nominal"])}" {safe_text(pipe["schedule"])} (ID: {safe_format(pipe["D_inner_mm"], ".2f")} mm)\n'
        report += f'   Cikis Hizi: {safe_format(alt_result["velocity_out"], ".2f")} m/s\n'
        report += f'   Cikis Basinci: {safe_format((safe_number(alt_result["P_out"], 0.0) / 1e5), ".4f")} bara\n'

    if "thicker" in alternatives:
        alt = alternatives["thicker"]
        pipe = alt["pipe"]
        alt_result = alt["result"]
        report += f'\n[2] {safe_text(alt["note"])}:\n'
        report += f'   Boru: {safe_text(pipe["nominal"])}" {safe_text(pipe["schedule"])} (ID: {safe_format(pipe["D_inner_mm"], ".2f")} mm)\n'
        report += f'   Cikis Hizi: {safe_format(alt_result["velocity_out"], ".2f")} m/s\n'
        report += f'   Cikis Basinci: {safe_format((safe_number(alt_result["P_out"], 0.0) / 1e5), ".4f")} bara\n'

    if "lowest_weight" in alternatives:
        alt = alternatives["lowest_weight"]
        pipe = alt["pipe"]
        alt_result = alt["result"]
        report += f'\n[*] {safe_text(alt["note"])}:\n'
        report += f'   Boru: {safe_text(pipe["nominal"])}" {safe_text(pipe["schedule"])} (ID: {safe_format(pipe["D_inner_mm"], ".2f")} mm)\n'
        report += f'   Birim Agirlik: {safe_format(pipe.get("weight_per_m", 0), ".2f")} kg/m\n'
        report += f'   Cikis Hizi: {safe_format(alt_result["velocity_out"], ".2f")} m/s\n'
        report += f'   Cikis Basinci: {safe_format((safe_number(alt_result["P_out"], 0.0) / 1e5), ".4f")} bara\n'

    return report

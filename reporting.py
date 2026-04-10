def format_pressure_drop_report(inputs, result):
    report = "=== HESAPLAMA SONUCU ===\n"
    report += "Hedef: Cikis Basinci\n"
    report += f"Giris Basinci: {inputs['P_in']/1e5:.4f} bara\n"
    report += f"Cikis Basinci: {result['P_out']/1e5:.4f} bara\n"
    report += f"Toplam Basinc Kaybi: {result['delta_p_total']/1e5:.4f} bar\n"
    report += f"  - Boru Kaybi: {result['delta_p_pipe']/1e5:.4f} bar\n"
    report += f"  - Fitting Kaybi: {result['delta_p_fittings']/1e5:.4f} bar\n\n"
    report += f"Akis Hizi (Giris): {result['velocity_in']:.2f} m/s\n"
    report += f"Akis Hizi (Cikis): {result['velocity_out']:.2f} m/s\n"
    report += f"Reynolds: {result['Re']:.0f}\n"
    report += f"Surtunme Faktoru (f): {result['f']:.5f}\n"
    return report


def format_max_length_report(inputs, result):
    report = "=== HESAPLAMA SONUCU ===\n"
    report += "Hedef: Maksimum Uzunluk\n"
    if "error" in result:
        report += f"HATA: {result['error']}\n"
    else:
        report += f"Maksimum Uzunluk: {result['L_max']:.2f} m\n"
        report += f"Reynolds: {result['Re']:.0f}\n"
    return report


def format_min_diameter_report(inputs, result):
    report = "=== HESAPLAMA SONUCU ===\n"
    report += "Hedef: Minimum Cap Secimi\n"
    report += f"Maksimum Hiz Limiti: {result['max_vel']:.2f} m/s\n"
    report += f"Gerekli Min. Ic Cap (Tahmini): {result['D_min_inner_mm']:.2f} mm\n"
    report += f"Gercek Akis Hizi (Giris): {result['flow_rate_actual']:.4f} m3/s\n\n"

    if not result["selected_pipe"]:
        report += "UYARI: Kriterlere uygun standart boru bulunamadi!\n"
        return report

    pipe = result["selected_pipe"]
    report += "=== SECILEN BORU (ASME B36.10M) ===\n"
    report += f'Nominal Cap: {pipe["nominal"]}"\n'
    report += f'Schedule: {pipe["schedule"]}\n'
    report += f'Dis Cap: {pipe["OD_mm"]:.2f} mm\n'
    report += f'Et Kalinligi: {pipe["t_mm"]:.2f} mm\n'
    report += f'Ic Cap: {pipe["D_inner_mm"]:.2f} mm\n'
    report += f'Gerekli Et Kalinligi (Mukavemet): {pipe["t_required_mm"]:.2f} mm\n\n'

    report += "=== PERFORMANS (SECILEN) ===\n"
    report += f'Giris Hizi: {result["velocity_in"]:.2f} m/s\n'
    report += f'Cikis Hizi: {result["velocity_out"]:.2f} m/s\n'
    report += f'Cikis Basinci: {result["P_out"]/1e5:.4f} bara\n'
    report += f'Durum: {result["velocity_status"]}\n'

    alternatives = result.get("alternatives") or {}
    if not alternatives:
        return report

    report += "\n=== ALTERNATIF SENARYOLAR ===\n"

    if "thinner" in alternatives:
        alt = alternatives["thinner"]
        pipe = alt["pipe"]
        alt_result = alt["result"]
        report += f'\n[1] {alt["note"]}:\n'
        report += f'   Boru: {pipe["nominal"]}" {pipe["schedule"]} (ID: {pipe["D_inner_mm"]:.2f} mm)\n'
        report += f'   Cikis Hizi: {alt_result["velocity_out"]:.2f} m/s\n'
        report += f'   Cikis Basinci: {alt_result["P_out"]/1e5:.4f} bara\n'

    if "thicker" in alternatives:
        alt = alternatives["thicker"]
        pipe = alt["pipe"]
        alt_result = alt["result"]
        report += f'\n[2] {alt["note"]}:\n'
        report += f'   Boru: {pipe["nominal"]}" {pipe["schedule"]} (ID: {pipe["D_inner_mm"]:.2f} mm)\n'
        report += f'   Cikis Hizi: {alt_result["velocity_out"]:.2f} m/s\n'
        report += f'   Cikis Basinci: {alt_result["P_out"]/1e5:.4f} bara\n'

    if "lowest_weight" in alternatives:
        alt = alternatives["lowest_weight"]
        pipe = alt["pipe"]
        alt_result = alt["result"]
        report += f'\n[*] {alt["note"]}:\n'
        report += f'   Boru: {pipe["nominal"]}" {pipe["schedule"]} (ID: {pipe["D_inner_mm"]:.2f} mm)\n'
        report += f'   Birim Agirlik: {pipe.get("weight_per_m", 0):.2f} kg/m\n'
        report += f'   Cikis Hizi: {alt_result["velocity_out"]:.2f} m/s\n'
        report += f'   Cikis Basinci: {alt_result["P_out"]/1e5:.4f} bara\n'

    return report

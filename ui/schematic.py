import tkinter as tk
from translations import t
from ui.widgets import ValidationHelper


class SchematicDrawer:
    def __init__(self, main_app):
        self.app = main_app

    def get_float_value(self, variable, default=0.0):
        val = variable.get()
        return ValidationHelper.parse_float(val, default)

    def get_int_value(self, variable, default=0):
        val = variable.get()
        return ValidationHelper.parse_int(val, default)

    # ──────────────────────────────────────────────
    # Yardımcı çizim metodları
    # ──────────────────────────────────────────────
    def _rounded_rect(self, canvas, x1, y1, x2, y2, r=10, **kwargs):
        """Canvas üzerinde köşeleri yuvarlak dikdörtgen çizer."""
        canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90,  extent=90, style=tk.PIESLICE, **kwargs)
        canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0,   extent=90, style=tk.PIESLICE, **kwargs)
        canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style=tk.PIESLICE, **kwargs)
        canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style=tk.PIESLICE, **kwargs)
        canvas.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
        canvas.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)

    def _info_card(self, canvas, cx, cy, title, value, unit="", color="#1976d2", bg="#e3f2fd",
                   title_font=("Segoe UI", 8), val_font=("Segoe UI", 10, "bold"), width=110):
        """Başlık+değer bilgisi içeren düzgün bilgi kartı çizer."""
        hw = width // 2
        self._rounded_rect(canvas, cx-hw, cy-28, cx+hw, cy+10, r=6, fill=bg, outline=color, width=1)
        canvas.create_text(cx, cy-17, text=title, font=title_font, fill=color)
        canvas.create_text(cx, cy+0, text=f"{value} {unit}".strip(), font=val_font, fill=color)

    def _pipe_3d(self, canvas, x1, y, x2, half_h, fill, outline, dash=()):
        """Boru gövdesi (3 katmanlı, 3D etkisi verir)."""
        # Ana dikdörtgen
        kw = dict(fill=fill, outline=outline, width=2)
        if dash:
            kw['dash'] = dash
        canvas.create_rectangle(x1, y - half_h, x2, y + half_h, **kw)
        # Üst aydınlık şerit (highlight)
        canvas.create_rectangle(x1 + 3, y - half_h + 3, x2 - 3, y - half_h + 8,
                                 fill=self._lighten(fill), outline="")
        # Alt gölge şerit
        canvas.create_rectangle(x1 + 3, y + half_h - 8, x2 - 3, y + half_h - 3,
                                 fill=self._darken(fill), outline="")

    @staticmethod
    def _lighten(hex_color):
        """Rengi %40 açık yap (basit)."""
        try:
            r = min(255, int(hex_color[1:3], 16) + 80)
            g = min(255, int(hex_color[3:5], 16) + 80)
            b = min(255, int(hex_color[5:7], 16) + 80)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    @staticmethod
    def _darken(hex_color):
        """Rengi %30 koyu yap (basit)."""
        try:
            r = max(0, int(hex_color[1:3], 16) - 50)
            g = max(0, int(hex_color[3:5], 16) - 50)
            b = max(0, int(hex_color[5:7], 16) - 50)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _gradient_bar(self, canvas, x1, y1, x2, y2, pct, col_left="#1976d2", col_right="#d32f2f"):
        """Renk geçişli doluluk çubuğu."""
        total_w = x2 - x1
        fill_w  = total_w * min(1.0, max(0.0, pct))
        steps = max(1, int(fill_w))
        for i in range(steps):
            t_val = i / max(1, steps - 1)
            # Lineer interpolasyon
            r = int(int(col_left[1:3], 16) * (1-t_val) + int(col_right[1:3], 16) * t_val)
            g = int(int(col_left[3:5], 16) * (1-t_val) + int(col_right[3:5], 16) * t_val)
            b = int(int(col_left[5:7], 16) * (1-t_val) + int(col_right[5:7], 16) * t_val)
            c = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(x1+i, y1, x1+i, y2, fill=c)
        # Çerçeve
        canvas.create_rectangle(x1, y1, x2, y2, outline="#9e9e9e", fill="")

    # ──────────────────────────────────────────────
    # Ana çizim metodu
    # ──────────────────────────────────────────────
    def draw_schematic(self, event=None):
        """Hesaplama hedefine ve duruma göre interaktif sistem şeması çizer."""
        canvas = self.app.schematic_canvas
        canvas.delete("all")

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 150 or h < 150:
            return

        target = self.app.calc_target.get()
        state  = getattr(self.app, 'schematic_state', 'pending')

        # ========== GEOMETRİ ==========
        mid_y      = h // 2 + 5
        margin_x   = max(90, w * 0.10)
        pipe_x1    = margin_x
        pipe_x2    = w - margin_x
        pipe_half  = 24          # boru yüksekliğinin yarısı

        # ========== RENK PALETI ==========
        C = {
            'known':     "#1565c0",
            'unknown':   "#c62828",
            'result':    "#2e7d32",
            'warning':   "#e65100",
            'text':      "#37474f",
            'subtext':   "#78909c",
            'pipe_ok':   "#bbdefb",
            'pipe_olok': "#1565c0",
            'pipe_pnd':  "#fff3e0",
            'pipe_olpnd':"#fb8c00",
            'pipe_err':  "#ffcdd2",
            'pipe_olerr':"#c62828",
            'pipe_calc': "#f1f8e9",
            'pipe_olcalc':"#388e3c",
        }

        # ========== ARKAPLAN GRİDİ ==========
        for gx in range(0, w, 40):
            canvas.create_line(gx, 0, gx, h, fill="#f7f7f7", width=1)
        for gy in range(0, h, 40):
            canvas.create_line(0, gy, w, gy, fill="#f7f7f7", width=1)

        # ========== DURUM ROZET (Sağ Üst) ==========
        s_cfg = {
            'pending':    ("📝 " + t("schematic_pending"),    "#757575", "#fafafa"),
            'calculating':("⏳ " + t("schematic_calculating"), "#e65100", "#fff3e0"),
            'completed':  ("✅ " + t("schematic_completed"),   "#2e7d32", "#e8f5e9"),
            'error':      ("❌ " + t("schematic_error"),       "#c62828", "#ffebee"),
        }
        s_txt, s_fg, s_bg = s_cfg.get(state, s_cfg['pending'])
        self._rounded_rect(canvas, w-210, 6, w-6, 32, r=8, fill=s_bg, outline=s_fg, width=1)
        canvas.create_text(w-108, 19, text=s_txt, font=("Segoe UI", 9, "bold"), fill=s_fg)
        if state == 'completed' and hasattr(self.app, 'last_calculation_time') and self.app.last_calculation_time:
            canvas.create_text(w-108, 40, text=f"🕐 {self.app.last_calculation_time}",
                               font=("Segoe UI", 8), fill=C['subtext'])

        # ========== BAŞLIK SATIRI ==========
        title_map = {
            t("target_pressure_drop"): ("Basınç Düşümü Analizi", "P_in · T · Q · L · D  →  P_out"),
            t("target_max_length"):    ("Maksimum Uzunluk Analizi", "P_in · P_out · T · Q · D  →  L_max"),
            t("target_min_diameter"):  ("Minimum Çap Seçimi", "P_in · T · Q · V_max  →  D_min"),
        }
        t1, t2 = title_map.get(target, (target, ""))
        canvas.create_text(20, 18, text=t1, font=("Segoe UI", 11, "bold"), fill=C['known'], anchor="w")
        canvas.create_text(20, 36, text=t2, font=("Segoe UI", 8),          fill=C['subtext'],  anchor="w")

        # ========== BORU GÖSTERİMİ ==========
        pipe_colors = {
            'pending':    (C['pipe_pnd'],  C['pipe_olpnd']),
            'calculating':(C['pipe_pnd'],  C['pipe_olpnd']),
            'completed':  (C['pipe_ok'],   C['pipe_olok']),
            'error':      (C['pipe_err'],  C['pipe_olerr']),
        }
        if target == t("target_min_diameter") and state == 'pending':
            p_fill, p_out_col = C['pipe_pnd'], C['pipe_olpnd']
            dash = (6, 4)
        elif target == t("target_max_length") and state in ('pending', 'calculating'):
            p_fill, p_out_col = C['pipe_ok'], C['pipe_olok']
            dash = ()
        else:
            p_fill, p_out_col = pipe_colors.get(state, (C['pipe_ok'], C['pipe_olok']))
            dash = ()

        self._pipe_3d(canvas, pipe_x1, mid_y, pipe_x2, pipe_half, p_fill, p_out_col, dash=dash)

        # ========== AKİŞ OKLARI ==========
        arr_col = C['result'] if state == 'completed' else C['known']
        # Sol ok
        canvas.create_line(10, mid_y, pipe_x1, mid_y, arrow=tk.LAST, width=3, fill=arr_col,
                           arrowshape=(10, 12, 5))
        canvas.create_text(pipe_x1 // 2, mid_y - 18, text=t("schematic_inlet"),
                           font=("Segoe UI", 8, "bold"), fill=arr_col)
        # Sağ ok
        canvas.create_line(pipe_x2, mid_y, w-10, mid_y, arrow=tk.LAST, width=3, fill=arr_col,
                           arrowshape=(10, 12, 5))
        canvas.create_text(pipe_x2 + (w - pipe_x2) // 2, mid_y - 18, text=t("schematic_outlet"),
                           font=("Segoe UI", 8, "bold"), fill=arr_col)

        # ========== GİRİŞ BİLGİ KARTI ==========
        try:
            p_in   = self.get_float_value(self.app.p_in_var, 0)
            t_val  = self.get_float_value(self.app.t_var, 25)
            q_val  = self.get_float_value(self.app.flow_var, 0)

            card_x = pipe_x1 - 55
            self._info_card(canvas, card_x, mid_y - 72,
                            title=f"P_in",
                            value=f"{p_in:.1f}",
                            unit=self.app.p_unit.get(),
                            color=C['known'], bg="#e3f2fd", width=110)
            self._info_card(canvas, card_x, mid_y,
                            title="T",
                            value=f"{t_val:.1f}",
                            unit=self.app.t_unit.get(),
                            color=C['known'], bg="#e3f2fd", width=110)
            self._info_card(canvas, card_x, mid_y + 72,
                            title="Q",
                            value=f"{q_val:.0f}",
                            unit=self.app.flow_unit.get(),
                            color=C['known'], bg="#e3f2fd", width=110)
        except Exception:
            pass

        # ========== FITTING BADGE ==========
        try:
            total_fit = sum(self.get_int_value(v, 0) for v in self.app.fitting_counts.values())
            if total_fit > 0:
                fx = pipe_x1 + (pipe_x2 - pipe_x1) * 0.15
                self._rounded_rect(canvas, fx-28, mid_y-18, fx+28, mid_y+18, r=6,
                                   fill="#fff3e0", outline=C['warning'], width=2)
                canvas.create_text(fx, mid_y - 6,  text="⚙", font=("Segoe UI", 10, "bold"), fill=C['warning'])
                canvas.create_text(fx, mid_y + 8,  text=f"×{total_fit}", font=("Segoe UI", 8, "bold"), fill=C['warning'])
                canvas.create_text(fx, mid_y - 32, text="Fitting", font=("Segoe UI", 7), fill=C['warning'])
        except Exception:
            pass

        # ========== HEDEF BAZLI İÇERİK ==========
        result = getattr(self.app, 'last_result', None) if state == 'completed' else None

        if target == t("target_pressure_drop"):
            self._draw_pressure_drop_schematic(canvas, w, h, mid_y, pipe_x1, pipe_x2, pipe_half, C, result)
        elif target == t("target_max_length"):
            self._draw_max_length_schematic(canvas, w, h, mid_y, pipe_x1, pipe_x2, pipe_half, C, result)
        elif target == t("target_min_diameter"):
            self._draw_min_diameter_schematic(canvas, w, h, mid_y, pipe_x1, pipe_x2, pipe_half, C, result)

    # ──────────────────────────────────────────────
    # Hedef bazlı detay çiziciler
    # ──────────────────────────────────────────────
    def _draw_pressure_drop_schematic(self, canvas, w, h, mid_y, x1, x2, ph, C, result):

        # Boru üstü: Çap etiketi
        D_val  = self.get_float_value(self.app.diam_var, 0)
        t_wall = self.get_float_value(self.app.thick_var, 0)
        D_in   = D_val - 2 * t_wall if D_val > 0 else 0
        canvas.create_text((x1+x2)/2, mid_y,
                           text=f"OD {D_val:.0f} mm  |  ID {D_in:.1f} mm",
                           font=("Segoe UI", 8, "bold"), fill=C['text'])

        # Boru altı: Uzunluk oku
        L_val = self.get_float_value(self.app.len_var, 0)
        ay = mid_y + ph + 15
        canvas.create_line(x1, ay, x2, ay, arrow=tk.BOTH, fill=C['known'], width=1, dash=(4,2))
        canvas.create_text((x1+x2)/2, ay + 12,
                           text=f"L = {L_val:.0f} m",
                           font=("Segoe UI", 8), fill=C['known'])

        if result and 'P_out' in result:
            p_out     = result['P_out'] / 1e5
            delta_p   = result.get('delta_p_total', 0) / 1e5
            v_out     = result.get('velocity_out', 0)
            v_in      = result.get('velocity_in', 0)
            p_in_bar  = self.get_float_value(self.app.p_in_var, 0)

            # Sağ: P_out kutusu
            self._info_card(canvas, x2 + (w - x2) // 2, mid_y - 60,
                            title="P_out", value=f"{p_out:.3f}", unit="bara",
                            color=C['result'], bg="#e8f5e9", width=120)
            # ΔP
            dp_pct = min(1.0, abs(delta_p) / max(p_in_bar, 0.001))
            bar_x1, bar_y1 = x2 + 5, mid_y + 10
            bar_x2, bar_y2 = w - 8,  mid_y + 26
            self._gradient_bar(canvas, bar_x1, bar_y1, bar_x2, bar_y2, dp_pct,
                               "#43a047", "#d32f2f")
            canvas.create_text((bar_x1+bar_x2)/2, mid_y + 38,
                               text=f"ΔP = {delta_p:.3f} bar ({dp_pct*100:.1f}%)",
                               font=("Segoe UI", 8), fill=C['warning'])

            # Hız badge
            v_col = C['warning'] if v_out > 20 else C['result']
            self._rounded_rect(canvas, (x1+x2)/2 - 80, mid_y + 48, (x1+x2)/2 + 80, mid_y + 70,
                                r=6, fill="#fafafa", outline=v_col, width=1)
            canvas.create_text((x1+x2)/2, mid_y + 59,
                               text=f"💨  v_in {v_in:.1f} m/s  →  v_out {v_out:.1f} m/s",
                               font=("Segoe UI", 8, "bold"), fill=v_col)

            self._draw_detail_bar(canvas, w, h, C, result)
        else:
            # Bilinmeyen P_out
            cx = x2 + (w-x2)//2
            self._info_card(canvas, cx, mid_y - 50,
                            title="P_out", value="?", unit="",
                            color=C['unknown'], bg="#ffebee", width=110)

    def _draw_max_length_schematic(self, canvas, w, h, mid_y, x1, x2, ph, C, result):
        # Boru üstü: Çap etiketi
        D_val = self.get_float_value(self.app.diam_var, 0)
        canvas.create_text((x1+x2)/2, mid_y,
                           text=f"D = {D_val:.0f} mm",
                           font=("Segoe UI", 8, "bold"), fill=C['known'])

        # Sağ: Hedef basınç
        p_tgt = self.get_float_value(self.app.target_p_var, 0)
        cx = x2 + (w-x2)//2
        self._info_card(canvas, cx, mid_y - 60,
                        title="P_out (Hedef)", value=f"{p_tgt:.1f}",
                        unit=self.app.target_p_unit.get(),
                        color=C['known'], bg="#e3f2fd", width=130)

        if result and 'L_max' in result:
            L_max = result['L_max']
            # Orta: L_max sonuç kutusu
            self._rounded_rect(canvas, (x1+x2)/2 - 100, mid_y + 40, (x1+x2)/2 + 100, mid_y + 80,
                                r=10, fill="#e8f5e9", outline=C['result'], width=2)
            canvas.create_text((x1+x2)/2, mid_y + 56,
                               text=f"✅  L_max = {L_max:.1f} m",
                               font=("Segoe UI", 11, "bold"), fill=C['result'])
            canvas.create_text((x1+x2)/2, mid_y + 71,
                               text=f"({L_max/1000:.3f} km)",
                               font=("Segoe UI", 8), fill=C['subtext'])

            # Uzunluk oku
            ay = mid_y + ph + 8
            canvas.create_line(x1, ay, x2, ay, arrow=tk.BOTH, fill=C['result'], width=1)

            self._draw_detail_bar(canvas, w, h, C, result)
        else:
            ay = mid_y + ph + 8
            canvas.create_line(x1, ay, x2 - 30, ay, fill=C['unknown'], width=2, dash=(4,2))
            canvas.create_text((x1+x2)/2, mid_y + 48,
                               text=f"❓ L_max = ?",
                               font=("Segoe UI", 11, "bold"), fill=C['unknown'])

    def _draw_min_diameter_schematic(self, canvas, w, h, mid_y, x1, x2, ph, C, result):
        # Uzunluk oku
        L_val = self.get_float_value(self.app.len_var, 0)
        ay = mid_y + ph + 15
        canvas.create_line(x1, ay, x2, ay, arrow=tk.BOTH, fill=C['known'], width=1, dash=(4, 2))
        canvas.create_text((x1+x2)/2, ay + 12,
                           text=f"L = {L_val:.0f} m",
                           font=("Segoe UI", 8), fill=C['known'])

        if result and result.get('selected_pipe'):
            pipe = result['selected_pipe']
            # Boru gövdesi içinde seçilen NPS
            canvas.create_text((x1+x2)/2, mid_y,
                               text=f"✅  NPS {pipe['nominal']}\"  Sch {pipe['schedule']}",
                               font=("Segoe UI", 11, "bold"), fill=C['result'])

            # Sağ panel: OD / ID / ağırlık
            cx = x2 + (w - x2)//2
            self._info_card(canvas, cx, mid_y - 75,
                            title="OD", value=f"{pipe['OD_mm']:.1f}", unit="mm",
                            color=C['result'], bg="#e8f5e9", width=110)
            self._info_card(canvas, cx, mid_y - 15,
                            title="ID", value=f"{pipe['D_inner_mm']:.1f}", unit="mm",
                            color=C['result'], bg="#e8f5e9", width=110)
            if 'weight_per_m' in pipe:
                self._info_card(canvas, cx, mid_y + 45,
                                title="Ağırlık", value=f"{pipe['weight_per_m']:.2f}", unit="kg/m",
                                color=C['text'], bg="#f5f5f5", width=110)

            # Durum badge
            vel_in  = result.get('velocity_in', 0)
            vel_lim = result.get('max_vel', 20)
            status  = result.get('velocity_status', '')
            v_pct   = min(1.0, vel_in / max(vel_lim, 0.001))
            v_col   = C['warning'] if v_pct > 0.9 else C['result']

            self._rounded_rect(canvas, (x1+x2)/2 - 90, mid_y + 38, (x1+x2)/2 + 90, mid_y + 60,
                                r=6, fill="#fafafa", outline=v_col, width=1)
            canvas.create_text((x1+x2)/2, mid_y + 49,
                               text=f"💨 {vel_in:.1f} m/s  /  {vel_lim:.0f} m/s limit  ({v_pct*100:.0f}%)",
                               font=("Segoe UI", 8, "bold"), fill=v_col)

            # Hız doluluk çubuğu
            bx1, bx2 = (x1+x2)/2 - 90, (x1+x2)/2 + 90
            self._gradient_bar(canvas, bx1, mid_y + 62, bx2, mid_y + 72, v_pct,
                               "#43a047", "#d32f2f")

            self._draw_detail_bar(canvas, w, h, C, result, include_pipe=True, pipe=pipe)
        else:
            canvas.create_text((x1+x2)/2, mid_y,
                               text=f"❓  D_min = ?",
                               font=("Segoe UI", 11, "bold"), fill=C['unknown'])

    # ──────────────────────────────────────────────
    # Ortak alt detay şeridi
    # ──────────────────────────────────────────────
    def _draw_detail_bar(self, canvas, w, h, C, result, include_pipe=False, pipe=None):
        """Alt kısımdaki teknik detay şeridini çizer."""
        dy = h - 30
        # Separator
        canvas.create_line(10, dy - 22, w - 10, dy - 22, fill="#e0e0e0", width=1)

        items = []

        Re = result.get('Re', 0)
        if Re > 0:
            regime = "Laminar" if Re < 2300 else ("Geçiş" if Re < 4000 else "Türbülanslı")
            items.append((f"Re: {Re/1000:.1f}k  ({regime})", C['result'] if Re >= 4000 else C['warning']))

        f = result.get('f', 0)
        if f > 0:
            items.append((f"f = {f:.5f}", C['text']))

        dp_pipe = result.get('delta_p_pipe', 0) / 1e5
        dp_fit  = result.get('delta_p_fittings', 0) / 1e5
        if dp_pipe + dp_fit > 0:
            items.append((f"ΔP boru: {dp_pipe:.3f} bar", C['text']))
            items.append((f"ΔP fitting: {dp_fit:.3f} bar", C['warning']))

        rho = result.get('gas_props_in', {}).get('density', 0)
        if rho > 0:
            items.append((f"ρ: {rho:.2f} kg/m³", C['subtext']))

        if include_pipe and pipe:
            t_mm  = pipe.get('t_mm', 0)
            t_req = pipe.get('t_required_mm', 0)
            if t_mm > 0:
                items.append((f"et: {t_mm:.2f} mm (min {t_req:.2f})", C['text']))

        n = len(items)
        if n == 0:
            return
        for i, (txt, col) in enumerate(items):
            cx = w * (i + 0.5) / n
            canvas.create_text(cx, dy, text=txt, font=("Segoe UI", 8), fill=col, anchor="center")

import tkinter as tk
import json
from datetime import datetime
from tkinter import ttk, messagebox, filedialog, Menu, simpledialog
from tkinter.scrolledtext import ScrolledText
import threading
import queue
import time
import math
import os
import webbrowser
import sys

# Modüler importlar
from auth import load_auth_config, prompt_for_admin_password, prompt_for_program_access, show_password_management_dialog
from app_paths import get_config_path, get_install_dir, get_session_file_path, load_config, save_config
from constants import convert_pressure_to_pa, convert_temperature_to_k
from release_metadata import APP_VERSION, get_release_notes, get_release_notes_title, get_versioned_exe_name
from data import COOLPROP_GASES, PIPE_MATERIALS, PIPE_ROUGHNESS, FITTING_K_FACTORS, ASME_B36_10M_DATA, GAS_PRESETS
from calculations import GasFlowCalculator
from controllers import GasFlowController
from reporting import format_max_length_report, format_min_diameter_report, format_pressure_drop_report
from updater import Updater, _obfuscate_token
from translations import t, t_fitting, set_language, get_language, get_fitting_name_tr
from ui.widgets import ToolTip, ValidationHelper, ValidatedEntry
from ui.dialogs import show_about, show_user_guide, show_program_details
from ui.schematic import SchematicDrawer
from ui.graphs import show_graphs
from flow_utils import (
    FLOW_MODE_COMPRESSIBLE,
    FLOW_MODE_INCOMPRESSIBLE,
    get_flow_mode_label,
    normalize_flow_mode,
)
from target_utils import (
    TARGET_PRESSURE_DROP,
    TARGET_MAX_LENGTH,
    TARGET_MIN_DIAMETER,
    get_calc_target_label,
    normalize_calc_target,
)
from ui.panels.gas_panel import GasPanel
from ui.panels.process_panel import ProcessPanel
from ui.panels.pipe_panel import PipePanel
from ui.panels.results_panel import ResultsPanel
from ui.panels.log_panel import LogPanel


from theme_manager import ThemeManager, THEMES, FONT_FAMILY, initialize_font_family
from state_manager import StateManager
from services.progress import ProgressService
from services.update_service import UpdateService
from services.report_service import ReportService
from services.project_io import ProjectIOService


def load_app_config():
    return load_config()


def save_app_config(config):
    return save_config(config)


# Config dosyasından dil ayarını yükle
def load_language_from_config():
    try:
        cfg = load_app_config()
        set_language(cfg.get("language", "tr"))
    except Exception as e:
        import traceback; traceback.print_exc()

load_language_from_config()

# --- Deleted ToolTip, ValidationHelper, ValidatedEntry (Moved to ui.widgets) ---


class GasFlowCalculatorApp:
    def __init__(self, root):
        self.root = root
        initialize_font_family(self.root)
        self.font_family = FONT_FAMILY
        self.root.font_family = FONT_FAMILY
        self.root.title(f"{t('app_title')} V{APP_VERSION}")
        self.root.geometry("1450x950")
        self.root.minsize(1100, 800)

        # Tema Ayarı
        cfg = load_app_config()
        self.current_theme = cfg.get("theme", "light")
        if self.current_theme not in THEMES:
            self.current_theme = "light"
        
        # Paylaşımlı renk sabitlerini ilk başta root üzerinde sakla
        self._colors = THEMES[self.current_theme]
        self.root._colors = THEMES[self.current_theme]
        self.root.current_theme = self.current_theme

        # Tema Yöneticisi
        self.theme = ThemeManager(self)

        # Durum Yöneticisi
        self.state = StateManager(self)

        # Hesaplama Motoru
        self.calculator = GasFlowCalculator()
        self.controller = GasFlowController()
        self.calculator.set_log_callback(self.log_message)
        # Güncelleme yöneticisi
        self.updater = Updater(self.log_message)
        self.last_download_path = None

        # Servisler
        self.progress = ProgressService(self)
        self.update_service = UpdateService(self)
        self.report_service = ReportService(self)
        self.project_io = ProjectIOService(self)

        # Değişkenler
        self.gas_components = {}
        self.fitting_counts = {}
        self.ball_valve_kv = tk.DoubleVar(value=0.0)
        self.ball_valve_cv = tk.DoubleVar(value=0.0)
        self.log_queue = queue.Queue()
        self.calc_queue = queue.Queue()
        
        # Validasyon ve Yardımcılar
        self.validation = ValidationHelper()
        self.report_text = None
        self.schematic_canvas = None
        
        # Şema durumu değişkenleri
        self.schematic_state = "pending"  # "pending", "calculating", "completed", "error"
        self.last_calculation_time = None
        self.last_result = None
        
        # Stil
        self.setup_styles()
        
        # Arayüz Oluşturma
        self.create_main_layout()
        
        # Menü Çubuğu
        self.create_menu()
        
        # Şema Çizicisi (Bağlamaları kur)
        self.schematic_drawer = SchematicDrawer(self) 
        self._setup_schematic_bindings()

        # Varsayılan Değerleri Kur
        self.setup_default_state()
        
        # İlk UI görünürlük ayarı
        self.update_ui_visibility()
        
        # Dil değişikliği sonrası oturum geri yükleme
        self._restore_session_after_lang_change()
        
        # Thread-safe log polling başlat (ana thread'de çalışır)
        self._poll_log_queue()
        
        self.log_message(f"{t('msg_program_started')}: V{APP_VERSION}")
        self.log_message(f"{t('msg_version')}: {APP_VERSION}")
        # Arka planda sessiz güncelleme kontrolü
        self.root.after(500, self.silent_update_check)
        
        # Güncelleme notlarını göster
        self.check_changelog()

    def setup_default_state(self):
        self.state.setup_default_state()

    def check_changelog(self):
        try:
            cfg = load_app_config()
            dismissed_version = cfg.get("dismissed_release_notes_version")
            if dismissed_version != APP_VERSION:
                self.root.after(1000, self.show_changelog_dialog)
        except Exception as e:
            self.log_message(f"Changelog kontrolu hatasi: {e}", level="ERROR")

    def show_changelog_dialog(self):
        language = get_language()
        top = tk.Toplevel(self.root)
        top.title(get_release_notes_title(APP_VERSION, language))
        top.geometry("650x500")
        top.transient(self.root)
        top.grab_set()

        txt = ScrolledText(top, wrap="word", font=(FONT_FAMILY, 10))
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", get_release_notes(APP_VERSION, language))
        txt.config(state="disabled")

        dont_show_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(top, text=t("dont_show_again"), variable=dont_show_var)
        chk.pack(anchor="w", padx=10, pady=5)

        def on_close():
            if dont_show_var.get():
                try:
                    cfg = load_app_config()
                    cfg["dismissed_release_notes_version"] = APP_VERSION
                    save_app_config(cfg)
                except Exception as e:
                    self.log_message(f"Changelog dismiss kayit hatasi: {e}", level="ERROR")
            top.destroy()

        btn = ttk.Button(top, text="Tamam / OK", command=on_close)
        btn.pack(pady=10)

    def create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # Dosya Menüsü
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu_file"), menu=file_menu)
        file_menu.add_command(label=t("menu_save_project"), command=self.save_project)
        file_menu.add_command(label=t("menu_load_project"), command=self.load_project)
        file_menu.add_separator()
        file_menu.add_command(label=t("menu_exit"), command=self.root.quit)
        
        # Güncelleme Menüsü
        update_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu_update"), menu=update_menu)
        update_menu.add_command(label=t("menu_check_updates"), command=self.check_updates)
        update_menu.add_command(label=t("menu_download_latest"), command=self.download_latest_release)
        update_menu.add_separator()
        update_menu.add_command(label=t("menu_apply_update"), command=self.apply_update_from_zip_file)
        update_menu.add_command(label=t("menu_update_config"), command=self.open_update_config)
        
        # Dil Menüsü
        lang_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu_language"), menu=lang_menu)
        lang_menu.add_command(label="🇹🇷 " + t("lang_turkish"), command=lambda: self.change_language("tr"))
        lang_menu.add_command(label="🇬🇧 " + t("lang_english"), command=lambda: self.change_language("en"))
        
        # Görünüm (Tema) Menüsü
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu_view"), menu=view_menu)
        view_menu.add_command(label="☀️  " + t("theme_light"), command=lambda: self.change_theme("light"))
        view_menu.add_command(label="🌙  " + t("theme_dark"), command=lambda: self.change_theme("dark"))
        view_menu.add_command(label="👁️  " + t("theme_contrast"), command=lambda: self.change_theme("contrast"))
        
        # Yardım Menüsü
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=t("menu_help"), menu=help_menu)
        help_menu.add_command(label=t("menu_user_guide"), command=self.show_user_guide)
        help_menu.add_command(label=t("program_details_title"), command=self.show_program_details)
        help_menu.add_separator()
        help_menu.add_command(label=t("menu_about"), command=self.show_about)
    
    def change_language(self, lang_code):
        """Dili değiştir ve uygulamayı yeniden başlat. Oturum verileri korunur."""
        current = get_language()
        if current == lang_code:
            return
        
        # Config dosyasını güncelle
        try:
            cfg = load_app_config()
            cfg["language"] = lang_code
            save_app_config(cfg)
        except Exception as e:
            messagebox.showerror(t("dialog_error"), str(e))
            return
        
        # Kullanıcıya bildir ve yeniden başlat
        set_language(lang_code)  # Mesajların yeni dilde görünmesi için
        if messagebox.askyesno(t("lang_change_title"), t("lang_change_message") + "\n\n" + t("lang_restart_now")):
            # Oturum verilerini kaydet (dil değişikliği sırasında veri kaybını önle)
            self._save_session_for_lang_change()
            self.root.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

    def change_theme(self, theme_name):
        self.theme.change_theme(theme_name)

    def setup_styles(self):
        self.theme.setup_styles()

    def _get_session_file_path(self):
        return self.state._get_session_file_path()

    def _save_session_for_lang_change(self):
        self.state._save_session_for_lang_change()

    def _restore_session_after_lang_change(self):
        self.state._restore_session_after_lang_change()
    
    def show_user_guide(self):
        show_user_guide(self.root)
    
    def show_about(self):
        show_about(self.root, APP_VERSION)
    
    def show_program_details(self):
        show_program_details(self.root)

    def validate_float(self, event):
        """Eski stil doğrulama - geriye uyumluluk için korundu."""
        widget = event.widget
        try:
            # Virgül desteği ekle
            value_str = widget.get()
            normalized = ValidationHelper.normalize_number(value_str)
            val = float(normalized)
            if val < 0: raise ValueError
            widget.config(bg="white")
        except ValueError:
            widget.config(bg="#ffe6e6")  # Hata durumunda hafif kırmızı

    def create_main_layout(self):
        # Ana Notebook (Sekmeler)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        # 1. Hesaplama Sekmesi
        calc_tab = ttk.Frame(self.notebook)
        self.notebook.add(calc_tab, text="  " + t("tab_calculation") + "  ")
        self.create_calc_tab_content(calc_tab)

        # 2. Log Sekmesi
        log_tab = ttk.Frame(self.notebook)
        self.notebook.add(log_tab, text="  " + t("tab_logs") + "  ")
        self.create_log_tab_content(log_tab)

        # Alt Bilgi / Butonlar
        self.create_footer()
        
        # Validasyon Bağlamaları (ValidatedEntry için otomatik, diğerleri için eski stil)
        # Not: ValidatedEntry kendi bağlamalarını yapar
        self.root.bind_class("TEntry", "<FocusOut>", self.validate_float)
        self.root.bind_class("TEntry", "<KeyRelease>", self._on_entry_key_release)
    
    def _on_entry_key_release(self, event):
        """Tuş bırakıldığında hızlı doğrulama."""
        widget = event.widget
        if isinstance(widget, ValidatedEntry):
            return  # ValidatedEntry kendi doğrulamasını yapar
        
        try:
            value_str = widget.get()
            if not value_str.strip():
                widget.config(bg="white")
                return
            normalized = ValidationHelper.normalize_number(value_str)
            val = float(normalized)
            if val < 0:
                widget.config(bg="#ffe6e6")
            else:
                widget.config(bg="white")
        except ValueError:
            widget.config(bg="#ffe6e6")

    def create_calc_tab_content(self, parent):
        # PanedWindow (Ayırıcı)
        self.paned_window = ttk.PanedWindow(parent, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # Sol Panel (Girdiler)
        left_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(left_panel, weight=1)
        
        # Sağ Panel (Rapor)
        right_panel = ttk.Frame(self.paned_window, width=450)
        self.paned_window.add(right_panel, weight=0) # Sağ panel başlangıçta sabit kalsın isteyebiliriz ama esnek olması daha iyi

        # --- GİRDİ GRUPLARI (Bileşenler) ---
        self.gas_panel = GasPanel(left_panel, self)
        self.gas_panel.pack(fill="x", pady=5)
        self.gas_panel.register(self)

        self.process_panel = ProcessPanel(left_panel, self)
        self.process_panel.pack(fill="x", pady=5)
        self.process_panel.register(self)

        self.pipe_panel = PipePanel(left_panel, self)
        self.pipe_panel.pack(fill="x", pady=5)
        self.pipe_panel.register(self)

        # --- SAĞ PANEL (RAPOR) ---
        self.results_panel = ResultsPanel(right_panel, self)
        self.results_panel.pack(fill="both", expand=True)
        self.results_panel.register(self)
    
    def _draw_progress_button(self, text, progress, idle=False):
        self.progress.draw_progress_button(text, progress, idle)

    def _on_progress_hover(self, event):
        self.progress.on_progress_hover(event)

    def _on_progress_leave(self, event):
        self.progress.on_progress_leave(event)

    def _on_progress_resize(self, event):
        self.progress.on_progress_resize(event)

    def update_progress(self, value, status_text=None):
        self.progress.is_calculating = self.is_calculating
        self.progress.progress_value = getattr(self, 'progress_value', 0)
        self.progress.update(value, status_text)
        self.progress_value = self.progress.progress_value

    def reset_progress_button(self):
        self.is_calculating = False
        self.progress_value = 0
        self.progress.is_calculating = False
        self.progress.progress_value = 0
        self.progress.reset()
    
    def _setup_schematic_bindings(self):
        """Şema otomatik güncelleme için binding'leri kur."""
        # Hesaplama hedefi değiştiğinde şemayı güncelle
        self.calc_target.trace_add("write", lambda *args: self._on_target_or_input_change())
        
        # Akış tipi değiştiğinde şemayı güncelle
        self.flow_type.bind("<<ComboboxSelected>>", self._on_target_or_input_change)
        
        # Basınç/Sıcaklık/Debi değişkenleri için trace
        self.p_in_var.trace_add("write", self._schedule_schematic_update)
        self.t_var.trace_add("write", self._schedule_schematic_update)
        self.flow_var.trace_add("write", self._schedule_schematic_update)
        self.len_var.trace_add("write", self._schedule_schematic_update)
        self.diam_var.trace_add("write", self._schedule_schematic_update)
        self.thick_var.trace_add("write", self._schedule_schematic_update)
        self.target_p_var.trace_add("write", self._schedule_schematic_update)
        self.max_vel_var.trace_add("write", self._schedule_schematic_update)
        
        # Debounce için timer ID
        self._schematic_update_timer = None
    
    def _on_target_or_input_change(self, event=None):
        """Hedef veya önemli girdi değiştiğinde."""
        # Check if target actually changed to prevent infinite loops
        target_val = self.calc_target.get()
        current_target = getattr(self, '_current_target', None)
        if current_target != target_val:
            self._current_target = target_val
            self.schematic_state = "pending"
            self.last_result = None
            
            # Güncelle segment butonu stillerini
            if hasattr(self, '_seg_buttons'):
                for t_val, btn in self._seg_buttons.items():
                    btn.config(style="SegBtnActive.TButton" if t_val == target_val else "SegBtn.TButton")
                    
            # UI görünürlüğünü güncelle (hedef değişti)
            self.update_ui_visibility()
        self.refresh_schematic()
    
    def _schedule_schematic_update(self, *args):
        """Şema güncellemesini 300ms gecikmeyle planla (debounce)."""
        if self._schematic_update_timer:
            self.root.after_cancel(self._schematic_update_timer)
        self._schematic_update_timer = self.root.after(300, self.refresh_schematic)
    
    def refresh_schematic(self):
        if hasattr(self, 'schematic_canvas'):
            self.schematic_drawer.draw_schematic()

    def draw_schematic(self, event=None):
        if hasattr(self, 'schematic_drawer'):
            self.schematic_drawer.draw_schematic(event)



    def create_log_tab_content(self, parent):
        self.log_panel = LogPanel(parent, self)
        self.log_panel.pack(fill="both", expand=True)
        self.log_panel.register(self)

    def log_message(self, message, level="INFO"):
        """Thread-safe log mesajı ekleme. Kuyruk ana thread'den periyodik olarak drenlenir."""
        timestamp = time.strftime("%H:%M:%S")
        # Kuyruğa yapısal veri ekle (queue.Queue thread-safe'dir)
        self.log_queue.put({"time": timestamp, "level": level, "message": message})
    
    def _poll_log_queue(self):
        """Ana thread'de periyodik olarak log kuyruğunu kontrol et."""
        self.process_log_queue()
        self.root.after(200, self._poll_log_queue)

    def process_log_queue(self):
        while not self.log_queue.empty():
            entry = self.log_queue.get()
            self.all_logs.append(entry)
            
            # Filtre kontrolü
            current_filter = self.log_filter_var.get()
            if current_filter == t("log_all") or entry["level"] == current_filter:
                self.log_tree.insert("", "end", values=(entry["time"], entry["level"], entry["message"]), tags=(entry["level"],))
                self.log_tree.yview_moveto(1) # Otomatik kaydır

    def apply_log_filter(self, event=None):
        self.log_panel.apply_log_filter(event)

    def clear_logs(self):
        self.log_panel.clear_logs()

    def create_footer(self):
        footer = tk.Frame(self.root, bg="#1a237e", height=26)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        # Sol: Uygulama adı
        tk.Label(footer,
                 text=f"  Gas Flow Calc V{APP_VERSION}  |  © {datetime.now().year} Mühendislik Araçları",
                 font=(FONT_FAMILY, 8), bg="#1a237e", fg="#c5cae9").pack(side="left")

        # Sağ: Durum etiketleri
        self.footer_status = tk.Label(footer, text="Hazır",
                                      font=(FONT_FAMILY, 8, "bold"),
                                      bg="#1a237e", fg="#a5d6a7")
        self.footer_status.pack(side="right", padx=8)

        self.footer_model = tk.Label(footer, text="",
                                     font=(FONT_FAMILY, 8),
                                     bg="#1a237e", fg="#90caf9")
        self.footer_model.pack(side="right", padx=8)

        self.footer_time = tk.Label(footer, text="",
                                    font=(FONT_FAMILY, 8),
                                    bg="#1a237e", fg="#b0bec5")
        self.footer_time.pack(side="right", padx=8)

    def _update_footer(self, status="Hazır", calc_time_ms=None):
        """Durum çubuğunu günceller."""
        try:
            model_short = {
                "CoolProp (High Accuracy EOS)": "CoolProp",
                "Peng-Robinson (PR EOS)": "PR-EOS",
                "Soave-Redlich-Kwong (SRK EOS)": "SRK",
                "Pseudo-Critical (Kay's Rule)": "Kay's Rule",
            }.get(self.thermo_model.get(), self.thermo_model.get())

            self.footer_model.config(text=f"⚙ {model_short}")

            color_map = {"Hazır": "#a5d6a7", "Hesaplanıyor...": "#ffcc80",
                         "Tamamlandı": "#a5d6a7", "Hata": "#ef9a9a"}
            col = color_map.get(status, "#cfd8dc")
            self.footer_status.config(text=status, fg=col)

            if calc_time_ms is not None:
                self.footer_time.config(text=f"⏱ {calc_time_ms} ms")
        except Exception as e:
            self.log_message(f"Footer guncelleme hatasi: {e}", level="ERROR")

    # --- İŞLEVSELLİK ---
    
    def filter_gas_list(self, *args):
        self.gas_panel.filter_gas_list(*args)

    def _clamp_fitting_value(self, var):
        self.pipe_panel._clamp_fitting_value(var)

    def add_gas_component(self):
        self.gas_panel.add_gas_component()

    def remove_gas(self, gas_id, widget):
        self.gas_panel.remove_gas(gas_id, widget)

    def update_gas_total(self, *args):
        self.gas_panel.update_gas_total(*args)

    def check_gas_composition(self):
        return self.gas_panel.check_gas_composition()

    def _on_nps_changed(self, event=None):
        self.pipe_panel._on_nps_changed(event)

    def _on_schedule_changed(self, event=None):
        self.pipe_panel._on_schedule_changed(event)

    def _toggle_fittings(self):
        self.pipe_panel._toggle_fittings()

    def _on_preset_selected(self, event=None):
        self.gas_panel._on_preset_selected(event)

    def _on_material_changed(self, event=None):
        self.pipe_panel._on_material_changed(event)

    def update_ui_visibility(self, event=None):
        target = self.calc_target.get()
        
        self.pipe_panel.show_length(False)
        self.pipe_panel.show_target_pressure(False)
        self.pipe_panel.show_max_velocity(False)
        
        if target == TARGET_MIN_DIAMETER:
            self.pipe_panel.show_design_frame(True)
            self.pipe_panel.lock_pipe_fields(True)
            self.pipe_panel.show_nps_schedule(False)
            self.pipe_panel.show_diameter_thickness(False)
            if normalize_flow_mode(self.flow_type.get()) == FLOW_MODE_COMPRESSIBLE:
                self.pipe_panel.show_length(True)
        else:
            self.pipe_panel.show_design_frame(False)
            self.pipe_panel.lock_pipe_fields(False)
            self.pipe_panel.show_nps_schedule(True)
            self.pipe_panel.show_diameter_thickness(True)
        
        if target == TARGET_PRESSURE_DROP:
            self.pipe_panel.show_length(True)
        elif target == TARGET_MAX_LENGTH:
            self.pipe_panel.show_target_pressure(True)
        elif target == TARGET_MIN_DIAMETER:
            self.pipe_panel.show_max_velocity(True)

    def save_report(self):
        self.report_service.save_report()

    def save_project(self):
        self.project_io.save_project()

    def load_project(self):
        self.project_io.load_project()

    def get_ui_state(self):
        return self.project_io.get_ui_state()

    def set_ui_state(self, data):
        self.project_io.set_ui_state(data)

    # --- HESAPLAMA BAŞLATMA ---
    def start_calculation(self):
        # 1. Gaz Bileşimi Kontrolü
        is_exact, total, mole_fractions, confirmed, error_msg = self.check_gas_composition()
        
        if error_msg:
            messagebox.showerror(t("dialog_gas_error_title", "Gaz Bileşimi Hatası"), error_msg)
            return

        if not confirmed:
            return

        normalization_info = None
        if not is_exact:
            normalization_info = {
                "original_total": total,
                "message": t("normalization_message", f"Gaz bileşimi %{total:.2f} idi, %100'e normalize edildi.")
            }
            self.log_message(t("log_normalization", f"Gaz bileşimi normalize edildi: %{total:.2f} → %100"), level="WARNING")

        # 2. Verileri Topla — Controller üzerinden
        ui_state = self.get_ui_state()
        inputs, errors = self.controller.prepare_inputs(ui_state, mole_fractions_override=mole_fractions)
        
        if errors:
            messagebox.showerror(t("dialog_input_error_title", "Girdi Hatası"), "\n".join(errors))
            return

        if inputs is None:
            messagebox.showerror(t("dialog_input_error_title", "Girdi Hatası"), t("dialog_input_prepare_error", "Girdi verileri hazırlanamadı."))
            return
            
        inputs["normalization_info"] = normalization_info

        # 3. Arayüzü Kilitle ve Progress Başlat
        self.results_panel.set_calculating(True)
        self.schematic_state = "calculating"
        self.update_progress(0, "Baslatiliyor...")
        self.refresh_schematic()
        self._update_footer("Hesaplaniyor...")
        self._calc_start_time = time.time()
        
        self.results_panel.clear_report()
        
        if normalization_info:
            self.results_panel.append_report(f"\u26a0\ufe0f {normalization_info['message']}\n\n")
        self.results_panel.append_report("Hesaplama baslatildi...\n")

        # 4. Thread Başlat
        threading.Thread(target=self.run_calculation_thread, args=(inputs,), daemon=True).start()
        
        # 5. Progress animasyonu başlat
        self._start_progress_animation()
        self.root.after(100, self.check_calc_queue)
    
    def _start_progress_animation(self):
        self.progress.is_calculating = self.results_panel.widgets['is_calculating']
        self.progress.start_animation()

    def get_float_value(self, var, default=0.0):
        """DoubleVar veya StringVar'dan normalize edilmiş float değer al."""
        try:
            # Önce doğrudan get() dene (DoubleVar için)
            val = var.get()
            if isinstance(val, (int, float)):
                return float(val)
            # String ise normalize et
            return ValidationHelper.parse_float(str(val), default=default) or default
        except (tk.TclError, ValueError, AttributeError):
            return default
    
    def get_int_value(self, var, default=0):
        """IntVar veya StringVar'dan normalize edilmiş int değer al."""
        try:
            val = var.get()
            if isinstance(val, int):
                return val
            if isinstance(val, float):
                return int(val)
            return ValidationHelper.parse_int(str(val), default=default) or default
        except (tk.TclError, ValueError, AttributeError):
            return default
    
    def run_calculation_thread(self, inputs):
        try:
            # Kullanicidan gelen mole_fractions degisti mi kontrol et
            self.calculator.clear_thermo_cache(
                mole_fractions=inputs.get("mole_fractions")
            )
            
            target = inputs['target']
            result = None
            
            if target == TARGET_PRESSURE_DROP:
                result = self.calculator.calculate_pressure_drop(inputs)
                report = format_pressure_drop_report(inputs, result)
            elif target == TARGET_MAX_LENGTH:
                result = self.calculator.calculate_max_length(inputs)
                report = format_max_length_report(inputs, result)
            elif target == TARGET_MIN_DIAMETER:
                result = self.calculator.calculate_min_diameter(inputs)
                report = format_min_diameter_report(inputs, result)
            else:
                report = "Bu özellik henüz V5 arayüzüne tam entegre edilmedi."

            self.calc_queue.put(("SUCCESS", {"report": report, "result": result}))
        except Exception as e:
            self.calc_queue.put(("ERROR", str(e)))

    def check_calc_queue(self):
        try:
            status, data = self.calc_queue.get_nowait()
            
            # Hesaplama tamamlandi - progress'i %100 yap
            self.update_progress(100, "Tamamlandi!")
            self.root.after(500, self.reset_progress_button)
            
            if status == "SUCCESS":
                elapsed_ms = int((time.time() - getattr(self, '_calc_start_time', 0)) * 1000)
                self._update_footer("Tamamlandi", calc_time_ms=elapsed_ms)
                self.results_panel.clear_report()
                self.results_panel.append_report(data['report'])
                self.last_result = data['result'] # Sonucu sakla
                
                # Minimum Cap modunda hesaplanan boru bilgilerini arayuze senkronize et
                target = self.calc_target.get()
                if target == TARGET_MIN_DIAMETER and data['result'].get('selected_pipe'):
                    p = data['result']['selected_pipe']
                    
                    self.pipe_panel.lock_pipe_fields(False)
                    self.pipe_panel.widgets['nps_combo'].set(p['nominal'])
                    if p['nominal'] in ASME_B36_10M_DATA:
                        schedules = list(ASME_B36_10M_DATA[p['nominal']]["schedules"].keys())
                        self.pipe_panel.widgets['schedule_combo'].config(values=schedules)
                    else:
                        self.pipe_panel.widgets['schedule_combo'].config(values=[p['schedule']])
                    self.pipe_panel.widgets['schedule_combo'].set(p['schedule'])
                    self.pipe_panel.widgets['diam_var'].set(p['OD_mm'])
                    self.pipe_panel.widgets['thick_var'].set(p['t_mm'])
                    self.pipe_panel.lock_pipe_fields(True)
                
                # Şema durumunu güncelle
                self.schematic_state = "completed"
                self.last_calculation_time = time.strftime("%H:%M:%S")
                self.refresh_schematic()  # Şemayı sonuçlarla güncelle
                
                # Tabloyu ve Profili Doldur
                self.populate_results_table(data['result'])
                self.populate_profile_table(data['result'])
                self._update_warning_banner(data['result'])
                
                # Gömülü Grafikleri Çiz
                show_graphs(self.charts_container, data['result'], app=self)

                self.results_panel.select_tab("summary")

                self.log_message(t("log_calc_complete", "Hesaplama başarıyla tamamlandı."), level="INFO")
            else:
                self._update_footer(t("status_error", "Hata"))
                messagebox.showerror(t("dialog_calc_error_title", "Hesaplama Hatası"), data)
                self.results_panel.append_report(f"\n{t('label_error', 'HATA')}: {data}")

                self.schematic_state = "error"
                self.refresh_schematic()

                self.log_message(t("log_calc_error", f"Hesaplama hatası: {data}"), level="ERROR")
        except queue.Empty:
            self.root.after(100, self.check_calc_queue)

    def _update_warning_banner(self, result):
        self.results_panel.hide_warning()
        status = result.get("choked_status", "N/A")
        
        if status != "OK" and status != "N/A":
            self.results_panel.show_warning(t("warning_choked"))

    def populate_results_table(self, result):
        self.results_panel.clear_results_table()
        if not result:
            return

        target = self.calc_target.get()
        ui_state = self.get_ui_state()
        rows = self.controller.get_results_table_data(result, target, ui_state)
        for param, value, unit, *extra in rows:
            tag = extra[0] if extra else ""
            self.results_panel.add_result_row(param, value, unit, tag)

        if "m_dot" in result:
            add_row("Kutlesel Debi", f"{result['m_dot']:.4f}", "kg/s")

    def populate_profile_table(self, result):
        self.results_panel.clear_profile_table()
            
        profile_data = result.get("profile_data")
        if profile_data and len(profile_data.get("distance", [])) > 0:
            d_list = profile_data["distance"]
            p_list = profile_data["pressure"]
            v_list = profile_data["velocity"]
            
            for d, p, v in zip(d_list, p_list, v_list):
                self.results_panel.add_profile_row(f"{d:.2f}", f"{p:.2f}", f"{v:.2f}")
            
            self.results_panel.enable_csv_export(True)
        else:
            self.results_panel.enable_csv_export(False)

    def export_profile_to_csv(self):
        self.report_service.export_profile_to_csv()

    # --- Güncelleme İşlevleri ---
    def silent_update_check(self):
        self.update_service.silent_check()

    def check_updates(self):
        self.update_service.check()

    def download_latest_release(self):
        self.update_service.download_latest()

    def open_update_config(self):
        self.update_service.open_config()

    def apply_update_from_zip_file(self):
        self.update_service.apply_update_from_file()

    def apply_update(self, zip_path: str):
        self.update_service.apply_update(zip_path)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    if not prompt_for_program_access(root):
        root.destroy()
        sys.exit(0)
    root.deiconify()
    app = GasFlowCalculatorApp(root)
    root.mainloop()

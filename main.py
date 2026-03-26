import tkinter as tk
import json
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
from app_paths import get_config_path, get_install_dir, get_session_file_path, load_config, save_config
from release_metadata import APP_VERSION, get_release_notes, get_release_notes_title, get_versioned_exe_name
from data import COOLPROP_GASES, PIPE_MATERIALS, PIPE_ROUGHNESS, FITTING_K_FACTORS, ASME_B36_10M_DATA, GAS_PRESETS
from calculations import GasFlowCalculator
from updater import Updater
from translations import t, t_fitting, set_language, get_language, get_fitting_name_tr
from ui.widgets import ToolTip, ValidationHelper, ValidatedEntry
from ui.dialogs import show_about, show_user_guide, show_program_details
from ui.schematic import SchematicDrawer
from ui.graphs import show_graphs
from ui.panels.gas_panel import GasPanel
from ui.panels.process_panel import ProcessPanel
from ui.panels.pipe_panel import PipePanel
from ui.panels.results_panel import ResultsPanel
from ui.panels.log_panel import LogPanel


def load_app_config():
    return load_config()


def save_app_config(config):
    return save_config(config)


# Config dosyasından dil ayarını yükle
def load_language_from_config():
    try:
        cfg = load_app_config()
        set_language(cfg.get("language", "tr"))
    except Exception:
        pass

load_language_from_config()

# --- Deleted ToolTip, ValidationHelper, ValidatedEntry (Moved to ui.widgets) ---


class GasFlowCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{t('app_title')} V{APP_VERSION}")
        self.root.geometry("1450x950")
        self.root.minsize(1100, 800)

        # Hesaplama Motoru
        self.calculator = GasFlowCalculator()
        self.calculator.set_log_callback(self.log_message)
        # Güncelleme yöneticisi
        self.updater = Updater(self.log_message)
        self.last_download_path = None

        # Değişkenler
        self.gas_components = {}
        self.fitting_counts = {}
        self.ball_valve_kv = tk.DoubleVar(value=0.0)
        self.ball_valve_cv = tk.DoubleVar(value=0.0)
        self.log_queue = queue.Queue()
        self.calc_queue = queue.Queue()
        
        # Validasyon ve Yardımcılar
        self.validation = ValidationHelper()
        self.gas_components = {} # {id: StringVar}
        self.fitting_counts = {} # {name: IntVar}
        self.ball_valve_kv = tk.DoubleVar()
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
        """Uygulama açılışında istenen varsayılan değerleri ayarlar."""
        # Hesaplama Hedefini Min Çap Yap
        self.calc_target.set(t("target_min_diameter"))
        
        # İstenen Gazları Ekle ve Değerlerini Gir
        defaults = {
            "METHANE": "98.0",
            "ETHANE": "1.0",
            "NITROGEN": "0.5",
            "CARBONDIOXIDE": "0.5"
        }
        
        for gas_id, value in defaults.items():
            self.gas_combo.set(COOLPROP_GASES[gas_id]["name"])
            self.add_gas_component()
            self.gas_components[gas_id].set(value)
            
        self.gas_combo.set(t("select_gas"))
        self.update_gas_total()

    def check_changelog(self):
        try:
            cfg = load_app_config()
            dismissed_version = cfg.get("dismissed_release_notes_version")
            if dismissed_version != APP_VERSION:
                self.root.after(1000, self.show_changelog_dialog)
        except Exception:
            pass

    def show_changelog_dialog(self):
        language = get_language()
        top = tk.Toplevel(self.root)
        top.title(get_release_notes_title(APP_VERSION, language))
        top.geometry("650x500")
        top.transient(self.root)
        top.grab_set()

        txt = ScrolledText(top, wrap="word", font=("Segoe UI", 10))
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
                except Exception:
                    pass
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
    
    def _get_session_file_path(self):
        """Dil değişikliği oturum dosyasının yolunu döndürür."""
        return get_session_file_path()
    
    def _save_session_for_lang_change(self):
        """Dil değişikliği öncesinde oturum verilerini geçici dosyaya kaydeder."""
        try:
            session_data = self.get_ui_state()
            session_path = self._get_session_file_path()
            with open(session_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_message(f"Oturum kaydetme hatası: {e}", level="WARNING")
    
    def _restore_session_after_lang_change(self):
        """Dil değişikliği sonrasında oturum verilerini geri yükler ve geçici dosyayı siler."""
        session_path = self._get_session_file_path()
        if not os.path.exists(session_path):
            return
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            self.set_ui_state(session_data)
            os.remove(session_path)
            self.log_message(t("msg_program_started") + " - " + "Session restored after language change.", level="INFO")
        except Exception as e:
            self.log_message(f"Oturum geri yükleme hatası: {e}", level="WARNING")
            try:
                os.remove(session_path)
            except OSError:
                pass
    
    def show_user_guide(self):
        show_user_guide(self.root)
    
    def show_about(self):
        show_about(self.root, APP_VERSION)
    
    def show_program_details(self):
        show_program_details(self.root)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # ── Renk Sistemi ─────────────────────────────────────
        BG          = "#f0f3f8"        # Ana arka plan (soğuk gri)
        CARD        = "#ffffff"        # Panel / kart arka planı
        ACCENT      = "#1a237e"        # Koyu lacivert ana vurgu rengi
        ACCENT2     = "#283593"        # Biraz açık vurgu
        ACCENT_LIGHT= "#e8eaf6"        # Açık lacivert (hover / highlight)
        TXT_DARK    = "#1c2032"        # Koyu metin
        TXT_MID     = "#455a64"        # Orta metin
        TXT_LIGHT   = "#78909c"        # Açık metin / hint
        SUCCESS     = "#2e7d32"
        WARN        = "#e65100"
        ERR         = "#c62828"
        # ─────────────────────────────────────────────────────

        # Global
        style.configure(".",
                        background=BG,
                        foreground=TXT_DARK,
                        font=("Segoe UI", 10),
                        focuscolor=ACCENT2)

        # ── Frame'ler ──
        style.configure("TFrame",  background=BG)
        style.configure("Card.TFrame", background=CARD, relief="flat")

        # ── LabelFrame (Panel Kartları) ──
        style.configure("TLabelframe",
                        background=CARD,
                        relief="flat",
                        borderwidth=1,
                        bordercolor="#dee2e6")
        style.configure("TLabelframe.Label",
                        background=CARD,
                        foreground=ACCENT,
                        font=("Segoe UI", 10, "bold"))
        style.configure("Bold.TLabelframe.Label",
                        background=CARD,
                        foreground=ACCENT,
                        font=("Segoe UI", 10, "bold"))

        # ── Notebook (Sekmeler) ──
        style.configure("TNotebook",
                        background=BG,
                        tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab",
                        background="#d1d8e6",
                        foreground=TXT_MID,
                        padding=[10, 5],
                        font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", ACCENT)],
                  font=[("selected", ("Segoe UI", 9, "bold"))])

        # ── Butonlar ──
        style.configure("TButton",
                        font=("Segoe UI", 10),
                        padding=[8, 5],
                        background="#dde3ef",
                        foreground=TXT_DARK,
                        relief="flat")
        style.map("TButton",
                  background=[("active", ACCENT_LIGHT), ("pressed", "#c5cae9")])

        # Seçim butonları (Hesaplama Hedefi)
        style.configure("SegBtn.TButton",
                        font=("Segoe UI", 9),
                        padding=[8, 4],
                        background="#dde3ef",
                        foreground=TXT_MID,
                        relief="flat")
        style.map("SegBtn.TButton",
                  background=[("active", ACCENT_LIGHT)])

        style.configure("SegBtnActive.TButton",
                        font=("Segoe UI", 9, "bold"),
                        padding=[8, 4],
                        background=ACCENT,
                        foreground="#ffffff",
                        relief="flat")
        style.map("SegBtnActive.TButton",
                  background=[("active", ACCENT2)])

        # ── Label'lar ──
        style.configure("TLabel",    background=CARD, foreground=TXT_DARK, font=("Segoe UI", 10))
        style.configure("Header.TLabel",
                        font=("Segoe UI", 14, "bold"),
                        foreground=ACCENT,
                        background=CARD)
        style.configure("Sub.TLabel",
                        font=("Segoe UI", 9),
                        foreground=TXT_LIGHT,
                        background=CARD)
        style.configure("Hint.TLabel",
                        font=("Segoe UI", 9, "italic"),
                        foreground=TXT_LIGHT,
                        background=CARD)

        # ── Treeview ──
        style.configure("Treeview",
                        font=("Segoe UI", 9),
                        rowheight=26,
                        background=CARD,
                        fieldbackground=CARD,
                        foreground=TXT_DARK)
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background=ACCENT_LIGHT,
                        foreground=ACCENT)
        style.map("Treeview",
                  background=[("selected", ACCENT_LIGHT)],
                  foreground=[("selected", ACCENT)])

        # ── Entry (Giriş Kutusu) ──
        style.configure("TEntry",
                        padding=[4, 3],
                        relief="flat",
                        foreground=TXT_DARK)
        style.map("TEntry",
                  fieldbackground=[("focus", "#eef2ff")])

        # ── Combobox ──
        style.configure("TCombobox", padding=[4, 3], relief="flat")

        # ── Scrollbar ──
        style.configure("TScrollbar", background="#ced4da", troughcolor=CARD, relief="flat")
        style.map("TScrollbar", background=[("active", ACCENT_LIGHT)])

        # Root arka planı
        self.root.configure(bg=BG)

        # Paylaşımlı renk sabitlerini sakla (paneller kullanabilsin)
        self._colors = {
            'bg': BG, 'card': CARD, 'accent': ACCENT, 'accent2': ACCENT2,
            'accent_light': ACCENT_LIGHT, 'txt_dark': TXT_DARK,
            'txt_mid': TXT_MID, 'txt_light': TXT_LIGHT,
            'success': SUCCESS, 'warn': WARN, 'err': ERR
        }

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
        
        self.process_panel = ProcessPanel(left_panel, self)
        self.process_panel.pack(fill="x", pady=5)
        
        self.pipe_panel = PipePanel(left_panel, self)
        self.pipe_panel.pack(fill="x", pady=5)

        # --- SAĞ PANEL (RAPOR) ---
        self.results_panel = ResultsPanel(right_panel, self)
        self.results_panel.pack(fill="both", expand=True)
    
    def _draw_progress_button(self, text, progress, idle=False):
        """Progress button'u çiz."""
        canvas = self.progress_canvas
        canvas.delete("all")
        
        width = canvas.winfo_width() or 400
        height = canvas.winfo_height() or 50
        
        if idle:
            # Bekleme durumu - düz yeşil
            canvas.create_rectangle(0, 0, width, height, fill="#28a745", outline="")
            canvas.create_text(width/2, height/2, text=text, 
                             font=("Segoe UI", 12, "bold"), fill="white")
        else:
            # İlerleme durumu - gri arka plan + yeşil ilerleme
            # Arka plan (gri)
            canvas.create_rectangle(0, 0, width, height, fill="#6c757d", outline="")
            
            # İlerleme çubuğu (yeşil)
            progress_width = (progress / 100) * width
            if progress_width > 0:
                canvas.create_rectangle(0, 0, progress_width, height, fill="#28a745", outline="")
            
            # Metin
            canvas.create_text(width/2, height/2, text=text, 
                             font=("Segoe UI", 12, "bold"), fill="white")
    
    def _on_progress_hover(self, event):
        """Mouse hover efekti."""
        if not self.is_calculating:
            self.progress_canvas.config(cursor="hand2")
            self._draw_progress_button(t("btn_calculate"), 0, idle=True)
            # Hafif parlama efekti
            self.progress_canvas.itemconfig("all", fill="")
            width = self.progress_canvas.winfo_width() or 400
            height = self.progress_canvas.winfo_height() or 50
            self.progress_canvas.delete("all")
            self.progress_canvas.create_rectangle(0, 0, width, height, fill="#2dbe50", outline="")
            self.progress_canvas.create_text(width/2, height/2, text=t("btn_calculate"), 
                                            font=("Segoe UI", 12, "bold"), fill="white")
    
    def _on_progress_leave(self, event):
        """Mouse leave efekti."""
        if not self.is_calculating:
            self._draw_progress_button(t("btn_calculate"), 0, idle=True)
    
    def _on_progress_resize(self, event):
        """Pencere boyutu değiştiğinde butonu yeniden çiz."""
        if not self.is_calculating:
            self._draw_progress_button(t("btn_calculate"), 0, idle=True)
    
    def update_progress(self, value, status_text=None):
        """İlerleme durumunu güncelle."""
        self.progress_value = min(100, max(0, value))
        text = status_text or f"{t('calculating_progress')}{int(self.progress_value)}"
        self._draw_progress_button(text, self.progress_value, idle=False)
        self.progress_canvas.update_idletasks()
    
    def reset_progress_button(self):
        """Progress button'u başlangıç durumuna getir."""
        self.is_calculating = False
        self.progress_value = 0
        self._draw_progress_button(t("btn_calculate"), 0, idle=True)
        self.progress_canvas.config(cursor="hand2")
    
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
        # Hesaplama sonuçlarını temizle (yeni hedef seçildi)
        if event and event.widget == self.calc_target:
            self.schematic_state = "pending"
            self.last_result = None
            # UI görünürlüğünü güncelle (hedef değişti)
            self.update_ui_visibility()
        self.refresh_schematic()
    
    def _schedule_schematic_update(self, *args):
        """Şema güncellemesini 300ms gecikmeyle planla (debounce)."""
        if self._schematic_update_timer:
            self.root.after_cancel(self._schematic_update_timer)
        self._schematic_update_timer = self.root.after(300, self.refresh_schematic)
    
    def refresh_schematic(self):
        """Şemayı yeniden çiz."""
        if hasattr(self, 'schematic_canvas'):
            self.draw_schematic()



    def create_log_tab_content(self, parent):
        self.log_panel = LogPanel(parent, self)
        self.log_panel.pack(fill="both", expand=True)

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
        # Tabloyu temizle
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
            
        current_filter = self.log_filter_var.get()
        
        # Yeniden doldur
        for entry in self.all_logs:
            if current_filter == t("log_all") or entry["level"] == current_filter:
                self.log_tree.insert("", "end", values=(entry["time"], entry["level"], entry["message"]), tags=(entry["level"],))
        
        self.log_tree.yview_moveto(1)

    def clear_logs(self):
        self.all_logs.clear()
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

    def create_footer(self):
        footer = tk.Frame(self.root, bg="#1a237e", height=26)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        # Sol: Uygulama adı
        tk.Label(footer,
                 text=f"  Gas Flow Calc V{APP_VERSION}  |  © 2025 Mühendislik Araçları",
                 font=("Segoe UI", 8), bg="#1a237e", fg="#c5cae9").pack(side="left")

        # Sağ: Durum etiketleri
        self.footer_status = tk.Label(footer, text="Hazır",
                                      font=("Segoe UI", 8, "bold"),
                                      bg="#1a237e", fg="#a5d6a7")
        self.footer_status.pack(side="right", padx=8)

        self.footer_model = tk.Label(footer, text="",
                                     font=("Segoe UI", 8),
                                     bg="#1a237e", fg="#90caf9")
        self.footer_model.pack(side="right", padx=8)

        self.footer_time = tk.Label(footer, text="",
                                    font=("Segoe UI", 8),
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
        except Exception:
            pass

    # --- İŞLEVSELLİK ---
    
    def filter_gas_list(self, *args):
        search = self.gas_search_var.get().lower()
        filtered = [g["name"] for g in COOLPROP_GASES.values() if search in g["name"].lower()]
        self.gas_combo['values'] = filtered
        if filtered: self.gas_combo.current(0)

    def _clamp_fitting_value(self, var):
        """Fitting değerini negatifse 0'a sabitle."""
        try:
            val = var.get()
            if val < 0:
                var.set(0)
        except (tk.TclError, ValueError):
            pass

    def add_gas_component(self):
        gas_name = self.gas_combo.get()
        if not gas_name or gas_name == t("select_gas"): return
        
        gas_id = next(k for k, v in COOLPROP_GASES.items() if v["name"] == gas_name)
        if gas_id in self.gas_components: return
        
        # StringVar kullan (virgül desteği için)
        var = tk.StringVar(value="0")
        self.gas_components[gas_id] = var
        
        row_frame = ttk.Frame(self.gas_list_inner)
        row_frame.pack(fill="x", pady=2)
        ttk.Label(row_frame, text=gas_name, width=25).pack(side="left")
        
        # Entry - StringVar ile bağlı
        entry = ttk.Entry(row_frame, textvariable=var, width=8)
        entry.pack(side="left", padx=5)
        
        # Her tuş vuruşunda ve değer değiştiğinde toplamı güncelle
        entry.bind("<KeyRelease>", lambda e: self.update_gas_total())
        var.trace_add("write", lambda *args: self.update_gas_total())
        
        ttk.Button(row_frame, text="X", width=3, command=lambda: self.remove_gas(gas_id, row_frame)).pack(side="left")
        
        self.update_gas_total()

    def remove_gas(self, gas_id, widget):
        del self.gas_components[gas_id]
        widget.destroy()
        self.update_gas_total()
    
    def update_gas_total(self, *args):
        """Gaz bileşimi toplamını hesapla ve göster."""
        total = 0.0
        for var in self.gas_components.values():
            try:
                # StringVar'dan string al ve normalize et
                val_str = var.get()
                normalized = ValidationHelper.normalize_number(val_str)
                if normalized:
                    val = float(normalized)
                    total += val
            except (ValueError, AttributeError, tk.TclError):
                pass
        
        # Toplam göstergesini güncelle
        self.gas_total_label.config(text=f"{total:.2f} %")

        # — Doluluk çubuğunu güncelle —
        try:
            bar_w = self.gas_total_bar.master.winfo_width()
            if bar_w > 2:
                fill_px = int(min(1.0, total / 100.0) * bar_w)
                self.gas_total_bar.place(x=0, y=0, relheight=1.0,
                                        width=fill_px)
                if abs(total - 100.0) <= 0.01:
                    self.gas_total_bar.config(bg="#2e7d32")
                elif total > 100:
                    self.gas_total_bar.config(bg="#c62828")
                else:
                    self.gas_total_bar.config(bg="#43a047")
        except Exception:
            pass

        # Durum kontrolü
        tolerance = 0.01  # %0.01 tolerans
        if abs(total - 100.0) <= tolerance:
            # Tam %100 - Yeşil
            self.gas_total_label.config(fg="#2e7d32")  # Koyu yeşil
            self.gas_status_label.config(text="✓", fg="#2e7d32")
        elif total == 0:
            # Boş - Gri
            self.gas_total_label.config(fg="#666")
            self.gas_status_label.config(text="", fg="#666")
        else:
            # %100 değil - Turuncu uyarı
            diff = total - 100.0
            sign = "+" if diff > 0 else ""
            self.gas_total_label.config(fg="#e65100")  # Turuncu
            self.gas_status_label.config(text=f"({sign}{diff:.2f}%)", fg="#e65100")
    
    def check_gas_composition(self):
        """
        Gaz bileşimi toplamını kontrol eder.
        Returns: (is_100_percent, total, normalized_fractions, user_confirmed)
        """
        total = 0.0
        raw_values = {}
        
        for gas_id, var in self.gas_components.items():
            val = self.get_float_value(var, 0)
            if val is not None and val > 0:
                raw_values[gas_id] = val
                total += val
        
        if total <= 0:
            return (False, 0, {}, False, "Gaz bileşenleri toplamı 0'dan büyük olmalıdır.")
        
        tolerance = 0.01  # %0.01 tolerans
        
        if abs(total - 100.0) <= tolerance:
            # Tam %100 - Normalize et ve devam
            normalized = {k: v / total for k, v in raw_values.items()}
            return (True, total, normalized, True, None)
        
        # %100 değil - Kullanıcıya sor
        diff = total - 100.0
        sign = "+" if diff > 0 else ""
        
        msg = (
            f"⚠️ GAZ BİLEŞİMİ UYARISI\n\n"
            f"Girilen gaz bileşimi toplamı: {total:.2f}%\n"
            f"Fark: {sign}{diff:.2f}%\n\n"
            f"Hesaplamaya devam etmek ister misiniz?\n\n"
            f"'Evet' seçerseniz:\n"
            f"  • Bileşenler ağırlıklı ortalamalarına göre\n"
            f"    %100'e normalize edilecek.\n"
            f"  • Orijinal oranlar korunacak.\n\n"
            f"'Hayır' seçerseniz:\n"
            f"  • Hesaplama iptal edilecek.\n"
            f"  • Değerleri manuel düzeltebilirsiniz."
        )
        
        user_choice = messagebox.askyesno("Gaz Bileşimi Kontrolü", msg, icon="warning")
        
        if user_choice:
            # Kullanıcı devam etmek istiyor - normalize et
            normalized = {k: v / total for k, v in raw_values.items()}
            return (False, total, normalized, True, None)
        else:
            # Kullanıcı iptal etti
            return (False, total, {}, False, "Hesaplama kullanıcı tarafından iptal edildi.")

    def _on_nps_changed(self, event=None):
        """NPS seçildiğinde ilgili Schedule listesini güncelle."""
        nps = self.nps_combo.get()
        if nps in ASME_B36_10M_DATA:
            data = ASME_B36_10M_DATA[nps]
            schedules = list(data["schedules"].keys())
            self.schedule_combo.config(values=schedules)
            self.schedule_combo.set("")  # Temizle
            # OD'yi otomatik doldur ve kilitle
            self.diam_var.set(data["OD_mm"])
            self.thick_var.set(0)
            self.ent_diam.config(state="readonly")
            self.ent_thick.config(state="readonly")

    def _on_schedule_changed(self, event=None):
        """Schedule seçildiğinde OD ve WT'yi otomatik doldur."""
        nps = self.nps_combo.get()
        schedule = self.schedule_combo.get()
        if nps in ASME_B36_10M_DATA and schedule:
            data = ASME_B36_10M_DATA[nps]
            self.diam_var.set(data["OD_mm"])
            wt = data["schedules"].get(schedule, 0)
            self.thick_var.set(wt)
            self.ent_diam.config(state="readonly")
            self.ent_thick.config(state="readonly")

    def _toggle_fittings(self):
        """Boru elemanları panelini aç/kapat."""
        if self._fittings_visible:
            self.fit_frame.pack_forget()
            self.fit_toggle_btn.config(text=t("toggle_fittings_show"))
        else:
            self.fit_frame.pack(fill="x", pady=(0, 10))
            self.fit_toggle_btn.config(text=t("toggle_fittings_hide"))
        self._fittings_visible = not self._fittings_visible

    def _on_preset_selected(self, event=None):
        """Hazır gaz karışımı seçildiğinde bileşenleri yükle."""
        preset_name = self.gas_preset_combo.get()
        if preset_name == t("gas_preset_select") or preset_name not in GAS_PRESETS:
            return
        
        # Mevcut gazları temizle
        for widget in self.gas_list_inner.winfo_children():
            widget.destroy()
        self.gas_components.clear()
        
        # Preset'teki gazları ekle
        preset = GAS_PRESETS[preset_name]
        for gas_id, percentage in preset.items():
            gas_name = COOLPROP_GASES.get(gas_id, {}).get("name", gas_id)
            var = tk.StringVar(value=str(percentage))
            self.gas_components[gas_id] = var
            
            row_frame = ttk.Frame(self.gas_list_inner)
            row_frame.pack(fill="x", pady=2)
            ttk.Label(row_frame, text=gas_name, width=25).pack(side="left")
            
            entry = ttk.Entry(row_frame, textvariable=var, width=8)
            entry.pack(side="left", padx=5)
            entry.bind("<KeyRelease>", lambda e: self.update_gas_total())
            var.trace_add("write", lambda *args: self.update_gas_total())
            
            ttk.Button(row_frame, text="X", width=3, command=lambda gid=gas_id, w=row_frame: self.remove_gas(gid, w)).pack(side="left")
        
        self.update_gas_total()

    def _on_material_changed(self, event=None):
        """Malzeme seçildiğinde SMYS'yi güncelle. Manuel seçimde SMYS düzenlenebilir."""
        material = self.material_combo.get()
        if material == "Manuel / Custom":
            self.ent_smys.config(state="normal")
            self.smys_var.set(0)  # Kullanıcı girsin
        else:
            smys = PIPE_MATERIALS.get(material, 0)
            self.smys_var.set(smys)
            self.ent_smys.config(state="disabled")

    def update_ui_visibility(self, event=None):
        target = self.calc_target.get()
        
        # Temizle
        self.lbl_len.grid_remove(); self.ent_len.grid_remove()
        self.lbl_target_p.grid_remove(); self.ent_target_p.grid_remove(); self.target_p_unit.grid_remove()
        self.lbl_max_vel.grid_remove(); self.ent_max_vel.grid_remove()
        
        # Tasarım Kriterleri: sadece Min.Çap modunda göster
        if target == t("target_min_diameter"):
            self.design_frame.pack(fill="x", pady=5)
        else:
            self.design_frame.pack_forget()
        
        if target == t("target_pressure_drop"):
            self.lbl_len.grid(row=0, column=4, padx=(15, 5)); self.ent_len.grid(row=0, column=5)
            self.pipe_panel.pack(fill="x", pady=5) # Göster
        elif target == t("target_max_length"):
            self.lbl_target_p.grid(row=0, column=4, padx=(15, 5)); self.ent_target_p.grid(row=0, column=5)
            self.target_p_unit.grid(row=0, column=6, padx=5)
            self.pipe_panel.pack(fill="x", pady=5) # Göster
        elif target == t("target_min_diameter"):
            self.lbl_max_vel.grid(row=0, column=4, padx=(15, 5)); self.ent_max_vel.grid(row=0, column=5)
            
            # Sıkıştırılabilir akış ise Uzunluk da gerekli
            if self.flow_type.get() == t("flow_compressible"):
                self.lbl_len.grid(row=0, column=6, padx=(15, 5)); self.ent_len.grid(row=0, column=7)

    def save_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.report_text.get(1.0, "end"))
            messagebox.showinfo(t("dialog_success"), t("report_saved"))

    def save_project(self):
        try:
            data = self.get_ui_state()
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                messagebox.showinfo(t("dialog_success"), t("project_saved"))
        except Exception as e:
            messagebox.showerror(t("dialog_error"), f"{t('save_error')}: {str(e)}")

    def load_project(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
            if path:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.set_ui_state(data)
                messagebox.showinfo(t("dialog_success"), t("project_loaded"))
        except Exception as e:
            messagebox.showerror(t("dialog_error"), f"{t('load_error')}: {str(e)}")

    def get_ui_state(self):
        # Gaz Bileşimi
        gas_data = {gas_id: var.get() for gas_id, var in self.gas_components.items()}
        
        # Fittings
        fitting_data = {name: var.get() for name, var in self.fitting_counts.items()}
        
        return {
            "gas_components": gas_data,
            "comp_type": self.comp_type.get(),
            "p_in": self.p_in_var.get(), "p_unit": self.p_unit.get(),
            "t_val": self.t_var.get(), "t_unit": self.t_unit.get(),
            "flow_val": self.flow_var.get(), "flow_unit": self.flow_unit.get(),
            "calc_target": self.calc_target.get(),
            "thermo_model": self.thermo_model.get(),
            "flow_type": self.flow_type.get(),
            "material": self.material_combo.get(),
            "opt_weight": self.opt_weight_var.get(),
            "fast_calc": self.fast_calc_var.get(),
            "len_val": self.len_var.get(),
            "diam_val": self.diam_var.get(),
            "thick_val": self.thick_var.get(),
            "nps_val": self.nps_combo.get(),
            "schedule_val": self.schedule_combo.get(),
            "smys_val": self.smys_var.get(),
            "target_p_val": self.target_p_var.get(), "target_p_unit": self.target_p_unit.get(),
            "max_vel_val": self.max_vel_var.get(),
            "p_design_val": self.p_design_var.get(), "p_design_unit": self.p_design_unit.get(),
            "factor_f": self.factor_f.get(), "factor_e": self.factor_e.get(), "factor_t": self.factor_t.get(),
            "fitting_counts": fitting_data,
            "ball_valve_kv": self.ball_valve_kv.get()
        }

    def set_ui_state(self, data):
        # Önce mevcut gazları temizle
        for widget in self.gas_list_inner.winfo_children():
            widget.destroy()
        self.gas_components.clear()
        
        # Gazları Yükle
        for gas_id, val in data.get("gas_components", {}).items():
            # StringVar kullan (virgül desteği için)
            var = tk.StringVar(value=str(val))
            self.gas_components[gas_id] = var
            
            # İsim bul
            gas_name = next((v for k, v in COOLPROP_GASES.items() if k == gas_id), gas_id)
            
            row_frame = ttk.Frame(self.gas_list_inner)
            row_frame.pack(fill="x", pady=2)
            ttk.Label(row_frame, text=gas_name, width=25).pack(side="left")
            
            entry = ttk.Entry(row_frame, textvariable=var, width=8)
            entry.pack(side="left", padx=5)
            entry.bind("<KeyRelease>", lambda e: self.update_gas_total())
            var.trace_add("write", lambda *args: self.update_gas_total())
            
            ttk.Button(row_frame, text="X", width=3, command=lambda gid=gas_id, w=row_frame: self.remove_gas(gid, w)).pack(side="left")
        
        # Gaz toplamını güncelle
        self.update_gas_total()

        self.comp_type.set(data.get("comp_type", "Mol %"))
        self.p_in_var.set(data.get("p_in", 0))
        self.p_unit.set(data.get("p_unit", "Barg"))
        self.t_var.set(data.get("t_val", 25))
        self.t_unit.set(data.get("t_unit", "°C"))
        self.flow_var.set(data.get("flow_val", 0))
        self.flow_unit.set(data.get("flow_unit", "Sm³/h"))
        self.calc_target.set(data.get("calc_target", t("target_pressure_drop")))
        self.thermo_model.set(data.get("thermo_model", "CoolProp (High Accuracy EOS)"))
        self.flow_type.set(data.get("flow_type", "Sıkıştırılamaz"))
        self.material_combo.set(data.get("material", "API 5L Grade B"))
        self._on_material_changed()  # SMYS güncelle
        if "smys_val" in data:
            self.smys_var.set(data["smys_val"])
        # NPS / Schedule geri yükle
        nps_val = data.get("nps_val", "")
        if nps_val:
            self.nps_combo.set(nps_val)
            self._on_nps_changed()  # Schedule listesini güncelle
            schedule_val = data.get("schedule_val", "")
            if schedule_val:
                self.schedule_combo.set(schedule_val)
        self.len_var.set(data.get("len_val", 100))
        self.diam_var.set(data.get("diam_val", 0))
        self.thick_var.set(data.get("thick_val", 0))
        self.target_p_var.set(data.get("target_p_val", 0))
        self.target_p_unit.set(data.get("target_p_unit", "Barg"))
        self.max_vel_var.set(data.get("max_vel_val", 20))
        self.p_design_var.set(data.get("p_design_val", 0))
        self.p_design_unit.set(data.get("p_design_unit", "Barg"))
        self.factor_f.set(data.get("factor_f", 0.72))
        self.factor_e.set(data.get("factor_e", 1.0))
        self.factor_t.set(data.get("factor_t", 1.0))
        self.ball_valve_kv.set(data.get("ball_valve_kv", 0))

        # Fittings
        fit_data = data.get("fitting_counts", {})
        for name, val in fit_data.items():
            if name in self.fitting_counts:
                self.fitting_counts[name].set(val)
        
        self.update_ui_visibility()

    def validate_inputs(self):
        """Kullanıcı girişlerini doğrular."""
        errors = []
        
        # 1. Gaz Bileşimi
        if not self.gas_components:
            errors.append("Lütfen en az bir gaz bileşeni ekleyin.")
        else:
            total_mole = sum(self.get_float_value(var, 0) for var in self.gas_components.values())
            if total_mole <= 0:
                errors.append("Toplam mol oranı 0'dan büyük olmalıdır.")
        
        # 2. Temel Parametreler
        if self.get_float_value(self.p_in_var, 0) <= 0: errors.append("Giriş basıncı pozitif olmalıdır.")
        if self.get_float_value(self.t_var, 25) <= -273.15: errors.append("Sıcaklık mutlak sıfırdan büyük olmalıdır.")
        if self.get_float_value(self.flow_var, 0) <= 0: errors.append("Akış debisi pozitif olmalıdır.")
        
        target = self.calc_target.get()
        
        # 3. Hedefe Özel Kontroller
        if target == t("target_pressure_drop"):
            if self.get_float_value(self.len_var, 0) <= 0: errors.append("Boru uzunluğu pozitif olmalıdır.")
            if self.get_float_value(self.diam_var, 0) <= 0: errors.append("Boru çapı pozitif olmalıdır.")
            diam = self.get_float_value(self.diam_var, 0)
            thick = self.get_float_value(self.thick_var, 0)
            if thick >= diam / 2: errors.append("Et kalınlığı yarıçaptan küçük olmalıdır.")
            
        elif target == t("target_max_length"):
            if self.get_float_value(self.target_p_var, 0) <= 0: errors.append("Hedef çıkış basıncı pozitif olmalıdır.")
            if self.get_float_value(self.diam_var, 0) <= 0: errors.append("Boru çapı pozitif olmalıdır.")
            
        elif target == t("target_min_diameter"):
            if self.get_float_value(self.max_vel_var, 0) <= 0: errors.append("Maksimum hız limiti pozitif olmalıdır.")
            if self.get_float_value(self.p_design_var, 0) <= 0: errors.append("Tasarım basıncı pozitif olmalıdır.")
            if self.flow_type.get() == t("flow_compressible") and self.get_float_value(self.len_var, 0) <= 0:
                errors.append("Sıkıştırılabilir akış çap hesabı için boru uzunluğu gereklidir.")

        if errors:
            messagebox.showwarning("Giriş Hatası", "\n".join(errors))
            return False
        return True

    # --- HESAPLAMA BAŞLATMA ---
    def start_calculation(self):
        # 0. Temel Validasyon
        if not self.validate_inputs(): return
        
        # 1. Gaz Bileşimi Kontrolü
        is_exact, total, mole_fractions, confirmed, error_msg = self.check_gas_composition()
        
        if error_msg:
            messagebox.showerror("Gaz Bileşimi Hatası", error_msg)
            return
        
        if not confirmed:
            return  # Kullanıcı iptal etti
        
        # Normalize bilgisi
        normalization_info = None
        if not is_exact:
            normalization_info = {
                "original_total": total,
                "message": f"Gaz bileşimi %{total:.2f} idi, %100'e normalize edildi."
            }
            self.log_message(f"⚠️ Gaz bileşimi normalize edildi: %{total:.2f} → %100", level="WARNING")

        # 2. Verileri Topla
        try:
            inputs = self.collect_inputs(mole_fractions_override=mole_fractions)
            inputs["normalization_info"] = normalization_info
        except ValueError as e:
            messagebox.showerror("Girdi Hatası", str(e))
            return

        # 3. Arayüzü Kilitle ve Progress Başlat
        self.is_calculating = True
        self.schematic_state = "calculating"
        self.update_progress(0, "Başlatılıyor...")
        self.progress_canvas.config(cursor="wait")
        self.refresh_schematic()
        self._update_footer("Hesaplanıyor...")
        self._calc_start_time = __import__('time').time()
        
        self.report_text.delete(1.0, "end")
        
        if normalization_info:
            self.report_text.insert("end", f"⚠️ {normalization_info['message']}\n\n")
        self.report_text.insert("end", "Hesaplama başlatıldı...\n")

        # 4. Thread Başlat
        threading.Thread(target=self.run_calculation_thread, args=(inputs,), daemon=True).start()
        
        # 5. Progress animasyonu başlat
        self._start_progress_animation()
        self.root.after(100, self.check_calc_queue)
    
    def _start_progress_animation(self):
        """Hesaplama süresince simüle edilmiş ilerleme animasyonu."""
        if not self.is_calculating:
            return
        
        # Yavaş yavaş ilerle ama %90'da dur (gerçek bitişi bekle)
        if self.progress_value < 90:
            # Hızlı başla, yavaşla
            increment = max(1, (90 - self.progress_value) / 20)
            self.progress_value = min(90, self.progress_value + increment)
            self.update_progress(self.progress_value)
        
        # Hala hesaplanıyorsa devam et (100ms arayla)
        if self.is_calculating and self.progress_value < 90:
            self.root.after(100, self._start_progress_animation)

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
    
    def collect_inputs(self, mole_fractions_override=None):
        """
        Hesaplama için gerekli tüm girdileri toplar.
        
        Args:
            mole_fractions_override: Önceden hesaplanmış ve normalize edilmiş mol fraksiyonları.
                                     None ise arayüzden hesaplanır.
        """
        # Gaz - Eğer override verilmişse onu kullan
        if mole_fractions_override is not None:
            mole_fractions = mole_fractions_override
        else:
            # Eski davranış - arayüzden hesapla
            if not self.gas_components: raise ValueError("En az bir gaz ekleyin.")
            total_pct = sum(self.get_float_value(v, 0) for v in self.gas_components.values())
            if total_pct <= 0: raise ValueError("Gaz yüzdeleri toplamı 0 olamaz.")
            
            mole_fractions = {k: self.get_float_value(v, 0)/total_pct for k, v in self.gas_components.items() if self.get_float_value(v, 0) > 0}
        
        if self.comp_type.get() == "Kütle %":
            mole_fractions = self.calculator.mass_to_mole_fraction(mole_fractions)

        # Basınç / Sıcaklık
        p_in_val = self.get_float_value(self.p_in_var, 0)
        p_unit = self.p_unit.get()
        # Birim Çevirme (Basitçe burada yapıyorum, normalde calculator'da da olabilir ama UI tarafında hazırlamak daha temiz)
        if p_unit == "Barg": P_in = (p_in_val + 1.01325) * 1e5
        elif p_unit == "Bara": P_in = p_in_val * 1e5
        elif p_unit == "Psig": P_in = (p_in_val + 14.696) * 6894.76
        else: P_in = p_in_val * 6894.76

        t_val = self.get_float_value(self.t_var, 25)
        t_unit = self.t_unit.get()
        if t_unit == "°C": T = t_val + 273.15
        elif t_unit == "°F": T = (t_val - 32) * 5/9 + 273.15
        else: T = t_val

        # Boru
        # Boru (Girdiler mm, hesaplama mm bekliyor)
        target = self.calc_target.get()
        D_outer = self.get_float_value(self.diam_var, 0)
        t_wall = self.get_float_value(self.thick_var, 0)
        
        # Eğer hedef Minimum Çap DEĞİLSE, Dış Çap ve Et Kalınlığı zorunludur.
        if target != t("target_min_diameter"):
            if D_outer <= 0: raise ValueError(t("validation_positive_diameter"))
            if t_wall <= 0: raise ValueError(t("validation_positive_thickness"))
            
        D_inner = D_outer - 2 * t_wall
        # Minimum çap hesabında başlangıç için D_inner 0 olabilir, hata vermesin.
        if target != t("target_min_diameter") and D_inner <= 0: 
            raise ValueError(t("validation_invalid_geometry"))

        # Fittings K
        total_k = 0
        for name, var in self.fitting_counts.items():
            count = self.get_int_value(var, 0)
            if count > 0:
                k = FITTING_K_FACTORS[name]
                # Vana Kv hesabı eklenebilir (basitlik için atlıyorum, V4'teki gibi eklenebilir)
                total_k += k * count

        flow_rate = self.get_float_value(self.flow_var, 0)
        len_val = self.get_float_value(self.len_var, 100)
        max_vel = self.get_float_value(self.max_vel_var, 20)
        factor_f = self.get_float_value(self.factor_f, 0.72)
        factor_e = self.get_float_value(self.factor_e, 1.0)
        factor_t = self.get_float_value(self.factor_t, 1.0)

        return {
            "P_in": P_in, "T": T, "mole_fractions": mole_fractions,
            "library_choice": self.thermo_model.get(),
            "flow_rate": flow_rate, "flow_unit": self.flow_unit.get(),
            "D_inner": D_inner, "L": len_val,
            "roughness": PIPE_ROUGHNESS.get(self.material_combo.get(), 4.57e-5),
            "total_k": total_k,
            "flow_property": self.flow_type.get(),
            "target": self.calc_target.get(),
            "P_out_target": self.convert_pressure_to_pa(self.get_float_value(self.target_p_var, 0), self.target_p_unit.get(), output_type="absolute") if self.calc_target.get() == t("target_max_length") else 0,
            
            # Min Çap İçin Ekler
            "max_velocity": max_vel,
            "optimize_weight": self.opt_weight_var.get(),
            "fast_calculation": self.fast_calc_var.get(),
            "P_design": self.convert_pressure_to_pa(self.get_float_value(self.p_design_var, 0), self.p_design_unit.get(), output_type="gauge"), # Barlow için Gauge
            "material": self.material_combo.get(),
            "SMYS": self.get_float_value(self.smys_var, 0),
            "F": factor_f, "E": factor_e, "T_factor": factor_t
        }

    def convert_pressure_to_pa(self, val, unit, output_type="absolute"):
        # output_type: "absolute" veya "gauge"
        
        # Önce Mutlak (Absolute) Pa'ya çevir
        abs_pa = 0
        if unit == "Barg": abs_pa = (val + 1.01325) * 1e5
        elif unit == "Bara": abs_pa = val * 1e5
        elif unit == "Psig": abs_pa = (val + 14.696) * 6894.76
        elif unit == "Psia": abs_pa = val * 6894.76
        
        if output_type == "absolute":
            return abs_pa
        else: # gauge
            return max(0, abs_pa - 101325)

    def run_calculation_thread(self, inputs):
        try:
            # Her yeni hesaplama için termodinamik cache'i temizle
            # (Gaz bileşimi veya koşullar değişmiş olabilir)
            self.calculator.clear_thermo_cache()
            
            target = inputs['target']
            result = None
            
            if target == t("target_pressure_drop"):
                result = self.calculator.calculate_pressure_drop(inputs)
                report = self.format_pressure_drop_report(inputs, result)
            elif target == t("target_max_length"):
                result = self.calculator.calculate_max_length(inputs)
                report = self.format_max_length_report(inputs, result)
            elif target == t("target_min_diameter"):
                result = self.calculator.calculate_min_diameter(inputs)
                report = self.format_min_diameter_report(inputs, result)
            else:
                report = "Bu özellik henüz V5 arayüzüne tam entegre edilmedi."

            self.calc_queue.put(("SUCCESS", {"report": report, "result": result}))
        except Exception as e:
            self.calc_queue.put(("ERROR", str(e)))

    def check_calc_queue(self):
        try:
            status, data = self.calc_queue.get_nowait()
            
            # Hesaplama tamamlandı - progress'i %100 yap
            self.update_progress(100, "Tamamlandı!")
            self.root.after(500, self.reset_progress_button)  # 0.5 sn sonra sıfırla
            
            if status == "SUCCESS":
                elapsed_ms = int((__import__('time').time() - getattr(self, '_calc_start_time', 0)) * 1000)
                self._update_footer("Tamamlandı", calc_time_ms=elapsed_ms)
                self.report_text.delete(1.0, "end")
                self.report_text.insert("end", data['report'])
                self.last_result = data['result'] # Sonucu sakla
                
                # Şema durumunu güncelle
                self.schematic_state = "completed"
                self.last_calculation_time = time.strftime("%H:%M:%S")
                self.refresh_schematic()  # Şemayı sonuçlarla güncelle
                
                # Tabloyu ve Profili Doldur
                self.populate_results_table(data['result'])
                self.populate_profile_table(data['result'])
                self._update_warning_banner(data['result'])
                
                # Gömülü Grafikleri Çiz
                show_graphs(self.charts_container, data['result'])
                
                self.res_notebook.select(self.tab_table) # Tabloyu göster
                
                self.log_message("✓ Hesaplama başarıyla tamamlandı.", level="INFO")
            else:
                self._update_footer("Hata")
                messagebox.showerror("Hesaplama Hatası", data)
                self.report_text.insert("end", f"\nHATA: {data}")
                
                # Şema durumunu hata olarak güncelle
                self.schematic_state = "error"
                self.refresh_schematic()
                
                self.log_message(f"✗ Hesaplama hatası: {data}", level="ERROR")
        except queue.Empty:
            self.root.after(100, self.check_calc_queue)

    def _update_warning_banner(self, result):
        """Hesaplama sonucuna göre uyarı afişini yönetir."""
        self.warning_card.pack_forget()
        status = result.get("choked_status", "N/A")
        
        if status != "OK" and status != "N/A":
            if "CHOKED" in status:
                self.warning_label.config(text=t("warning_choked"), bg="#f8d7da", fg="#721c24")
                self.warning_card.config(bg="#f8d7da")
            else:
                self.warning_label.config(text=t("warning_choked"), bg="#fff3cd", fg="#856404")
                self.warning_card.config(bg="#fff3cd")
            
            # Summary card paketlendiyse, ondan hemen sonra yerleştir. Pack sırasını belirleyen "after" argümanı yoksa direkt alta gider.
            self.warning_card.pack(fill="x", pady=(0, 5), after=self.summary_card)

    def populate_profile_table(self, result):
        """Profil verisi sekmesini doldurur ve CSV butonunu aktif/pasif yapar."""
        for item in self.prof_tree.get_children():
            self.prof_tree.delete(item)
            
        profile_data = result.get("profile_data")
        if profile_data and len(profile_data.get("distance", [])) > 0:
            d_list = profile_data["distance"]
            p_list = profile_data["pressure"]
            v_list = profile_data["velocity"]
            
            for d, p, v in zip(d_list, p_list, v_list):
                self.prof_tree.insert("", "end", values=(f"{d:.2f}", f"{p:.2f}", f"{v:.2f}"))
            
            self.btn_export_csv.config(state="normal")
        else:
            self.btn_export_csv.config(state="disabled")

    def export_profile_to_csv(self):
        """Profil verilerini CSV olarak kaydeder."""
        if not self.last_result or "profile_data" not in self.last_result:
            return
            
        import csv
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                                                 title=t("export_csv"))
        if not file_path:
            return
            
        try:
            profile_data = self.last_result["profile_data"]
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([t("col_distance"), t("col_pressure"), t("col_velocity")])
                for d, p, v in zip(profile_data["distance"], profile_data["pressure"], profile_data["velocity"]):
                    writer.writerow([f"{d:.2f}", f"{p:.2f}", f"{v:.2f}"])
            
            self.log_message(f"Profil verisi dışa aktarıldı: {file_path}", level="INFO")
            messagebox.showinfo(t("dialog_success"), f"CSV başarıyla kaydedildi:\n{file_path}")
        except Exception as e:
            self.log_message(f"CSV dışa aktarma hatası: {str(e)}", level="ERROR")
            messagebox.showerror(t("dialog_error"), str(e))

    def populate_results_table(self, result):
        # Tabloyu temizle
        for item in self.res_tree.get_children():
            self.res_tree.delete(item)
            
        if not result: return
        
        # Yardımcı fonksiyon
        def add_row(param, value, unit="", tag=""):
            self.res_tree.insert("", "end", values=(param, value, unit), tags=(tag,))

        # Hedefe göre içerik
        target = self.calc_target.get()
        
        if target == t("target_pressure_drop"):
            add_row("Giriş Basıncı", f"{self.p_in_var.get():.2f}", self.p_unit.get())
            add_row("Çıkış Basıncı", f"{result['P_out']/1e5:.4f}", "bara")
            add_row("Toplam Basınç Kaybı", f"{result['delta_p_total']/1e5:.4f}", "bar")
            add_row("Giriş Hızı", f"{result['velocity_in']:.2f}", "m/s")
            add_row("Çıkış Hızı", f"{result['velocity_out']:.2f}", "m/s")
            
        elif target == t("target_max_length"):
            if "error" in result:
                 add_row("Durum", "HATA", "", "error")
                 add_row("Mesaj", result['error'], "")
            else:
                add_row("Maksimum Uzunluk", f"{result['L_max']:.2f}", "m")
                add_row("Reynolds", f"{result['Re']:.0f}", "")
                
        elif target == t("target_min_diameter"):
            if result['selected_pipe']:
                p = result['selected_pipe']
                add_row("Seçilen Boru", f"{p['nominal']}\"", f"Sch {p['schedule']}", "success")
                add_row("İç Çap", f"{p['D_inner_mm']:.2f}", "mm")
                if 'weight_per_m' in p:
                    add_row(t("unit_weight"), f"{p['weight_per_m']:.2f}", "kg/m")
                add_row("Çıkış Hızı", f"{result['velocity_out']:.2f}", "m/s")
                add_row("Limit Hız", f"{result['max_vel']:.2f}", "m/s")
                
                status_tag = "success" if "Uygun" in result['velocity_status'] else "warning"
                add_row("Durum", result['velocity_status'], "", status_tag)
                
                # Alternatif Senaryolar Gridi
                if 'alternative_options' in result and result['alternative_options']:
                    add_row("", "", "")  # Boşluk
                    add_row("--- Alternatif Seçenekler ---", "", "", "warning")
                    for alt in result['alternative_options']:
                        p_alt = alt['pipe']
                        add_row(f"[★] {alt['note']}", f"{p_alt['nominal']}\" Sch {p_alt['schedule']}", "")
                        if 'weight_per_m' in p_alt:
                            add_row(f"   ↳ {t('unit_weight')}", f"{p_alt['weight_per_m']:.2f}", "kg/m")
            else:
                add_row("Durum", "Uygun Boru Yok", "", "error")

        # Ortak Veriler (Debi vb.)
        if 'm_dot' in result:
             add_row("Kütlesel Debi", f"{result['m_dot']:.4f}", "kg/s")

        # Summary Card güncelle
        self._update_summary_card(result, target)

    def _update_summary_card(self, result, target):
        """Hesaplama sonrası özet kartını güncelle."""
        bg_color = "#e8f5e9"; fg_color = "#2e7d32"  # Yeşil (varsayılan)
        summary_text = ""
        
        try:
            if target == t("target_pressure_drop"):
                p_out_bar = result['P_out'] / 1e5
                dp_bar = result['delta_p_total'] / 1e5
                v_out = result['velocity_out']
                summary_text = f"P_out = {p_out_bar:.2f} bara  │  ΔP = {dp_bar:.3f} bar  │  v = {v_out:.1f} m/s"
                if v_out > 20:
                    bg_color = "#fff3e0"; fg_color = "#e65100"  # Turuncu
                    summary_text += "  ⚠"
                    
            elif target == t("target_max_length"):
                if "error" in result:
                    bg_color = "#ffebee"; fg_color = "#c62828"
                    summary_text = f"❌ {result['error']}"
                else:
                    summary_text = f"L_max = {result['L_max']:.1f} m  │  Re = {result['Re']:.0f}"
                    
            elif target == t("target_min_diameter"):
                if result.get('selected_pipe'):
                    p = result['selected_pipe']
                    summary_text = f"{p['nominal']}\" Sch {p['schedule']}  │  v = {result['velocity_out']:.1f} m/s"
                    if "Uygun" not in result.get('velocity_status', ''):
                        bg_color = "#fff3e0"; fg_color = "#e65100"
                        summary_text += "  ⚠"
                else:
                    bg_color = "#ffebee"; fg_color = "#c62828"
                    summary_text = "❌ Uygun boru bulunamadı"
        except (KeyError, TypeError):
            summary_text = "Hesaplama tamamlandı"
        
        self.summary_card.config(bg=bg_color)
        self.summary_label.config(text=summary_text, bg=bg_color, fg=fg_color)
        self.summary_card.pack(fill="x", pady=(0, 5))

    def format_pressure_drop_report(self, inputs, result):
        # Basit rapor formatı
        res = f"=== HESAPLAMA SONUCU ===\n"
        res += f"Hedef: Çıkış Basıncı\n"
        res += f"Giriş Basıncı: {inputs['P_in']/1e5:.4f} bara\n"
        res += f"Çıkış Basıncı: {result['P_out']/1e5:.4f} bara\n"
        res += f"Toplam Basınç Kaybı: {result['delta_p_total']/1e5:.4f} bar\n"
        res += f"  - Boru Kaybı: {result['delta_p_pipe']/1e5:.4f} bar\n"
        res += f"  - Fitting Kaybı: {result['delta_p_fittings']/1e5:.4f} bar\n\n"
        res += f"Akış Hızı (Giriş): {result['velocity_in']:.2f} m/s\n"
        res += f"Akış Hızı (Çıkış): {result['velocity_out']:.2f} m/s\n"
        res += f"Reynolds: {result['Re']:.0f}\n"
        res += f"Sürtünme Faktörü (f): {result['f']:.5f}\n"
        return res

    def format_max_length_report(self, inputs, result):
        res = f"=== HESAPLAMA SONUCU ===\n"
        res += f"Hedef: Maksimum Uzunluk\n"
        if "error" in result:
            res += f"HATA: {result['error']}\n"
        else:
            res += f"Maksimum Uzunluk: {result['L_max']:.2f} m\n"
            res += f"Reynolds: {result['Re']:.0f}\n"
        return res

    def format_min_diameter_report(self, inputs, result):
        res = f"=== HESAPLAMA SONUCU ===\n"
        res += f"Hedef: Minimum Çap Seçimi\n"
        res += f"Maksimum Hız Limiti: {result['max_vel']:.2f} m/s\n"
        res += f"Gerekli Min. İç Çap (Tahmini): {result['D_min_inner_mm']:.2f} mm\n"
        res += f"Gerçek Akış Hızı (Giriş): {result['flow_rate_actual']:.4f} m³/s\n\n"
        
        if result['selected_pipe']:
            pipe = result['selected_pipe']
            res += f"=== SEÇİLEN BORU (ASME B36.10M) ===\n"
            res += f"Nominal Çap: {pipe['nominal']}\"\n"
            res += f"Schedule: {pipe['schedule']}\n"
            res += f"Dış Çap: {pipe['OD_mm']:.2f} mm\n"
            res += f"Et Kalınlığı: {pipe['t_mm']:.2f} mm\n"
            res += f"İç Çap: {pipe['D_inner_mm']:.2f} mm\n"
            res += f"Gerekli Et Kalınlığı (Mukavemet): {pipe['t_required_mm']:.2f} mm\n\n"
            
            res += f"=== PERFORMANS (SEÇİLEN) ===\n"
            res += f"Giriş Hızı: {result['velocity_in']:.2f} m/s\n"
            res += f"Çıkış Hızı: {result['velocity_out']:.2f} m/s\n"
            res += f"Çıkış Basıncı: {result['P_out']/1e5:.4f} bara\n"
            res += f"Durum: {result['velocity_status']}\n"
            
            # Alternatifler
            if 'alternatives' in result and result['alternatives']:
                res += f"\n=== ALTERNATİF SENARYOLAR ===\n"
                
                # Thinner
                if 'thinner' in result['alternatives']:
                    alt = result['alternatives']['thinner']
                    p = alt['pipe']
                    r = alt['result']
                    res += f"\n[1] {alt['note']}:\n"
                    res += f"   Boru: {p['nominal']}\" {p['schedule']} (ID: {p['D_inner_mm']:.2f} mm)\n"
                    res += f"   Çıkış Hızı: {r['velocity_out']:.2f} m/s\n"
                    res += f"   Çıkış Basıncı: {r['P_out']/1e5:.4f} bara\n"
                
                # Thicker
                if 'thicker' in result['alternatives']:
                    alt = result['alternatives']['thicker']
                    p = alt['pipe']
                    r = alt['result']
                    res += f"\n[2] {alt['note']}:\n"
                    res += f"   Boru: {p['nominal']}\" {p['schedule']} (ID: {p['D_inner_mm']:.2f} mm)\n"
                    res += f"   Çıkış Hızı: {r['velocity_out']:.2f} m/s\n"
                    res += f"   Çıkış Basıncı: {r['P_out']/1e5:.4f} bara\n"

                # Lowest Weight (Eğer optimize_weight seçilmemiş ama daha hafifi varsa)
                if 'lowest_weight' in result['alternatives']:
                    alt = result['alternatives']['lowest_weight']
                    p = alt['pipe']
                    r = alt['result']
                    res += f"\n[★] {alt['note']}:\n"
                    res += f"   Boru: {p['nominal']}\" {p['schedule']} (ID: {p['D_inner_mm']:.2f} mm)\n"
                    res += f"   Birim Ağırlık: {p.get('weight_per_m', 0):.2f} kg/m\n"
                    res += f"   Çıkış Hızı: {r['velocity_out']:.2f} m/s\n"
                    res += f"   Çıkış Basıncı: {r['P_out']/1e5:.4f} bara\n"

        else:
            res += "UYARI: Kriterlere uygun standart boru bulunamadı!\n"
            
        return res

    def draw_schematic(self, event=None):
        """Hesaplama hedefine ve duruma göre interaktif sistem şeması çizer."""
        self.schematic_drawer.draw_schematic(event)

    def show_graphs(self):
        show_graphs(self.root, getattr(self, 'last_result', None))
    # Eski show_graphs silindi (ui.graphs'a taşındı)

    def _get_default_update_dir(self):
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.isdir(downloads_dir):
            return downloads_dir
        return get_install_dir()

    def _get_update_filetypes(self, asset_name):
        ext = os.path.splitext(asset_name)[1].lower()
        if ext == ".exe":
            return [("Executable Files", "*.exe"), ("All Files", "*.*")]
        if ext == ".zip":
            return [("Zip Files", "*.zip"), ("All Files", "*.*")]
        return [("All Files", "*.*")]

    def _prompt_update_download_path(self, asset_info):
        asset_name = asset_info.get("name") or get_versioned_exe_name()
        ext = os.path.splitext(asset_name)[1].lower()
        return filedialog.asksaveasfilename(
            title=t("update_save_as"),
            initialdir=self._get_default_update_dir(),
            initialfile=asset_name,
            defaultextension=ext,
            filetypes=self._get_update_filetypes(asset_name),
        )

    def _open_download_folder(self, file_path):
        folder_path = os.path.dirname(file_path)
        try:
            os.startfile(folder_path)
        except Exception:
            webbrowser.open(folder_path)

    def _ensure_github_token_for_updates(self):
        if not getattr(self.updater, "private_repo", False):
            return True
        if self.updater.github_token:
            return True

        if not messagebox.askyesno(t("dialog_update"), t("update_token_required")):
            return False

        token = simpledialog.askstring(
            t("dialog_update"),
            t("update_token_prompt"),
            parent=self.root,
            show="*",
        )
        if not token:
            return False

        cfg = load_app_config()
        cfg["github_token"] = token.strip()
        save_app_config(cfg)
        self.updater = Updater(self.log_message)
        return bool(self.updater.github_token)

    # --- Güncelleme İşlevleri ---
    def silent_update_check(self):
        try:
            if getattr(self.updater, "private_repo", False) and not self.updater.github_token:
                self.log_message(t("update_private_repo_skip"), level="INFO")
                return
            update_info = self.updater.check_for_update(current_version=APP_VERSION)
            if update_info and update_info.get("has_update"):
                self.log_message(f"{t('update_new_version')}: {update_info['latest_version']}")
        except Exception as e:
            self.log_message(f"Silent update check failed: {e}", level="WARNING")

    def check_updates(self):
        try:
            if not self._ensure_github_token_for_updates():
                return
            self.log_message(t("update_checking"))
            info = self.updater.check_for_update(current_version=APP_VERSION)
            if not info:
                messagebox.showinfo(t("dialog_update"), t("update_config_error"))
                return
            if info["has_update"]:
                body = info.get('body', '')
                preview = (body[:500] + ('...' if len(body) > 500 else '')) if body else 'N/A'
                msg = (
                    f"{t('update_new_version')}: {info['latest_version']}\n\n"
                    f"{t('update_changes')}: {preview}\n\n"
                    f"{t('update_download_ask')}"
                )
                if messagebox.askyesno(t("update_available"), msg):
                    self.download_latest_release()
            else:
                messagebox.showinfo(t("dialog_update"), t("update_up_to_date"))
        except Exception as e:
            messagebox.showerror(t("dialog_error"), str(e))

    def download_latest_release(self):
        try:
            if not self._ensure_github_token_for_updates():
                return
            asset_info = self.updater.get_latest_asset_info()
            if not asset_info:
                messagebox.showinfo(t("dialog_info"), t("update_no_asset"))
                return

            save_path = self._prompt_update_download_path(asset_info)
            if not save_path:
                self.log_message(t("update_download_cancelled"), level="INFO")
                return

            self.log_message(t("update_downloading"))
            asset_path = self.updater.download_latest_asset(destination_path=save_path)
            if asset_path:
                self.last_download_path = asset_path
                if asset_path.lower().endswith(".zip"):
                    if messagebox.askyesno(t("dialog_info"), f"{t('update_downloaded')}: {asset_path}\n\n{t('update_apply_ask')}"):
                        self.apply_update(asset_path)
                    else:
                        messagebox.showinfo(t("dialog_info"), t("update_later"))
                else:
                    msg = f"{t('update_downloaded')}: {asset_path}\n\n{t('update_exe_ready')}\n\n{t('update_open_folder_ask')}"
                    if messagebox.askyesno(t("dialog_info"), msg):
                        self._open_download_folder(asset_path)
            else:
                messagebox.showinfo(t("dialog_info"), t("update_no_asset"))
        except Exception as e:
            messagebox.showerror(t("dialog_error"), str(e))

    def open_update_config(self):
        try:
            cfg_path = get_config_path()
            if not os.path.exists(cfg_path):
                save_app_config(load_config(self.updater.config))
            if os.path.exists(cfg_path):
                os.startfile(cfg_path)
            else:
                messagebox.showinfo("Bilgi", f"Yapılandırma dosyası bulunamadı: {cfg_path}")
        except Exception as e:
            messagebox.showerror("Açma Hatası", str(e))

    def apply_update_from_zip_file(self):
        path = filedialog.askopenfilename(filetypes=[("Zip Files", "*.zip")])
        if not path:
            return
        self.apply_update(path)

    def apply_update(self, zip_path: str):
        try:
            target_dir = get_install_dir()
            info = self.updater.apply_update_from_zip(zip_path, target_dir)
            backup = info.get("backup_dir") if info else None
            msg = "Güncelleme uygulandı. Uygulamayı yeniden başlatmanız önerilir."
            if backup:
                msg += f"\nYedek klasör: {backup}"
            messagebox.showinfo("Güncelleme", msg)
        except Exception as e:
            messagebox.showerror("Güncelleme Hatası", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = GasFlowCalculatorApp(root)
    root.mainloop()

import tkinter as tk
import unittest
import os
import json
from ui.widgets import ValidatedEntry
from translations import t
from app_paths import get_config_path

class TestThemeValidation(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            raise unittest.SkipTest("Tk not available")
        
        self.main_mod = __import__("main")
        self.app = self.main_mod.GasFlowCalculatorApp(self.root)
        self.root.update_idletasks()

    def tearDown(self):
        for after_id in self.root.tk.call("after", "info"):
            try:
                self.root.after_cancel(after_id)
            except (tk.TclError, RuntimeError):
                pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_theme_switching_palette_loads(self):
        # 1. Başlangıç teması tanımlı mı kontrol et
        self.assertIn(self.app.current_theme, ["light", "dark", "contrast"])
        
        # 2. Temayı "dark" yap ve renkleri kontrol et
        self.app.change_theme("dark")
        self.assertEqual(self.app.current_theme, "dark")
        self.assertEqual(self.app._colors["bg"], "#121214")
        self.assertEqual(self.app._colors["card"], "#1e1e24")
        
        # 3. Temayı "contrast" yap ve renkleri kontrol et
        self.app.change_theme("contrast")
        self.assertEqual(self.app.current_theme, "contrast")
        self.assertEqual(self.app._colors["bg"], "#000000")
        
        # 4. Temayı "light" yap ve renkleri kontrol et
        self.app.change_theme("light")
        self.assertEqual(self.app.current_theme, "light")
        self.assertEqual(self.app._colors["bg"], "#f0f3f8")

    def test_theme_persistence_in_config(self):
        # Temayı değiştir
        self.app.change_theme("contrast")
        
        # Yapılandırma dosyasının varlığını ve değerini kontrol et
        config_path = get_config_path()
        self.assertTrue(os.path.exists(config_path))
        
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            
        self.assertEqual(config_data.get("theme"), "contrast")
        
        # Temayı varsayılana geri yükle
        self.app.change_theme("light")

    def test_validated_entry_theme_resolved_colors(self):
        # Container ve ValidatedEntry widget'ı oluştur
        frame = tk.Frame(self.root)
        entry = ValidatedEntry(
            frame,
            validation_type="float",
            min_value=1.0,
            max_value=10.0,
            allow_zero=False,
            allow_negative=False
        )
        entry.pack()
        
        # Light theme için renkleri kontrol et
        self.app.change_theme("light")
        normal_bg, normal_fg, err_bg, err_fg = entry._resolve_theme_colors()
        self.assertEqual(normal_bg, "white")
        self.assertEqual(normal_fg, "black")
        self.assertEqual(err_bg, "#ffe6e6")
        self.assertEqual(err_fg, "#c62828")
        
        # Dark theme için renkleri kontrol et
        self.app.change_theme("dark")
        normal_bg, normal_fg, err_bg, err_fg = entry._resolve_theme_colors()
        self.assertEqual(normal_bg, "#1e1e24")
        self.assertEqual(normal_fg, "#e2e2e9")
        self.assertEqual(err_bg, "#4c1c1c")
        self.assertEqual(err_fg, "#ff8a80")
        
        # Contrast theme için renkleri kontrol et
        self.app.change_theme("contrast")
        normal_bg, normal_fg, err_bg, err_fg = entry._resolve_theme_colors()
        self.assertEqual(normal_bg, "#000000")
        self.assertEqual(normal_fg, "#ffffff")
        self.assertEqual(err_bg, "#ff0000")
        self.assertEqual(err_fg, "#ffffff")

    def test_validated_entry_bounds_validation(self):
        # Container ve ValidatedEntry widget'ı oluştur
        frame = tk.Frame(self.root)
        val_var = tk.DoubleVar(value=5.0)
        entry = ValidatedEntry(
            frame,
            textvariable=val_var,
            validation_type="float",
            min_value=1.0,
            max_value=10.0,
            allow_zero=False,
            allow_negative=False
        )
        entry.pack()
        
        # Temayı light yapalım
        self.app.change_theme("light")
        
        # 1. Geçerli değer: renkler normal olmalı
        entry._validate_input()
        self.assertTrue(entry.is_valid)
        self.assertEqual(str(entry.cget("background")), "white")
        
        # 2. Minimum değer altı geçersiz değer
        val_var.set(0.5)
        entry._validate_input()
        self.assertFalse(entry.is_valid)
        self.assertEqual(entry.error_message, f"{t('val_min_value')}: 1.0")
        
        # 3. Maksimum değer üstü geçersiz değer
        val_var.set(12.5)
        entry._validate_input()
        self.assertFalse(entry.is_valid)
        self.assertEqual(entry.error_message, f"{t('val_max_value')}: 10.0")
        
        # 4. Sıfır değeri kabul edilmeme durumu
        zero_var = tk.DoubleVar(value=0.0)
        entry_zero = ValidatedEntry(
            frame,
            textvariable=zero_var,
            validation_type="float",
            min_value=0.0,
            allow_zero=False
        )
        entry_zero._validate_input()
        self.assertFalse(entry_zero.is_valid)
        self.assertEqual(entry_zero.error_message, t("val_no_zero"))
        
        # 5. Negatif değeri kabul edilmeme durumu
        neg_var = tk.DoubleVar(value=-2.0)
        entry_neg = ValidatedEntry(
            frame,
            textvariable=neg_var,
            validation_type="float",
            allow_negative=False
        )
        entry_neg._validate_input()
        self.assertFalse(entry_neg.is_valid)
        self.assertEqual(entry_neg.error_message, t("val_no_negative"))

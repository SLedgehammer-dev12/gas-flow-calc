import tkinter as tk
from tkinter import ttk
from translations import t

class ToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.wait_time = 500     # miliseconds
        self.wrap_length = 180   # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.wait_time, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       wraplength = self.wrap_length)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

# --- DOĞRULAMA SINIFI (Canlı Kontrol) ---
class ValidationHelper:
    """Kullanıcı girişleri için canlı doğrulama yardımcısı."""
    
    # Hata stilleri
    ERROR_BG = "#ffe6e6"      # Hafif kırmızı arka plan
    ERROR_FG = "#c62828"      # Koyu kırmızı metin
    NORMAL_BG = "white"
    NORMAL_FG = "black"
    WARNING_BG = "#fff3e0"    # Hafif turuncu
    
    @staticmethod
    def normalize_number(value_str):
        """
        Virgül ve nokta ile girilen sayıları normalize eder.
        Örnek: "1,5" veya "1.5" -> 1.5
        Türk lokali desteği: virgül ondalık ayracı olarak kabul edilir.
        """
        if not value_str:
            return ""
        
        # String'e çevir (StringVar olabilir)
        s = str(value_str).strip()
        
        # Boş kontrol
        if not s:
            return ""
        
        comma_count = s.count(',')
        dot_count = s.count('.')
        
        if comma_count > 0 and dot_count > 0:
            # İkisi de var - hangisi ondalık ayracı?
            last_comma = s.rfind(',')
            last_dot = s.rfind('.')
            
            if last_comma > last_dot:
                # Virgül sonda: Türk/Avrupa formatı (1.234,56)
                s = s.replace('.', '')  # Binlik noktaları kaldır
                s = s.replace(',', '.')  # Virgül -> Nokta
            else:
                # Nokta sonda: ABD formatı (1,234.56)
                s = s.replace(',', '')  # Binlik virgülleri kaldır
        elif comma_count > 0:
            # Sadece virgül var
            if comma_count == 1:
                # Tek virgül = ondalık ayracı
                s = s.replace(',', '.')
            else:
                # Birden fazla virgül = binlik ayracı
                s = s.replace(',', '')
        
        return s
    
    @staticmethod
    def parse_float(value_str, default=0.0):
        try:
            normalized = ValidationHelper.normalize_number(value_str)
            if not normalized:
                return default
            return float(normalized)
        except ValueError:
            return None
    
    @staticmethod
    def parse_int(value_str, default=0):
        try:
            normalized = ValidationHelper.normalize_number(value_str)
            if not normalized:
                return default
            return int(float(normalized))
        except ValueError:
            return None


class ValidatedEntry(ttk.Entry):
    """
    Canlı doğrulama yapan Entry widget'ı.
    """
    
    def __init__(self, master, textvariable=None, validation_type="float", 
                 min_value=None, max_value=None, allow_zero=True, allow_negative=False,
                 error_callback=None, **kwargs):
        super().__init__(master, textvariable=textvariable, **kwargs)
        
        self.validation_type = validation_type
        self.min_value = min_value
        self.max_value = max_value
        self.allow_zero = allow_zero
        self.allow_negative = allow_negative
        self.error_callback = error_callback
        
        self.error_tooltip = None
        self.error_message = ""
        self.is_valid = True
        
        # Orijinal arka plan rengini sakla
        self._original_bg = self.cget('background') if self.cget('background') else 'white'
        
        # Event bağlamaları
        self.bind('<KeyRelease>', self._on_key_release)
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<Leave>', self._hide_error_tooltip)
        
    def _on_key_release(self, event=None):
        self._validate_input()
        
    def _on_focus_out(self, event=None):
        self._normalize_and_validate()
        self._hide_error_tooltip()
        
    def _on_focus_in(self, event=None):
        if not self.is_valid:
            self._show_error_tooltip()
    
    def _normalize_and_validate(self):
        current = self.get()
        normalized = ValidationHelper.normalize_number(current)
        if normalized != current:
            try:
                float(normalized)
                state = self.cget('state')
                self.config(state='normal')
                self.delete(0, tk.END)
                self.insert(0, normalized)
                self.config(state=state)
            except ValueError:
                pass
        self._validate_input()
    
    def _validate_input(self):
        value_str = self.get()
        self.error_message = ""
        self.is_valid = True
        
        if not value_str.strip():
            self._set_normal_style()
            return True
        
        normalized = ValidationHelper.normalize_number(value_str)
        
        try:
            if self.validation_type == "int":
                value = int(float(normalized))
            else:
                value = float(normalized)
        except ValueError:
            self.error_message = t("val_invalid_format") if t("val_invalid_format") != "val_invalid_format" else "Geçersiz format"
            self.is_valid = False
            self._set_error_style()
            return False
        
        if self.min_value is not None and value < self.min_value:
            self.error_message = f"{t('val_min_value') if t('val_min_value') != 'val_min_value' else 'Min'}: {self.min_value}"
            self.is_valid = False
            self._set_error_style()
            return False
            
        if self.max_value is not None and value > self.max_value:
            self.error_message = f"{t('val_max_value') if t('val_max_value') != 'val_max_value' else 'Max'}: {self.max_value}"
            self.is_valid = False
            self._set_error_style()
            return False
        
        if not self.allow_zero and value == 0:
            self.error_message = t("val_no_zero") if t("val_no_zero") != "val_no_zero" else "Sıfır olamaz"
            self.is_valid = False
            self._set_error_style()
            return False
        
        if not self.allow_negative and value < 0:
            self.error_message = t("val_no_negative") if t("val_no_negative") != "val_no_negative" else "Negatif olamaz"
            self.is_valid = False
            self._set_error_style()
            return False
        
        if self.validation_type == "percentage":
            if value < 0 or value > 100:
                self.error_message = "0-100%"
                self.is_valid = False
                self._set_error_style()
                return False
        
        self._set_normal_style()
        return True
    
    def _set_error_style(self):
        self.config(background=ValidationHelper.ERROR_BG, foreground=ValidationHelper.ERROR_FG)
        self._show_error_tooltip()
        if self.error_callback:
            self.error_callback(self, self.error_message)
    
    def _set_normal_style(self):
        self.config(background=ValidationHelper.NORMAL_BG, foreground=ValidationHelper.NORMAL_FG)
        self._hide_error_tooltip()
        if self.error_callback:
            self.error_callback(self, None)
    
    def _show_error_tooltip(self, event=None):
        if not self.error_message: return
        if self.error_tooltip: return
        
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        
        self.error_tooltip = tk.Toplevel(self)
        self.error_tooltip.wm_overrideredirect(True)
        self.error_tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.error_tooltip, 
            text=f"⚠ {self.error_message}",
            background="#ffcdd2", foreground="#b71c1c",
            font=("Segoe UI", 9), padx=8, pady=4, relief="solid", borderwidth=1
        )
        label.pack()
    
    def _hide_error_tooltip(self, event=None):
        if self.error_tooltip:
            self.error_tooltip.destroy()
            self.error_tooltip = None
    
    def get_value(self, default=0.0):
        if self.validation_type == "int":
            return ValidationHelper.parse_int(self.get(), default=int(default))
        return ValidationHelper.parse_float(self.get(), default=default)

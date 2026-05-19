import hashlib
import hmac
import secrets
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from app_paths import load_config, save_config
from translations import get_language, t


PBKDF2_ITERATIONS = 200_000
ADMIN_HASH_KEY = "auth_admin_password_hash"
PROGRAM_HASH_KEY = "auth_program_password_hash"
MIN_PASSWORD_LENGTH = 4
MAX_BRUTE_FORCE_ATTEMPTS = 5
BRUTE_FORCE_DELAY_SECONDS = 30


def _msg(key: str, tr_default: str, en_default: str) -> str:
    default = tr_default if get_language() == "tr" else en_default
    return t(key, default)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_value: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_value.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        expected = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        ).hex()
        return hmac.compare_digest(expected, digest_hex)
    except Exception:
        return False


def load_auth_config():
    return load_config()


def is_first_run():
    config = load_auth_config()
    return ADMIN_HASH_KEY not in config or PROGRAM_HASH_KEY not in config


def validate_password_strength(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, _msg(
            "auth_weak_short",
            f"Sifre en az {MIN_PASSWORD_LENGTH} karakter olmalidir.",
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
        )
    return True, ""


def update_passwords(admin_password: str | None = None, program_password: str | None = None):
    config = load_auth_config()
    if admin_password is not None:
        config[ADMIN_HASH_KEY] = hash_password(admin_password)
    if program_password is not None:
        config[PROGRAM_HASH_KEY] = hash_password(program_password)
    save_config(config)
    return config


def prompt_for_program_access(parent) -> bool:
    config = load_auth_config()

    if PROGRAM_HASH_KEY not in config:
        return _force_first_time_password_setup(parent)

    prompt_title = _msg("auth_login_title", "Program Girisi", "Program Login")
    prompt_text = _msg("auth_login_prompt", "Program sifresini girin:", "Enter the program password:")
    invalid_text = _msg(
        "auth_login_invalid",
        "Gecersiz program sifresi. Tekrar deneyin.",
        "Invalid program password. Please try again.",
    )
    locked_text = _msg(
        "auth_locked",
        f"Cok fazla hatali deneme. {BRUTE_FORCE_DELAY_SECONDS} saniye bekleyin.",
        f"Too many failed attempts. Please wait {BRUTE_FORCE_DELAY_SECONDS} seconds.",
    )

    attempts = 0
    while True:
        if attempts >= MAX_BRUTE_FORCE_ATTEMPTS:
            messagebox.showerror(
                _msg("dialog_error", "Hata", "Error"), locked_text, parent=parent
            )
            time.sleep(BRUTE_FORCE_DELAY_SECONDS)
            attempts = 0

        password = simpledialog.askstring(prompt_title, prompt_text, parent=parent, show="*")
        if password is None:
            return False
        if verify_password(password, config[PROGRAM_HASH_KEY]):
            return True
        attempts += 1
        remaining = MAX_BRUTE_FORCE_ATTEMPTS - attempts
        remaining_text = _msg(
            "auth_attempts_remaining",
            f"Gecersiz sifre. Kalan deneme: {remaining}",
            f"Invalid password. Remaining attempts: {remaining}",
        )
        messagebox.showerror(_msg("dialog_error", "Hata", "Error"), remaining_text, parent=parent)


def _force_first_time_password_setup(parent) -> bool:
    title = _msg("auth_first_time_title", "Ilk Kurulum", "First Time Setup")
    info = _msg(
        "auth_first_time_info",
        "Program ilk kez calistiriliyor.\nLutfen bir program giris sifresi ve admin sifresi belirleyin.",
        "First time setup. Please set a program access password and an admin password.",
    )
    messagebox.showinfo(title, info, parent=parent)

    dialog = PasswordManagementDialog(parent, first_time=True)
    parent.wait_window(dialog)
    return dialog.saved


def prompt_for_admin_password(parent) -> bool:
    config = load_auth_config()
    prompt_title = _msg("auth_admin_title", "Admin Dogrulama", "Admin Verification")
    prompt_text = _msg("auth_admin_prompt", "Admin sifresini girin:", "Enter the admin password:")
    invalid_text = _msg(
        "auth_admin_invalid",
        "Gecersiz admin sifresi. Tekrar deneyin.",
        "Invalid admin password. Please try again.",
    )
    locked_text = _msg(
        "auth_locked",
        f"Cok fazla hatali deneme. {BRUTE_FORCE_DELAY_SECONDS} saniye bekleyin.",
        f"Too many failed attempts. Please wait {BRUTE_FORCE_DELAY_SECONDS} seconds.",
    )

    if ADMIN_HASH_KEY not in config:
        messagebox.showerror(
            _msg("dialog_error", "Hata", "Error"),
            _msg("auth_no_admin_password", "Admin sifresi bulunamadi.", "Admin password not found."),
            parent=parent,
        )
        return False

    attempts = 0
    while True:
        if attempts >= MAX_BRUTE_FORCE_ATTEMPTS:
            messagebox.showerror(
                _msg("dialog_error", "Hata", "Error"), locked_text, parent=parent
            )
            time.sleep(BRUTE_FORCE_DELAY_SECONDS)
            attempts = 0

        password = simpledialog.askstring(prompt_title, prompt_text, parent=parent, show="*")
        if password is None:
            return False
        if verify_password(password, config[ADMIN_HASH_KEY]):
            return True
        attempts += 1
        remaining = MAX_BRUTE_FORCE_ATTEMPTS - attempts
        remaining_text = _msg(
            "auth_admin_attempts_remaining",
            f"Gecersiz sifre. Kalan deneme: {remaining}",
            f"Invalid password. Remaining attempts: {remaining}",
        )
        messagebox.showerror(_msg("dialog_error", "Hata", "Error"), remaining_text, parent=parent)


class PasswordManagementDialog(tk.Toplevel):
    def __init__(self, parent, first_time=False):
        super().__init__(parent)
        self.parent = parent
        self.saved = False
        self.first_time = first_time

        self.title(_msg("auth_manage_title", "Parola Yonetimi", "Password Management"))
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.program_password_var = tk.StringVar()
        self.program_password_confirm_var = tk.StringVar()
        self.admin_password_var = tk.StringVar()
        self.admin_password_confirm_var = tk.StringVar()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self.first_time:
            return
        self.destroy()

    def _build_ui(self):
        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)

        info_text = _msg(
            "auth_manage_info",
            "Bos birakilan alanlar degistirilmez.",
            "Blank fields are left unchanged.",
        )
        if self.first_time:
            info_text = _msg(
                "auth_first_time_required",
                "Tum alanlar doldurulmalidir. Sifreler en az {} karakter olmalidir.".format(MIN_PASSWORD_LENGTH),
                "All fields are required. Passwords must be at least {} characters.".format(MIN_PASSWORD_LENGTH),
            )
        ttk.Label(
            container,
            text=info_text,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(
            container,
            text=_msg("auth_program_password", "Program giris sifresi", "Program access password"),
        ).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(container, textvariable=self.program_password_var, show="*", width=28).grid(
            row=1, column=1, sticky="ew", pady=4
        )

        ttk.Label(
            container,
            text=_msg("auth_program_password_confirm", "Program sifresi tekrar", "Confirm program password"),
        ).grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(container, textvariable=self.program_password_confirm_var, show="*", width=28).grid(
            row=2, column=1, sticky="ew", pady=4
        )

        ttk.Separator(container, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(
            container,
            text=_msg("auth_admin_password", "Admin sifresi", "Admin password"),
        ).grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(container, textvariable=self.admin_password_var, show="*", width=28).grid(
            row=4, column=1, sticky="ew", pady=4
        )

        ttk.Label(
            container,
            text=_msg("auth_admin_password_confirm", "Admin sifresi tekrar", "Confirm admin password"),
        ).grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(container, textvariable=self.admin_password_confirm_var, show="*", width=28).grid(
            row=5, column=1, sticky="ew", pady=4
        )

        button_frame = ttk.Frame(container)
        button_frame.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))

        ttk.Button(
            button_frame,
            text=_msg("auth_cancel", "Iptal", "Cancel"),
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            button_frame,
            text=_msg("auth_save", "Kaydet", "Save"),
            command=self._save,
        ).pack(side="right")

        container.columnconfigure(1, weight=1)

    def _save(self):
        new_program_password = self.program_password_var.get().strip()
        confirm_program_password = self.program_password_confirm_var.get().strip()
        new_admin_password = self.admin_password_var.get().strip()
        confirm_admin_password = self.admin_password_confirm_var.get().strip()

        if self.first_time:
            if not new_program_password or not new_admin_password:
                messagebox.showwarning(
                    _msg("dialog_error", "Hata", "Error"),
                    _msg(
                        "auth_first_time_all_required",
                        "Ilk kurulumda tum sifre alanlari doldurulmalidir.",
                        "All password fields must be filled during first time setup.",
                    ),
                    parent=self,
                )
                return

        if not new_program_password and not new_admin_password:
            messagebox.showwarning(
                _msg("dialog_error", "Hata", "Error"),
                _msg(
                    "auth_manage_no_changes",
                    "Degistirmek icin en az bir yeni sifre girin.",
                    "Enter at least one new password to change.",
                ),
                parent=self,
            )
            return

        if new_program_password and new_program_password != confirm_program_password:
            messagebox.showerror(
                _msg("dialog_error", "Hata", "Error"),
                _msg(
                    "auth_program_password_mismatch",
                    "Program sifresi ve tekrar alani eslesmiyor.",
                    "Program password and confirmation do not match.",
                ),
                parent=self,
            )
            return

        if new_admin_password and new_admin_password != confirm_admin_password:
            messagebox.showerror(
                _msg("dialog_error", "Hata", "Error"),
                _msg(
                    "auth_admin_password_mismatch",
                    "Admin sifresi ve tekrar alani eslesmiyor.",
                    "Admin password and confirmation do not match.",
                ),
                parent=self,
            )
            return

        if new_program_password:
            valid, err_msg = validate_password_strength(new_program_password)
            if not valid:
                messagebox.showerror(_msg("dialog_error", "Hata", "Error"), err_msg, parent=self)
                return

        if new_admin_password:
            valid, err_msg = validate_password_strength(new_admin_password)
            if not valid:
                messagebox.showerror(_msg("dialog_error", "Hata", "Error"), err_msg, parent=self)
                return

        update_passwords(
            admin_password=new_admin_password or None,
            program_password=new_program_password or None,
        )
        self.saved = True
        messagebox.showinfo(
            _msg("dialog_success", "Basarili", "Success"),
            _msg(
                "auth_manage_saved",
                "Parolalar basariyla guncellendi.",
                "Passwords were updated successfully.",
            ),
            parent=self,
        )
        self.destroy()


def show_password_management_dialog(parent) -> bool:
    dialog = PasswordManagementDialog(parent)
    parent.wait_window(dialog)
    return dialog.saved

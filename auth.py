import hashlib
import hmac
import secrets
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from app_paths import load_config, save_config
from translations import get_language, t


DEFAULT_ADMIN_PASSWORD = "123456"
DEFAULT_PROGRAM_PASSWORD = "123456"
PBKDF2_ITERATIONS = 200_000
ADMIN_HASH_KEY = "auth_admin_password_hash"
PROGRAM_HASH_KEY = "auth_program_password_hash"


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
    config = load_config()
    changed = False

    if ADMIN_HASH_KEY not in config:
        config[ADMIN_HASH_KEY] = hash_password(DEFAULT_ADMIN_PASSWORD)
        changed = True
    if PROGRAM_HASH_KEY not in config:
        config[PROGRAM_HASH_KEY] = hash_password(DEFAULT_PROGRAM_PASSWORD)
        changed = True

    if changed:
        save_config(config)
    return config


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
    prompt_title = _msg("auth_login_title", "Program Girisi", "Program Login")
    prompt_text = _msg("auth_login_prompt", "Program sifresini girin:", "Enter the program password:")
    invalid_text = _msg(
        "auth_login_invalid",
        "Gecersiz program sifresi. Tekrar deneyin.",
        "Invalid program password. Please try again.",
    )

    while True:
        password = simpledialog.askstring(prompt_title, prompt_text, parent=parent, show="*")
        if password is None:
            return False
        if verify_password(password, config[PROGRAM_HASH_KEY]):
            return True
        messagebox.showerror(_msg("dialog_error", "Hata", "Error"), invalid_text, parent=parent)


def prompt_for_admin_password(parent) -> bool:
    config = load_auth_config()
    prompt_title = _msg("auth_admin_title", "Admin Dogrulama", "Admin Verification")
    prompt_text = _msg("auth_admin_prompt", "Admin sifresini girin:", "Enter the admin password:")
    invalid_text = _msg(
        "auth_admin_invalid",
        "Admin sifresi yanlis.",
        "Incorrect admin password.",
    )

    password = simpledialog.askstring(prompt_title, prompt_text, parent=parent, show="*")
    if password is None:
        return False
    if verify_password(password, config[ADMIN_HASH_KEY]):
        return True
    messagebox.showerror(_msg("dialog_error", "Hata", "Error"), invalid_text, parent=parent)
    return False


class PasswordManagementDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.saved = False

        self.title(_msg("auth_manage_title", "Parola Yonetimi", "Password Management"))
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.program_password_var = tk.StringVar()
        self.program_password_confirm_var = tk.StringVar()
        self.admin_password_var = tk.StringVar()
        self.admin_password_confirm_var = tk.StringVar()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build_ui(self):
        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text=_msg(
                "auth_manage_info",
                "Bos birakilan alanlar degistirilmez.",
                "Blank fields are left unchanged.",
            ),
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

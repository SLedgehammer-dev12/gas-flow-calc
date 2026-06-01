import hashlib
import hmac
import json
import os
import re
import secrets
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from app_paths import load_config, save_config
from translations import get_language, t


PBKDF2_ITERATIONS = 200_000
ADMIN_USERNAME_KEY = "auth_admin_username"
ADMIN_HASH_KEY = "auth_admin_password_hash"
LOCKOUT_STATE_KEY = "auth_lockout_state"
MIN_PASSWORD_LENGTH = 8
MAX_BRUTE_FORCE_ATTEMPTS = 5
BRUTE_FORCE_BASE_DELAY = 30
BRUTE_FORCE_MAX_DELAY = 86400
ARTIFICIAL_LOGIN_DELAY = 1.0
MAX_LOCKOUT_CYCLES = 6
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "123456"


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


def _load_auth_config():
    return load_config()


def _ensure_default_admin() -> dict:
    """Create default admin/123456 credentials if none exist."""
    config = _load_auth_config()
    changed = False
    if ADMIN_USERNAME_KEY not in config:
        config[ADMIN_USERNAME_KEY] = hash_password(DEFAULT_ADMIN_USERNAME)
        changed = True
    if ADMIN_HASH_KEY not in config:
        config[ADMIN_HASH_KEY] = hash_password(DEFAULT_ADMIN_PASSWORD)
        changed = True
    if changed:
        save_config(config)
    return config


def hash_username(username: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    normalized = username.lower().strip()
    digest = hashlib.pbkdf2_hmac("sha256", normalized.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_username(username: str, stored_value: str) -> bool:
    return verify_password(username.lower().strip(), stored_value)


def validate_password_strength(password: str):
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, _msg(
            "auth_weak_short",
            f"Sifre en az {MIN_PASSWORD_LENGTH} karakter olmalidir.",
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
        )
    if not re.search(r"[A-Z\u00C0-\u00DC]", password):
        return False, _msg(
            "auth_weak_uppercase",
            "Sifre en az bir buyuk harf icermelidir.",
            "Password must contain at least one uppercase letter.",
        )
    if not re.search(r"[0-9]", password):
        return False, _msg(
            "auth_weak_digit",
            "Sifre en az bir rakam icermelidir.",
            "Password must contain at least one digit.",
        )
    return True, ""


def update_admin_credentials(new_username: str | None = None, new_password: str | None = None) -> dict:
    """Update admin username and/or password in config."""
    config = _load_auth_config()
    changed = False
    if new_username is not None:
        config[ADMIN_USERNAME_KEY] = hash_username(new_username)
        changed = True
    if new_password is not None:
        config[ADMIN_HASH_KEY] = hash_password(new_password)
        changed = True
    if changed:
        save_config(config)
    return config


def _lockout_hmac_key() -> bytes:
    host = os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME", "unknown")
    user = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
    seed = f"{host}::{user}::GasFlowCalcLockout".encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", seed, b"auth-lockout-hmac-v1", iterations=200_000)


def _lockout_sign(data: dict) -> dict:
    serialized = json.dumps(data, separators=(",", ":"), sort_keys=True)
    key = _lockout_hmac_key()
    sig = hmac.new(key, serialized.encode("utf-8"), "sha256").hexdigest()
    return {"data": data, "hmac": sig}


def _lockout_verify(signed: dict) -> dict | None:
    try:
        data = signed.get("data")
        expected_sig = signed.get("hmac", "")
        serialized = json.dumps(data, separators=(",", ":"), sort_keys=True)
        key = _lockout_hmac_key()
        actual_sig = hmac.new(key, serialized.encode("utf-8"), "sha256").hexdigest()
        if hmac.compare_digest(actual_sig, expected_sig):
            return data
    except Exception:
        pass
    return None


def _migrate_lockout_state(raw: dict) -> dict:
    """Migrate old 'program' key to 'login' and ensure all keys exist."""
    if "program" in raw and "login" not in raw:
        raw["login"] = raw.pop("program")
    for key in ("login", "admin"):
        entry = raw.setdefault(key, {})
        entry.setdefault("attempts", 0)
        entry.setdefault("locked_until", 0.0)
        entry.setdefault("lockout_cycles", 0)
        entry.setdefault("total_attempts", 0)
    return raw


def _load_lockout_state():
    empty_state = _migrate_lockout_state({})
    try:
        config = load_config()
        raw = config.get(LOCKOUT_STATE_KEY)
        if isinstance(raw, dict) and "hmac" in raw:
            verified = _lockout_verify(raw)
            if verified is not None:
                return _migrate_lockout_state(verified)
        if isinstance(raw, dict) and "hmac" not in raw:
            return _migrate_lockout_state(raw)
        return empty_state
    except Exception:
        return empty_state


def _save_lockout_state(state: dict):
    try:
        config = load_config()
        signed = _lockout_sign(state)
        config[LOCKOUT_STATE_KEY] = signed
        save_config(config)
    except Exception:
        pass


_lockout_state = _load_lockout_state()


def _get_lockout_duration(lockout_cycles: int) -> int:
    """Exponential backoff: 30s, 60s, 120s, 240s, 480s, then 86400s."""
    if lockout_cycles >= MAX_LOCKOUT_CYCLES:
        return BRUTE_FORCE_MAX_DELAY
    if lockout_cycles <= 0:
        return BRUTE_FORCE_BASE_DELAY
    duration = BRUTE_FORCE_BASE_DELAY * (2 ** (lockout_cycles - 1))
    return min(duration, BRUTE_FORCE_MAX_DELAY)


def _check_and_update_lockout(parent, key: str) -> bool:
    state = _lockout_state[key]
    now = time.time()
    if now < state["locked_until"]:
        remaining = int(state["locked_until"] - now)
        if state.get("lockout_cycles", 0) >= MAX_LOCKOUT_CYCLES:
            text = _msg(
                "login_locked_max",
                "Hesap 24 saat sureyle kilitlendi.",
                "Account locked for 24 hours.",
            )
        else:
            text = _msg(
                "auth_locked",
                f"Cok fazla hatali deneme. {remaining} saniye bekleyin.",
                f"Too many failed attempts. Please wait {remaining} seconds.",
            )
        messagebox.showerror(_msg("dialog_error", "Hata", "Error"), text, parent=parent)
        return True
    return False


def _increment_lockout(key: str) -> bool:
    """Increment attempt counter. Returns True if now locked."""
    state = _lockout_state[key]
    state["attempts"] = state.get("attempts", 0) + 1
    state["total_attempts"] = state.get("total_attempts", 0) + 1

    if state["attempts"] >= MAX_BRUTE_FORCE_ATTEMPTS:
        state["lockout_cycles"] = state.get("lockout_cycles", 0) + 1
        duration = _get_lockout_duration(state["lockout_cycles"])
        state["locked_until"] = time.time() + duration
        state["attempts"] = 0
        _save_lockout_state(_lockout_state)
        return True
    _save_lockout_state(_lockout_state)
    return False


def _reset_lockout(key: str):
    state = _lockout_state[key]
    state["attempts"] = 0
    state["locked_until"] = 0.0
    _save_lockout_state(_lockout_state)


class LoginDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.result = False

        self.title(_msg("login_title", "Giris", "Login"))
        self.resizable(False, False)
        self.grab_set()

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Return>", lambda e: self._do_login())

        self.update_idletasks()
        w, h = 350, 200
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_close(self):
        self.destroy()

    def _build_ui(self):
        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text=_msg("login_username", "Kullanici adi", "Username")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.username_entry = ttk.Entry(container, textvariable=self.username_var, width=28)
        self.username_entry.grid(row=0, column=1, sticky="ew", pady=(0, 4))
        self.username_entry.focus_set()

        ttk.Label(container, text=_msg("login_password", "Sifre", "Password")).grid(
            row=1, column=0, sticky="w", pady=4
        )
        ttk.Entry(container, textvariable=self.password_var, show="*", width=28).grid(
            row=1, column=1, sticky="ew", pady=4
        )

        button_frame = ttk.Frame(container)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="e", pady=(12, 0))

        ttk.Button(
            button_frame,
            text=_msg("login_cancel", "Iptal", "Cancel"),
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        self.login_button = ttk.Button(
            button_frame,
            text=_msg("login_button", "Giris", "Login"),
            command=self._do_login,
        )
        self.login_button.pack(side="right")

        container.columnconfigure(1, weight=1)

    def _do_login(self):
        _ensure_default_admin()
        config = _load_auth_config()

        if _check_and_update_lockout(self, "login"):
            return

        time.sleep(ARTIFICIAL_LOGIN_DELAY)

        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showerror(
                _msg("dialog_error", "Hata", "Error"),
                _msg("login_required", "Kullanici adi ve sifre gereklidir.", "Username and password are required."),
                parent=self,
            )
            return

        stored_username_hash = config.get(ADMIN_USERNAME_KEY, "")
        stored_password_hash = config.get(ADMIN_HASH_KEY, "")

        username_ok = verify_username(username, stored_username_hash)
        password_ok = verify_password(password, stored_password_hash) if username_ok else False

        if username_ok and password_ok:
            _reset_lockout("login")
            self.result = True
            self.destroy()
        else:
            locked = _increment_lockout("login")
            if locked:
                state = _lockout_state["login"]
                if state.get("lockout_cycles", 0) >= MAX_LOCKOUT_CYCLES:
                    msg = _msg(
                        "login_locked_max",
                        "Hesap 24 saat sureyle kilitlendi. En fazla deneme sayisina ulasildi.",
                        "Account locked for 24 hours. Maximum attempts reached.",
                    )
                else:
                    duration = _get_lockout_duration(state.get("lockout_cycles", 1))
                    msg = _msg(
                        "login_locked",
                        f"Hesap {duration} saniye sureyle kilitlendi.",
                        f"Account locked for {duration} seconds.",
                    )
                messagebox.showerror(_msg("dialog_error", "Hata", "Error"), msg, parent=self)
            else:
                remaining = MAX_BRUTE_FORCE_ATTEMPTS - _lockout_state["login"]["attempts"]
                msg = _msg(
                    "login_invalid_attempts",
                    f"Gecersiz kullanici adi veya sifre. Kalan deneme: {remaining}",
                    f"Invalid username or password. Remaining attempts: {remaining}",
                )
                messagebox.showerror(_msg("dialog_error", "Hata", "Error"), msg, parent=self)
                self.password_var.set("")
                self.username_entry.focus_set()


def prompt_for_login(parent) -> bool:
    """Show login dialog. Returns True if authenticated."""
    _ensure_default_admin()
    dialog = LoginDialog(parent)
    dialog.wait_window()
    return dialog.result


def prompt_for_admin_password(parent) -> bool:
    """Verify existing admin password for sensitive operations."""
    config = _load_auth_config()

    if ADMIN_HASH_KEY not in config:
        messagebox.showerror(
            _msg("dialog_error", "Hata", "Error"),
            _msg("auth_no_admin_password", "Admin sifresi bulunamadi.", "Admin password not found."),
            parent=parent,
        )
        return False

    while True:
        if _check_and_update_lockout(parent, "admin"):
            return False

        password = simpledialog.askstring(
            _msg("auth_admin_title", "Admin Dogrulama", "Admin Verification"),
            _msg("auth_admin_prompt", "Admin sifresini girin:", "Enter the admin password:"),
            parent=parent,
            show="*",
        )
        if password is None:
            return False

        if _check_and_update_lockout(parent, "admin"):
            return False

        if verify_password(password, config[ADMIN_HASH_KEY]):
            _reset_lockout("admin")
            return True

        locked = _increment_lockout("admin")
        if locked:
            state = _lockout_state["admin"]
            if state.get("lockout_cycles", 0) >= MAX_LOCKOUT_CYCLES:
                messagebox.showerror(
                    _msg("dialog_error", "Hata", "Error"),
                    _msg(
                        "login_locked_max",
                        "Admin hesabi 24 saat sureyle kilitlendi.",
                        "Admin account locked for 24 hours.",
                    ),
                    parent=parent,
                )
            else:
                duration = _get_lockout_duration(state.get("lockout_cycles", 1))
                messagebox.showerror(
                    _msg("dialog_error", "Hata", "Error"),
                    _msg(
                        "login_locked",
                        f"Admin hesabi {duration} saniye sureyle kilitlendi.",
                        f"Admin account locked for {duration} seconds.",
                    ),
                    parent=parent,
                )
            return False
        else:
            remaining = MAX_BRUTE_FORCE_ATTEMPTS - _lockout_state["admin"]["attempts"]
            messagebox.showerror(
                _msg("dialog_error", "Hata", "Error"),
                _msg(
                    "auth_admin_attempts_remaining",
                    f"Gecersiz sifre. Kalan deneme: {remaining}",
                    f"Invalid password. Remaining attempts: {remaining}",
                ),
                parent=parent,
            )


class PasswordManagementDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.saved = False

        self.title(_msg("auth_manage_title", "Kullanici ve Parola Yonetimi", "User & Password Management"))
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.password_confirm_var = tk.StringVar()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.destroy()

    def _build_ui(self):
        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)

        info_text = _msg(
            "auth_manage_info",
            "Bos birakilan alanlar degistirilmez.\n"
            "Kullanici adi en az 3 karakter, bosluk icermemeli.\n"
            "Sifre en az 8 karakter, bir buyuk harf ve bir rakam icermeli.",
            "Blank fields are left unchanged.\n"
            "Username: min 3 characters, no spaces.\n"
            "Password: min 8 characters, one uppercase, one digit.",
        )
        ttk.Label(container, text=info_text).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
        )

        ttk.Label(
            container,
            text=_msg("auth_manage_username", "Yeni kullanici adi", "New username"),
        ).grid(row=1, column=0, sticky="w", pady=4)
        self.username_entry = ttk.Entry(container, textvariable=self.username_var, width=28)
        self.username_entry.grid(row=1, column=1, sticky="ew", pady=4)
        self.username_entry.focus_set()

        ttk.Separator(container, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=10
        )

        ttk.Label(
            container,
            text=_msg("auth_manage_password", "Yeni sifre", "New password"),
        ).grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(container, textvariable=self.password_var, show="*", width=28).grid(
            row=3, column=1, sticky="ew", pady=4
        )

        ttk.Label(
            container,
            text=_msg("auth_manage_confirm", "Yeni sifre tekrar", "Confirm new password"),
        ).grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(container, textvariable=self.password_confirm_var, show="*", width=28).grid(
            row=4, column=1, sticky="ew", pady=4
        )

        button_frame = ttk.Frame(container)
        button_frame.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))

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
        new_username = self.username_var.get().strip()
        new_password = self.password_var.get().strip()
        confirm_password = self.password_confirm_var.get().strip()

        if not new_username and not new_password:
            messagebox.showwarning(
                _msg("dialog_error", "Hata", "Error"),
                _msg(
                    "auth_manage_no_changes",
                    "Degistirmek icin en az bir alan doldurun.",
                    "Fill at least one field to make a change.",
                ),
                parent=self,
            )
            return

        if new_username:
            if len(new_username) < 3:
                messagebox.showerror(
                    _msg("dialog_error", "Hata", "Error"),
                    _msg(
                        "auth_username_short",
                        "Kullanici adi en az 3 karakter olmalidir.",
                        "Username must be at least 3 characters.",
                    ),
                    parent=self,
                )
                return
            if " " in new_username:
                messagebox.showerror(
                    _msg("dialog_error", "Hata", "Error"),
                    _msg(
                        "auth_username_whitespace",
                        "Kullanici adi bosluk iceremez.",
                        "Username cannot contain spaces.",
                    ),
                    parent=self,
                )
                return

        if new_password:
            if new_password != confirm_password:
                messagebox.showerror(
                    _msg("dialog_error", "Hata", "Error"),
                    _msg(
                        "auth_password_mismatch",
                        "Sifre ve tekrar alani eslesmiyor.",
                        "Password and confirmation do not match.",
                    ),
                    parent=self,
                )
                return
            valid, err_msg = validate_password_strength(new_password)
            if not valid:
                messagebox.showerror(_msg("dialog_error", "Hata", "Error"), err_msg, parent=self)
                return

        update_admin_credentials(
            new_username=new_username or None,
            new_password=new_password or None,
        )
        self.saved = True
        messagebox.showinfo(
            _msg("dialog_success", "Basarili", "Success"),
            _msg(
                "auth_manage_saved",
                "Kullanici adi ve/veya sifre basariyla guncellendi.",
                "Username and/or password updated successfully.",
            ),
            parent=self,
        )
        self.destroy()


def show_password_management_dialog(parent) -> bool:
    """Open password management dialog (requires prior admin verification)."""
    dialog = PasswordManagementDialog(parent)
    dialog.wait_window()
    return dialog.saved

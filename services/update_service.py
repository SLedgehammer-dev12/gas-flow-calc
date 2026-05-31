import os
from tkinter import messagebox, filedialog
from app_paths import get_config_path, get_install_dir, load_config, save_config
from release_metadata import APP_VERSION
from translations import t
from updater import Updater, _obfuscate_token, _deobfuscate_token


class UpdateService:
    def __init__(self, app):
        self.app = app
        self.last_download_path = None
        cfg = self._load_config()
        self.updater = Updater(self.app.log_message)

    def _load_config(self):
        path = get_config_path()
        if os.path.exists(path):
            try:
                import json
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def silent_check(self):
        try:
            if getattr(self.updater, "private_repo", False) and not self.updater.github_token:
                self.app.log_message(t("update_private_repo_skip"), level="INFO")
                return
            info = self.updater.check_for_update(current_version=APP_VERSION)
            if info and info.get("has_update"):
                self.app.log_message(f"{t('update_new_version')}: {info['latest_version']}")
        except Exception as e:
            self.app.log_message(f"Silent update check failed: {e}", level="WARNING")

    def check(self):
        try:
            self.app.log_message(t("update_checking"))
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
                    self.download_latest()
            else:
                messagebox.showinfo(t("dialog_update"), t("update_up_to_date"))
        except Exception as e:
            messagebox.showerror(t("dialog_error"), str(e))

    def download_latest(self):
        try:
            asset_info = self.updater.get_latest_asset_info()
            if not asset_info:
                messagebox.showinfo(t("dialog_info"), t("update_no_asset"))
                return
            filename = self._get_filename(asset_info)
            save_path = filedialog.asksaveasfilename(
                initialfile=filename or "Gas_Flow_Calc_Update.zip",
                defaultextension=".zip",
                filetypes=[("Zip files", "*.zip"), ("Exe files", "*.exe"), ("All files", "*.*")],
            )
            if not save_path:
                self.app.log_message(t("update_download_cancelled"), level="INFO")
                return

            self.app.log_message(t("update_downloading"))
            asset_path = self.updater.download_latest_asset(destination_path=save_path)
            if asset_path:
                self.last_download_path = asset_path
                if asset_path.lower().endswith(".zip"):
                    if messagebox.askyesno(t("dialog_info"),
                        f"{t('update_downloaded')}: {asset_path}\n\n{t('update_apply_ask')}"):
                        self._apply_update(asset_path)
                    else:
                        messagebox.showinfo(t("dialog_info"), t("update_later"))
                else:
                    msg = f"{t('update_downloaded')}: {asset_path}\n\n{t('update_exe_ready')}\n\n{t('update_open_folder_ask')}"
                    if messagebox.askyesno(t("dialog_info"), msg):
                        self._open_folder(asset_path)
            else:
                messagebox.showinfo(t("dialog_info"), t("update_no_asset"))
        except Exception as e:
            messagebox.showerror(t("dialog_error"), str(e))

    def _get_filename(self, asset_info):
        return asset_info.get("name", None)

    def _open_folder(self, filepath):
        import subprocess
        folder = os.path.dirname(os.path.abspath(filepath))
        try:
            subprocess.Popen(["open", folder])
        except Exception:
            try:
                os.startfile(folder)
            except Exception:
                pass

    def open_config(self):
        cfg_path = get_config_path()
        if not os.path.exists(cfg_path):
            save_config(load_config())
        if os.path.exists(cfg_path):
            os.startfile(cfg_path)
        else:
            messagebox.showinfo("Bilgi", f"Yapilandirma dosyasi bulunamadi: {cfg_path}")

    def apply_update_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("Zip Files", "*.zip")])
        if not path:
            return
        self._apply_update(path)

    def _apply_update(self, zip_path):
        try:
            target_dir = get_install_dir()
            info = self.updater.apply_update_from_zip(zip_path, target_dir)
            backup = info.get("backup_dir") if info else None
            msg = "Guncelleme uygulandi. Uygulamayi yeniden baslatmaniz onerilir."
            if backup:
                msg += f"\n\nYedek: {backup}"
            messagebox.showinfo("Guncelleme", msg)
        except Exception as e:
            messagebox.showerror("Guncelleme Hatasi", str(e))

    def apply_update(self, zip_path):
        self._apply_update(zip_path)

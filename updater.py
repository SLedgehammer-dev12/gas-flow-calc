import json
import os
import re
import shutil
import ssl
import subprocess
import tempfile
import zipfile
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app_paths import load_config, save_config


GITHUB_API_RELEASES = "https://api.github.com/repos/{repo}/releases/latest"
GITHUB_BRANCH_ZIP = "https://github.com/{repo}/archive/refs/heads/{branch}.zip"
GITHUB_RAW_FILE = "https://raw.githubusercontent.com/{repo}/{branch}/{path}"

DEFAULT_CONFIG = {
    "repo": "SLedgehammer-dev12/gas-flow-calc",
    "private_repo": False,
    "asset_name_regex": r"(gas[\s._-]*flow[\s._-]*calc).*\.(exe|zip)$",
    "update_mode": "releases",
    "branch": "main",
    "version_source_path": "",
    "version_regex": r'APP_VERSION\s*=\s*"(\d+\.\d+\.\d+)"',
    "app_subdir_in_zip": "",
    "exclude_on_apply": ["config.json", "__pycache__", ".git", "_backups"],
    "github_token": "",
}


def _load_config(log):
    try:
        config = load_config(DEFAULT_CONFIG)
        migrated = False

        if config.get("repo") in {
            "SLedgehammer-dev12/Programlar",
            "SLedgehammer-dev12/gas-flow-calc-v6-1",
            "SLedgehammer-dev12/gas-flow-calc",
        }:
            if config.get("repo") != DEFAULT_CONFIG["repo"]:
                config["repo"] = DEFAULT_CONFIG["repo"]
                migrated = True
            if config.get("private_repo") != DEFAULT_CONFIG["private_repo"]:
                config["private_repo"] = DEFAULT_CONFIG["private_repo"]
                migrated = True

        if config.get("repo") == DEFAULT_CONFIG["repo"] and config.get("update_mode") == "branch":
            config["update_mode"] = DEFAULT_CONFIG["update_mode"]
            config["asset_name_regex"] = DEFAULT_CONFIG["asset_name_regex"]
            config["branch"] = DEFAULT_CONFIG["branch"]
            config["version_source_path"] = DEFAULT_CONFIG["version_source_path"]
            migrated = True

        if config.get("repo") == DEFAULT_CONFIG["repo"] and config.get("asset_name_regex") != DEFAULT_CONFIG["asset_name_regex"]:
            config["asset_name_regex"] = DEFAULT_CONFIG["asset_name_regex"]
            migrated = True

        if config.get("repo") == DEFAULT_CONFIG["repo"] and config.get("private_repo") != DEFAULT_CONFIG["private_repo"]:
            config["private_repo"] = DEFAULT_CONFIG["private_repo"]
            migrated = True

        if migrated:
            save_config(config)

        return config
    except Exception as e:
        if log:
            log(f"Guncelleme yapilandirmasi okunamadi: {e}", level="WARNING")
        return dict(DEFAULT_CONFIG)


def _semver_tuple(v: str):
    match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", v.strip())
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())


class Updater:
    def __init__(self, log_callback=None):
        self.log = log_callback or (lambda msg, level="INFO": None)
        self.config = _load_config(self.log)
        self.repo = self.config.get("repo", "")
        self.asset_name_regex = self.config.get("asset_name_regex", r"\.zip$")
        self.private_repo = bool(self.config.get("private_repo", False))
        self.update_mode = self.config.get("update_mode", "releases")
        self.branch = self.config.get("branch", "main")
        self.version_source_path = self.config.get("version_source_path", "")
        self.version_regex = self.config.get("version_regex", r'APP_VERSION\s*=\s*"(\d+\.\d+\.\d+)"')
        self.app_subdir_in_zip = self.config.get("app_subdir_in_zip", "")
        self.exclude_on_apply = set(self.config.get("exclude_on_apply", []))
        self.github_token = self.config.get("github_token") or os.environ.get("GITHUB_TOKEN") or ""

    def _headers(self, accept: str | None = None, include_auth: bool = True):
        headers = {"User-Agent": "GasFlowCalc-Updater"}
        if accept:
            headers["Accept"] = accept
        if include_auth and self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        return headers

    def _clear_invalid_public_token(self):
        if self.private_repo or not self.github_token:
            return False

        self.log(
            "Public repo icin gecersiz GitHub token temizleniyor; istek kimliksiz tekrar denenecek.",
            level="WARNING",
        )
        self.github_token = ""

        if self.config.get("github_token"):
            self.config["github_token"] = ""
            try:
                save_config(self.config)
            except Exception as e:
                self.log(f"Gecersiz GitHub token temizlenemedi: {e}", level="WARNING")

        return True

    def _format_request_error(self, error):
        if isinstance(error, HTTPError):
            if error.code == 404 and not self.github_token:
                return (
                    "GitHub release bilgisine erisilemedi. "
                    "Repo private oldugu icin local config icinde 'github_token' tanimlanmali."
                )
            if error.code == 404:
                return "GitHub release veya asset bulunamadi (HTTP 404)."
            if error.code == 401:
                return "GitHub token gecersiz veya yetkisiz (HTTP 401)."
            if error.code == 403:
                return "GitHub erisimi reddedildi veya rate limit asildi (HTTP 403)."
        if isinstance(error, URLError) and self._is_ssl_verification_error(error):
            return (
                "SSL sertifika zinciri dogrulanamadi. Kurumsal ag SSL denetimi veya "
                "eksik sertifika zinciri nedeniyle Python/OpenSSL GitHub baglantisini reddetti."
            )
        return str(error)

    def _is_ssl_verification_error(self, error):
        reason = getattr(error, "reason", error)
        if isinstance(reason, ssl.SSLCertVerificationError):
            return True
        text = str(reason or error)
        return "CERTIFICATE_VERIFY_FAILED" in text or "Missing Authority Key Identifier" in text

    @staticmethod
    def _ps_quote(value: str):
        return "'" + str(value).replace("'", "''") + "'"

    def _powershell_headers(self, headers):
        items = [f"{self._ps_quote(key)}={self._ps_quote(value)}" for key, value in headers.items()]
        return "@{" + ";".join(items) + "}"

    def _powershell_fetch_text(self, url: str, headers: dict, timeout: int):
        command = (
            "$ProgressPreference='SilentlyContinue'; "
            f"$headers={self._powershell_headers(headers)}; "
            "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
            f"$response=Invoke-WebRequest -UseBasicParsing -Uri {self._ps_quote(url)} "
            f"-Headers $headers -TimeoutSec {int(timeout)}; "
            "$response.Content"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=max(30, int(timeout) + 15),
            check=True,
        )
        return result.stdout

    def _powershell_download_to_path(self, url: str, headers: dict, destination_path: str, timeout: int):
        command = (
            "$ProgressPreference='SilentlyContinue'; "
            f"$headers={self._powershell_headers(headers)}; "
            f"Invoke-WebRequest -UseBasicParsing -Uri {self._ps_quote(url)} "
            f"-Headers $headers -TimeoutSec {int(timeout)} -OutFile {self._ps_quote(destination_path)}"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=max(60, int(timeout) + 30),
            check=True,
        )

    def _read_url_text(self, url: str, accept: str | None = None, timeout: int = 10):
        headers = self._headers(accept)
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except HTTPError as error:
            if error.code == 401 and self._clear_invalid_public_token():
                return self._read_url_text(url, accept=accept, timeout=timeout)
            raise
        except URLError as error:
            if os.name == "nt" and self._is_ssl_verification_error(error):
                self.log(
                    "Python SSL dogrulamasi basarisiz oldu; Windows ag katmani ile tekrar deneniyor.",
                    level="WARNING",
                )
                return self._powershell_fetch_text(url, headers, timeout)
            raise

    def _default_download_path(self, file_name: str):
        tmp_dir = os.path.join(tempfile.gettempdir(), "gas_flow_calc_updates")
        os.makedirs(tmp_dir, exist_ok=True)
        return os.path.join(tmp_dir, file_name)

    def _get_selected_release_asset(self, assets):
        pattern = re.compile(self.asset_name_regex, re.IGNORECASE)
        matching_assets = [asset for asset in assets if pattern.search(asset.get("name", ""))]
        candidates = matching_assets or assets
        if not candidates:
            return None

        def sort_key(asset):
            name = asset.get("name", "").lower()
            if name.endswith(".exe"):
                return (0, name)
            if name.endswith(".zip"):
                return (1, name)
            return (2, name)

        return sorted(candidates, key=sort_key)[0]

    def check_for_update(self, current_version: str):
        if not self.repo:
            self.log("GitHub repo bilgisi yapilandirmada yok.", level="WARNING")
            return None

        if self.update_mode == "branch":
            if not self.version_source_path:
                self.log("Branch modu icin 'version_source_path' gerekli.", level="ERROR")
                return None

            quoted_path = quote(self.version_source_path, safe="/")
            raw_url = GITHUB_RAW_FILE.format(repo=self.repo, branch=self.branch, path=quoted_path)
            try:
                content = self._read_url_text(raw_url, timeout=10)
            except Exception as e:
                self.log(f"Surum bilgisi alinamadi: {e}", level="ERROR")
                return None

            match = re.search(self.version_regex, content)
            latest_tag = match.group(1) if match else "0.0.0"
            latest = _semver_tuple(latest_tag)
            current = _semver_tuple(current_version)
            return {
                "has_update": latest > current,
                "latest_version": latest_tag,
                "body": f"Branch: {self.branch} (dosya: {self.version_source_path})",
                "assets": [],
            }

        url = GITHUB_API_RELEASES.format(repo=self.repo)
        try:
            content = self._read_url_text(url, accept="application/vnd.github+json", timeout=10)
            data = json.loads(content)
        except (URLError, HTTPError) as e:
            self.log(f"GitHub API erisim hatasi: {self._format_request_error(e)}", level="ERROR")
            return None
        except Exception as e:
            self.log(f"Bilinmeyen hata: {e}", level="ERROR")
            return None

        latest_tag = data.get("tag_name") or data.get("name") or "0.0.0"
        latest = _semver_tuple(latest_tag)
        current = _semver_tuple(current_version)
        return {
            "has_update": latest > current,
            "latest_version": latest_tag,
            "body": data.get("body", ""),
            "assets": data.get("assets", []),
        }

    def get_latest_asset_info(self):
        if not self.repo:
            raise RuntimeError("GitHub repo yapilandirilmadi.")

        if self.update_mode == "branch":
            return {
                "name": f"{self.repo.split('/')[-1]}-{self.branch}.zip",
                "browser_download_url": GITHUB_BRANCH_ZIP.format(repo=self.repo, branch=self.branch),
            }

        info = self.check_for_update(current_version="0.0.0")
        if not info:
            return None

        chosen = self._get_selected_release_asset(info.get("assets", []))
        if not chosen:
            return None
        return chosen

    def download_latest_asset(self, destination_path=None):
        if not self.repo:
            raise RuntimeError("GitHub repo yapilandirilmadi.")

        asset_info = self.get_latest_asset_info()
        if not asset_info:
            return None

        file_name = asset_info.get("name") or "update.bin"
        browser_download_url = asset_info.get("browser_download_url")
        if not browser_download_url:
            return None

        self.log(f"Indirme basliyor: {file_name}")
        file_path = destination_path or self._default_download_path(file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        def _download_once():
            req = Request(browser_download_url, headers=self._headers())
            with urlopen(req, timeout=60) as resp:
                return resp.read()

        try:
            data = _download_once()
        except (URLError, HTTPError) as e:
            if isinstance(e, HTTPError) and e.code == 401 and self._clear_invalid_public_token():
                try:
                    data = _download_once()
                except Exception as retry_error:
                    raise RuntimeError(f"Indirme basarisiz: {retry_error}") from retry_error
            elif isinstance(e, URLError) and os.name == "nt" and self._is_ssl_verification_error(e):
                self.log(
                    "Python SSL dogrulamasi basarisiz oldu; indirme Windows ag katmani ile tekrar deneniyor.",
                    level="WARNING",
                )
                try:
                    self._powershell_download_to_path(browser_download_url, self._headers(), file_path, timeout=60)
                    self.log(f"Indirme tamamlandi: {file_path}")
                    return file_path
                except Exception as fallback_error:
                    raise RuntimeError(
                        f"Indirme basarisiz: {self._format_request_error(e)} / PowerShell fallback: {fallback_error}"
                    ) from e
            else:
                raise RuntimeError(f"Indirme basarisiz: {self._format_request_error(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Indirme basarisiz: {e}") from e

        with open(file_path, "wb") as f:
            f.write(data)
        self.log(f"Indirme tamamlandi: {file_path}")
        return file_path

    def apply_update_from_zip(self, zip_path: str, target_dir: str):
        if not os.path.isfile(zip_path):
            raise RuntimeError(f"Zip dosyasi bulunamadi: {zip_path}")
        if not os.path.isdir(target_dir):
            raise RuntimeError(f"Hedef klasor bulunamadi: {target_dir}")

        self.log(f"Guncelleme uygulaniyor: {zip_path}")

        tmp_root = os.path.join(tempfile.gettempdir(), "gas_flow_calc_updates", "extract")
        if os.path.isdir(tmp_root):
            try:
                shutil.rmtree(tmp_root)
            except Exception:
                pass
        os.makedirs(tmp_root, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_root)

        entries = os.listdir(tmp_root)
        extracted_root = tmp_root
        if len(entries) == 1 and os.path.isdir(os.path.join(tmp_root, entries[0])):
            extracted_root = os.path.join(tmp_root, entries[0])

        source_dir = extracted_root
        if self.app_subdir_in_zip:
            candidate = os.path.join(extracted_root, self.app_subdir_in_zip)
            if os.path.isdir(candidate):
                source_dir = candidate
            else:
                self.log(f"Uyari: app_subdir_in_zip bulunamadi: {candidate}", level="WARNING")

        parent = os.path.dirname(target_dir.rstrip("/\\"))
        base = os.path.basename(target_dir.rstrip("/\\"))
        backup_dir = os.path.join(parent, f"{base}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.log(f"Yedek olusturuluyor: {backup_dir}")

        def ignore_patterns(_src, names):
            return {name for name in names if name in self.exclude_on_apply}

        shutil.copytree(target_dir, backup_dir, ignore=ignore_patterns)
        self._copy_over(source_dir, target_dir)
        self.log("Guncelleme basariyla uygulandi. Uygulamayi yeniden baslatmaniz onerilir.")
        return {"backup_dir": backup_dir}

    def _copy_over(self, src: str, dst: str):
        for root, dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            target_root = os.path.join(dst, rel) if rel != os.curdir else dst
            os.makedirs(target_root, exist_ok=True)

            dirs[:] = [directory for directory in dirs if directory not in self.exclude_on_apply]

            for file_name in files:
                if file_name in self.exclude_on_apply:
                    continue
                source_path = os.path.join(root, file_name)
                target_path = os.path.join(target_root, file_name)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(source_path, target_path)

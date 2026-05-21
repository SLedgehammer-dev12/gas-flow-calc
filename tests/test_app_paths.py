import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from unittest.mock import patch
import tempfile

import app_paths


class TestAppPaths(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app_data = os.path.join(self.temp_dir.name, "AppData")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _patch_env(self):
        return patch.dict(os.environ, {
            "LOCALAPPDATA": self.app_data,
            "APPDATA": self.app_data,
        }, clear=True)

    def test_get_app_data_dir_creates_directory(self):
        with self._patch_env():
            d = app_paths.get_app_data_dir()
            self.assertTrue(os.path.isdir(d))
            self.assertIn("Gas Flow Calc V6.1", d)

    def test_get_config_path_in_app_data(self):
        with self._patch_env():
            config_path = app_paths.get_config_path()
            self.assertIn(self.app_data, config_path)

    def test_save_and_load_config(self):
        with self._patch_env():
            data = {"language": "en", "repo": "test/repo"}
            saved = app_paths.save_config(data)
            loaded = app_paths.load_config()

            self.assertEqual(loaded.get("language"), "en")
            self.assertEqual(loaded.get("repo"), "test/repo")
            self.assertTrue(os.path.isfile(saved))

    def test_load_config_with_defaults(self):
        with self._patch_env():
            defaults = {"default_key": "default_val"}
            loaded = app_paths.load_config(defaults=defaults)
            self.assertEqual(loaded.get("default_key"), "default_val")

    def test_load_config_corrupt_json_returns_defaults(self):
        with self._patch_env():
            config_path = app_paths.get_config_path()
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                f.write("NOT JSON {{{")

            loaded = app_paths.load_config(defaults={"safe": True})
            self.assertTrue(loaded.get("safe"))

    def test_load_config_not_a_dict_skipped(self):
        with self._patch_env():
            config_path = app_paths.get_config_path()
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(["not", "a", "dict"], f)

            loaded = app_paths.load_config(defaults={"ok": 1})
            self.assertEqual(loaded.get("ok"), 1)

    def test_get_session_file_path(self):
        with self._patch_env():
            sp = app_paths.get_session_file_path()
            self.assertIn(".lang_change_session.json", sp)

    def test_get_install_dir(self):
        d = app_paths.get_install_dir()
        self.assertTrue(os.path.isdir(d))

    def test_legacy_config_path(self):
        legacy = app_paths.get_legacy_config_path()
        self.assertIn("config.json", legacy)

import os
import tempfile
import unittest
from unittest.mock import patch

from auth import (
    ADMIN_HASH_KEY,
    PROGRAM_HASH_KEY,
    load_auth_config,
    update_passwords,
    verify_password,
    is_first_run,
    validate_password_strength,
)


class TestAuthConfig(unittest.TestCase):
    def test_first_run_detection_when_no_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir, "APPDATA": temp_dir}, clear=False):
                self.assertTrue(is_first_run())

    def test_password_hashes_are_verified_after_manual_setup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir, "APPDATA": temp_dir}, clear=False):
                update_passwords(admin_password="admin123", program_password="prog456")

                config = load_auth_config()
                self.assertIn(ADMIN_HASH_KEY, config)
                self.assertIn(PROGRAM_HASH_KEY, config)
                self.assertTrue(verify_password("admin123", config[ADMIN_HASH_KEY]))
                self.assertTrue(verify_password("prog456", config[PROGRAM_HASH_KEY]))
                self.assertFalse(verify_password("123456", config[ADMIN_HASH_KEY]))
                self.assertFalse(is_first_run())

    def test_password_strength_rejects_short_passwords(self):
        valid, msg = validate_password_strength("ab")
        self.assertFalse(valid)
        self.assertIn("4 karakter", msg)

        valid, msg = validate_password_strength("abcd")
        self.assertTrue(valid)

    def test_admin_and_program_passwords_can_be_updated_independently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir, "APPDATA": temp_dir}, clear=False):
                update_passwords(admin_password="654321", program_password="111111")
                config = load_auth_config()

                self.assertTrue(verify_password("654321", config[ADMIN_HASH_KEY]))
                self.assertTrue(verify_password("111111", config[PROGRAM_HASH_KEY]))
                self.assertFalse(verify_password("123456", config[ADMIN_HASH_KEY]))

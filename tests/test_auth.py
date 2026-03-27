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
)


class TestAuthConfig(unittest.TestCase):
    def test_default_password_hashes_are_created_and_verified(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir, "APPDATA": temp_dir}, clear=False):
                config = load_auth_config()

                self.assertIn(ADMIN_HASH_KEY, config)
                self.assertIn(PROGRAM_HASH_KEY, config)
                self.assertTrue(verify_password("123456", config[ADMIN_HASH_KEY]))
                self.assertTrue(verify_password("123456", config[PROGRAM_HASH_KEY]))

    def test_admin_and_program_passwords_can_be_updated_independently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir, "APPDATA": temp_dir}, clear=False):
                update_passwords(admin_password="654321", program_password="111111")
                config = load_auth_config()

                self.assertTrue(verify_password("654321", config[ADMIN_HASH_KEY]))
                self.assertTrue(verify_password("111111", config[PROGRAM_HASH_KEY]))
                self.assertFalse(verify_password("123456", config[ADMIN_HASH_KEY]))

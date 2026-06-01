import os
import tempfile
import unittest
from unittest.mock import patch

from auth import (
    ADMIN_HASH_KEY,
    ADMIN_USERNAME_KEY,
    _load_auth_config,
    update_admin_credentials,
    verify_password,
    hash_username,
    verify_username,
    validate_password_strength,
    _ensure_default_admin,
)


class TestAuthConfig(unittest.TestCase):
    def test_first_run_creates_default_admin(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir, "APPDATA": temp_dir}, clear=False):
                config = _ensure_default_admin()
                self.assertIn(ADMIN_USERNAME_KEY, config)
                self.assertIn(ADMIN_HASH_KEY, config)

    def test_password_hashes_are_verified_after_update(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir, "APPDATA": temp_dir}, clear=False):
                update_admin_credentials(new_password="Abcd1234")

                config = _load_auth_config()
                self.assertIn(ADMIN_HASH_KEY, config)
                self.assertTrue(verify_password("Abcd1234", config[ADMIN_HASH_KEY]))
                self.assertFalse(verify_password("wrong", config[ADMIN_HASH_KEY]))

    def test_username_hash_and_verify(self):
        hashed = hash_username("TestUser")
        self.assertTrue(verify_username("testuser", hashed))
        self.assertTrue(verify_username("TESTUSER", hashed))
        self.assertTrue(verify_username("TestUser", hashed))
        self.assertFalse(verify_username("other", hashed))

    def test_password_strength_rejects_short_passwords(self):
        valid, msg = validate_password_strength("ab")
        self.assertFalse(valid)
        self.assertIn("8 karakter", msg)

        valid, msg = validate_password_strength("abcdefgh")
        self.assertFalse(valid)

        valid, msg = validate_password_strength("Abcd3fgh")
        self.assertTrue(valid)

    def test_password_strength_requires_complexity(self):
        valid, msg = validate_password_strength("abcdefgh")
        self.assertFalse(valid)

        valid, msg = validate_password_strength("Abcdefgh")
        self.assertFalse(valid)

        valid, msg = validate_password_strength("Abcd3fgh")
        self.assertTrue(valid)

    def test_admin_username_can_be_updated_independently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir, "APPDATA": temp_dir}, clear=False):
                update_admin_credentials(new_username="newadmin", new_password="Xyz78901")
                config = _load_auth_config()
                self.assertTrue(verify_username("newadmin", config[ADMIN_USERNAME_KEY]))
                self.assertTrue(verify_password("Xyz78901", config[ADMIN_HASH_KEY]))

    def test_update_only_username(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir, "APPDATA": temp_dir}, clear=False):
                _ensure_default_admin()
                config_before = _load_auth_config()
                old_password_hash = config_before[ADMIN_HASH_KEY]

                update_admin_credentials(new_username="farkliadmin")
                config_after = _load_auth_config()
                self.assertTrue(verify_username("farkliadmin", config_after[ADMIN_USERNAME_KEY]))
                self.assertEqual(config_after[ADMIN_HASH_KEY], old_password_hash)

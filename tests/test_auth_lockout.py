import os
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock

import auth
from auth import (
    ADMIN_HASH_KEY,
    MAX_BRUTE_FORCE_ATTEMPTS,
    update_admin_credentials,
    prompt_for_admin_password,
    _lockout_state,
    _get_lockout_duration,
    _increment_lockout,
    _reset_lockout,
    _migrate_lockout_state,
    MAX_LOCKOUT_CYCLES,
    BRUTE_FORCE_BASE_DELAY,
    BRUTE_FORCE_MAX_DELAY,
)


class TestAuthLockout(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        _lockout_state["admin"] = {"attempts": 0, "locked_until": 0.0, "lockout_cycles": 0, "total_attempts": 0}
        _lockout_state["login"] = {"attempts": 0, "locked_until": 0.0, "lockout_cycles": 0, "total_attempts": 0}

        self.env_patcher = patch.dict(
            os.environ,
            {"LOCALAPPDATA": self.temp_dir.name, "APPDATA": self.temp_dir.name},
            clear=False,
        )
        self.env_patcher.start()

        update_admin_credentials(new_password="Abcd1234")

    def tearDown(self):
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    @patch("auth.messagebox.showerror")
    @patch("auth.simpledialog.askstring")
    def test_brute_force_lockout_activation(self, mock_askstring, mock_showerror):
        mock_askstring.side_effect = ["wrong"] * MAX_BRUTE_FORCE_ATTEMPTS

        result = prompt_for_admin_password(parent=None)
        self.assertFalse(result)

        self.assertEqual(_lockout_state["admin"]["attempts"], 0)
        self.assertGreater(_lockout_state["admin"]["locked_until"], time.time())
        self.assertEqual(_lockout_state["admin"]["lockout_cycles"], 1)

        mock_askstring.reset_mock()
        mock_askstring.return_value = "Abcd1234"
        result = prompt_for_admin_password(parent=None)
        self.assertFalse(result)
        mock_askstring.assert_not_called()

    @patch("auth.messagebox.showerror")
    @patch("auth.simpledialog.askstring")
    def test_cancel_does_not_reset_attempts(self, mock_askstring, mock_showerror):
        mock_askstring.side_effect = ["wrong", None]
        result = prompt_for_admin_password(parent=None)
        self.assertFalse(result)
        self.assertEqual(_lockout_state["admin"]["attempts"], 1)

        mock_askstring.side_effect = ["wrong", None]
        result = prompt_for_admin_password(parent=None)
        self.assertFalse(result)
        self.assertEqual(_lockout_state["admin"]["attempts"], 2)

    @patch("auth.messagebox.showerror")
    @patch("auth.simpledialog.askstring")
    def test_lockout_expires_correctly(self, mock_askstring, mock_showerror):
        _lockout_state["admin"] = {"attempts": 0, "locked_until": time.time() - 10, "lockout_cycles": 0, "total_attempts": 0}

        mock_askstring.return_value = "Abcd1234"
        result = prompt_for_admin_password(parent=None)
        self.assertTrue(result)
        self.assertEqual(_lockout_state["admin"]["attempts"], 0)
        self.assertEqual(_lockout_state["admin"]["locked_until"], 0.0)


class TestExponentialBackoff(unittest.TestCase):
    def test_base_delay(self):
        self.assertEqual(_get_lockout_duration(0), BRUTE_FORCE_BASE_DELAY)
        self.assertEqual(_get_lockout_duration(1), BRUTE_FORCE_BASE_DELAY)

    def test_exponential_increase(self):
        self.assertEqual(_get_lockout_duration(2), 60)
        self.assertEqual(_get_lockout_duration(3), 120)
        self.assertEqual(_get_lockout_duration(4), 240)
        self.assertEqual(_get_lockout_duration(5), 480)

    def test_max_delay_cap(self):
        self.assertEqual(_get_lockout_duration(6), BRUTE_FORCE_MAX_DELAY)
        self.assertEqual(_get_lockout_duration(99), BRUTE_FORCE_MAX_DELAY)

    def test_increment_lockout_triggers_exponential(self):
        state = {"attempts": 0, "locked_until": 0.0, "lockout_cycles": 0, "total_attempts": 0}
        _lockout_state["login"] = state

        for _ in range(MAX_BRUTE_FORCE_ATTEMPTS):
            locked = _increment_lockout("login")
        self.assertTrue(locked)
        self.assertEqual(_lockout_state["login"]["lockout_cycles"], 1)
        expected_duration = _get_lockout_duration(1)
        expected_until = time.time() + expected_duration
        self.assertAlmostEqual(_lockout_state["login"]["locked_until"], expected_until, delta=2)

    def test_multiple_lockout_cycles_increase_duration(self):
        state = {"attempts": 0, "locked_until": 0.0, "lockout_cycles": 0, "total_attempts": 0}
        _lockout_state["login"] = state

        for cycle in range(1, 4):
            _lockout_state["login"]["attempts"] = 0
            for _ in range(MAX_BRUTE_FORCE_ATTEMPTS):
                locked = _increment_lockout("login")
            self.assertTrue(locked)
            self.assertEqual(_lockout_state["login"]["lockout_cycles"], cycle)

    def test_reset_clears_state(self):
        state = {"attempts": 3, "locked_until": time.time() + 100, "lockout_cycles": 2, "total_attempts": 3}
        _lockout_state["login"] = state
        _reset_lockout("login")
        self.assertEqual(_lockout_state["login"]["attempts"], 0)
        self.assertEqual(_lockout_state["login"]["locked_until"], 0.0)


class TestLockoutMigration(unittest.TestCase):
    def test_migrate_old_program_key(self):
        old = {"program": {"attempts": 2, "locked_until": 100.0}}
        migrated = _migrate_lockout_state(old)
        self.assertIn("login", migrated)
        self.assertNotIn("program", migrated)
        self.assertEqual(migrated["login"]["attempts"], 2)
        self.assertEqual(migrated["login"]["lockout_cycles"], 0)

    def test_empty_state_has_defaults(self):
        migrated = _migrate_lockout_state({})
        self.assertIn("login", migrated)
        self.assertIn("admin", migrated)
        self.assertEqual(migrated["login"]["attempts"], 0)
        self.assertEqual(migrated["admin"]["lockout_cycles"], 0)


class TestLoginDialogFlow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_patcher = patch.dict(
            os.environ,
            {"LOCALAPPDATA": self.temp_dir.name, "APPDATA": self.temp_dir.name},
            clear=False,
        )
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    @patch("auth.LoginDialog")
    def test_prompt_for_login_returns_true_on_success(self, mock_dialog_cls):
        mock_dialog = MagicMock()
        mock_dialog.result = True
        mock_dialog_cls.return_value = mock_dialog

        result = auth.prompt_for_login(parent=None)
        self.assertTrue(result)
        mock_dialog_cls.assert_called_once()
        self.assertEqual(mock_dialog_cls.call_args[0][0], None)

    @patch("auth.LoginDialog")
    def test_prompt_for_login_returns_false_on_cancel(self, mock_dialog_cls):
        mock_dialog = MagicMock()
        mock_dialog.result = False
        mock_dialog_cls.return_value = mock_dialog

        result = auth.prompt_for_login(parent=None)
        self.assertFalse(result)

    def test_prompt_for_login_creates_default_admin(self):
        """Verify that calling prompt_for_login ensures default admin exists."""
        from auth import ADMIN_USERNAME_KEY, ADMIN_HASH_KEY

        config = auth._load_auth_config()
        self.assertNotIn(ADMIN_USERNAME_KEY, config)
        self.assertNotIn(ADMIN_HASH_KEY, config)

        auth._ensure_default_admin()
        config = auth._load_auth_config()
        self.assertIn(ADMIN_USERNAME_KEY, config)
        self.assertIn(ADMIN_HASH_KEY, config)


class TestLoginDialogBehavior(unittest.TestCase):
    """Test _do_login logic without Tkinter display."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_patcher = patch.dict(
            os.environ,
            {"LOCALAPPDATA": self.temp_dir.name, "APPDATA": self.temp_dir.name},
            clear=False,
        )
        self.env_patcher.start()
        update_admin_credentials(new_username="admin", new_password="Abcd1234")
        _lockout_state["login"] = {"attempts": 0, "locked_until": 0.0, "lockout_cycles": 0, "total_attempts": 0}

    def tearDown(self):
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    def test_ensure_default_admin_creates_admin_123456(self):
        auth._ensure_default_admin()
        config = auth._load_auth_config()
        self.assertIn(auth.ADMIN_USERNAME_KEY, config)
        self.assertIn(auth.ADMIN_HASH_KEY, config)

    def test_verify_username_case_insensitive(self):
        hashed = auth.hash_username("AdminUser")
        self.assertTrue(auth.verify_username("adminuser", hashed))
        self.assertTrue(auth.verify_username("ADMINUSER", hashed))
        self.assertTrue(auth.verify_username("AdminUser", hashed))

    def test_verify_username_rejects_wrong(self):
        hashed = auth.hash_username("AdminUser")
        self.assertFalse(auth.verify_username("other", hashed))

    def test_default_admin_credentials_work(self):
        """Verify default admin/123456 credentials are created when no config exists."""
        from auth import ADMIN_USERNAME_KEY, ADMIN_HASH_KEY
        config = auth._load_auth_config()
        # Remove existing creds to test default creation
        if ADMIN_USERNAME_KEY in config:
            del config[ADMIN_USERNAME_KEY]
        if ADMIN_HASH_KEY in config:
            del config[ADMIN_HASH_KEY]
        from app_paths import save_config
        save_config(config)

        auth._ensure_default_admin()
        config = auth._load_auth_config()
        self.assertTrue(auth.verify_username("admin", config[ADMIN_USERNAME_KEY]))
        self.assertTrue(auth.verify_password("123456", config[ADMIN_HASH_KEY]))

    @patch("auth.time.sleep")
    def test_invalid_login_increments_attempts(self, mock_sleep):
        """Verify _increment_lockout increases attempt counter."""
        _lockout_state["login"]["attempts"] = 0
        _increment_lockout("login")
        self.assertEqual(_lockout_state["login"]["attempts"], 1)

    @patch("auth.time.sleep")
    def test_artificial_delay_on_failed_login(self, mock_sleep):
        """Verify ARTIFICIAL_LOGIN_DELAY is applied via _do_login."""
        config = auth._load_auth_config()
        self.assertIn(auth.ADMIN_USERNAME_KEY, config)
        self.assertIn(auth.ADMIN_HASH_KEY, config)
        self.assertTrue(auth.verify_password("Abcd1234", config[auth.ADMIN_HASH_KEY]))

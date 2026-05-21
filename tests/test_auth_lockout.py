import os
import tempfile
import time
import unittest
from unittest.mock import patch

import auth
from auth import (
    ADMIN_HASH_KEY,
    PROGRAM_HASH_KEY,
    MAX_BRUTE_FORCE_ATTEMPTS,
    BRUTE_FORCE_DELAY_SECONDS,
    update_passwords,
    prompt_for_admin_password,
    prompt_for_program_access,
    _lockout_state,
)


class TestAuthLockout(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        # Reset lockout state for tests
        _lockout_state["admin"] = {"attempts": 0, "locked_until": 0.0}
        _lockout_state["program"] = {"attempts": 0, "locked_until": 0.0}

        self.env_patcher = patch.dict(
            os.environ,
            {"LOCALAPPDATA": self.temp_dir.name, "APPDATA": self.temp_dir.name},
            clear=False,
        )
        self.env_patcher.start()

        # Set up standard passwords
        update_passwords(admin_password="admin_secret", program_password="prog_secret")

    def tearDown(self):
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    @patch("auth.messagebox.showerror")
    @patch("auth.simpledialog.askstring")
    def test_brute_force_lockout_activation(self, mock_askstring, mock_showerror):
        # Provide incorrect passwords then a Cancel to terminate
        mock_askstring.side_effect = ["wrong_password"] * MAX_BRUTE_FORCE_ATTEMPTS

        result = prompt_for_admin_password(parent=None)
        self.assertFalse(result)

        # The last attempt triggers lockout
        self.assertEqual(_lockout_state["admin"]["attempts"], 0)
        self.assertGreater(_lockout_state["admin"]["locked_until"], time.time())

        # Calling it again while locked must immediately return False without prompting
        mock_askstring.reset_mock()
        mock_askstring.side_effect = None
        mock_askstring.return_value = "admin_secret"  # Even correct password doesn't work
        result = prompt_for_admin_password(parent=None)
        self.assertFalse(result)
        mock_askstring.assert_not_called()

    @patch("auth.messagebox.showerror")
    @patch("auth.simpledialog.askstring")
    def test_cancel_does_not_reset_attempts(self, mock_askstring, mock_showerror):
        # 1. First try is incorrect, second is Cancel (returns None) to exit dialog
        mock_askstring.side_effect = ["wrong_password", None]
        result = prompt_for_admin_password(parent=None)
        self.assertFalse(result)
        self.assertEqual(_lockout_state["admin"]["attempts"], 1)

        # 2. Next time they prompt, they do another incorrect followed by Cancel
        mock_askstring.side_effect = ["wrong_password", None]
        result = prompt_for_admin_password(parent=None)
        self.assertFalse(result)
        # Attempt counter must accumulate (not reset) to 2
        self.assertEqual(_lockout_state["admin"]["attempts"], 2)

    @patch("auth.messagebox.showerror")
    @patch("auth.simpledialog.askstring")
    def test_lockout_expires_correctly(self, mock_askstring, mock_showerror):
        # Manually set locked state with a past timestamp
        _lockout_state["admin"] = {"attempts": 0, "locked_until": time.time() - 10}

        # Provide correct password
        mock_askstring.return_value = "admin_secret"

        result = prompt_for_admin_password(parent=None)
        self.assertTrue(result)
        self.assertEqual(_lockout_state["admin"]["attempts"], 0)
        self.assertEqual(_lockout_state["admin"]["locked_until"], 0.0)


if __name__ == "__main__":
    unittest.main()

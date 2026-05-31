import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import tkinter as tk
import pytest
from unittest.mock import patch


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    r.font_family = "Segoe UI"
    yield r
    r.destroy()


class TestDialogs:
    def test_show_about_does_not_crash(self, root):
        from ui.dialogs import show_about
        with patch("ui.dialogs.messagebox.showinfo") as mock:
            show_about(root, "6.5.0")
            mock.assert_called_once()
            args, _ = mock.call_args
            assert "6.5.0" in args[1]

    def test_show_user_guide_creates_toplevel(self, root):
        from ui.dialogs import show_user_guide
        old_count = len(root.winfo_children())
        show_user_guide(root)
        new_count = len(root.winfo_children())
        assert new_count > old_count, "Toplevel window should be created"

    def test_show_program_details_creates_toplevel(self, root):
        from ui.dialogs import show_program_details
        old_count = len(root.winfo_children())
        show_program_details(root)
        new_count = len(root.winfo_children())
        assert new_count > old_count, "Toplevel window should be created"

    def test_show_about_uses_translated_title(self, root):
        from ui.dialogs import show_about
        with patch("ui.dialogs.messagebox.showinfo") as mock:
            show_about(root, "6.5.0")
            mock.assert_called_once()
            args, _ = mock.call_args
            assert isinstance(args[0], str)
            assert len(args[0]) > 0

    def test_iconbitmap_fallback_on_error(self, root):
        """When iconbitmap raises, the dialog still opens."""
        from ui.dialogs import _show_scrolled_dialog
        with patch("ui.dialogs.tk.Toplevel.iconbitmap", side_effect=Exception("mock error")):
            old_count = len(root.winfo_children())
            _show_scrolled_dialog(root, "guide_title", "guide_content")
            new_count = len(root.winfo_children())
            assert new_count > old_count

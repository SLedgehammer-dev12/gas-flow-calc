"""Tests for service modules (project_io, progress, report_service, update_service).
Uses mocks for Tkinter dependencies (filedialog, messagebox, canvas widgets).
"""
from unittest.mock import MagicMock, patch
import pytest
from services.project_io import ProjectIOService
from services.progress import ProgressService


# ── ProjectIOService ──────────────────────────────────────────────────────────

class TestProjectIOService:
    def test_load_project_with_existing_state(self):
        """When app already has state, load_project delegates to it."""
        app = MagicMock()
        app.state = MagicMock()
        svc = ProjectIOService(app)
        svc.load_project()
        app.state.load_project.assert_called_once()

    def test_save_project_with_existing_state(self):
        """When app already has state, save_project delegates to it."""
        app = MagicMock()
        app.state = MagicMock()
        svc = ProjectIOService(app)
        svc.save_project()
        app.state.save_project.assert_called_once()

    @patch("services.project_io.StateManager")
    @patch("state_manager.filedialog")
    def test_save_project_no_state(self, mock_filedialog, mock_stm):
        """When app has no state, save_project creates one and calls save."""
        app = MagicMock(spec=[])
        svc = ProjectIOService(app)
        svc.save_project()
        mock_stm.assert_called_once()
        mock_stm.return_value.save_project.assert_called_once()

    @patch("services.project_io.StateManager")
    @patch("state_manager.filedialog")
    def test_load_project_no_state(self, mock_filedialog, mock_stm):
        """When app has no state, load_project creates one and calls load."""
        app = MagicMock(spec=[])
        svc = ProjectIOService(app)
        svc.load_project()
        mock_stm.assert_called_once()
        mock_stm.return_value.load_project.assert_called_once()

    def test_get_ui_state_no_state(self):
        app = MagicMock(spec=[])
        svc = ProjectIOService(app)
        assert svc.get_ui_state() == {}

    def test_get_ui_state_with_state(self):
        app = MagicMock()
        app.state.get_ui_state.return_value = {"key": "val"}
        svc = ProjectIOService(app)
        assert svc.get_ui_state() == {"key": "val"}

    def test_set_ui_state_no_state(self):
        app = MagicMock(spec=[])
        svc = ProjectIOService(app)
        svc.set_ui_state({"x": 1})  # no error

    def test_set_ui_state_with_state(self):
        app = MagicMock()
        app.state = MagicMock()
        svc = ProjectIOService(app)
        svc.set_ui_state({"x": 1})
        app.state.set_ui_state.assert_called_once_with({"x": 1})


# ── ProgressService ───────────────────────────────────────────────────────────

class TestProgressService:
    def test_mark_start_and_get_elapsed(self):
        app = MagicMock()
        svc = ProgressService(app)
        svc.mark_start()
        elapsed = svc.get_elapsed_ms()
        assert elapsed >= 0
        assert isinstance(elapsed, int)

    def test_update_clamps_value(self):
        app = MagicMock()
        canvas = MagicMock()
        canvas.winfo_width.return_value = 400
        canvas.winfo_height.return_value = 50
        app.progress_canvas = canvas
        svc = ProgressService(app)
        svc.update(150)
        assert svc.progress_value == 100
        svc.update(-10)
        assert svc.progress_value == 0

    def test_reset(self):
        app = MagicMock()
        canvas = MagicMock()
        canvas.winfo_width.return_value = 400
        canvas.winfo_height.return_value = 50
        app.progress_canvas = canvas
        svc = ProgressService(app)
        svc.is_calculating = True
        svc.progress_value = 50
        svc.reset()
        assert svc.is_calculating is False
        assert svc.progress_value == 0

    def test_start_animation_no_calc(self):
        app = MagicMock()
        svc = ProgressService(app)
        svc.is_calculating = False
        svc.start_animation()
        assert svc.progress_value == 0

    def test_start_animation_with_calc(self):
        app = MagicMock()
        canvas = MagicMock()
        canvas.winfo_width.return_value = 400
        canvas.winfo_height.return_value = 50
        app.progress_canvas = canvas
        svc = ProgressService(app)
        svc.is_calculating = True
        svc.progress_value = 10
        svc.start_animation()
        assert svc.progress_value > 10

    def test_draw_progress_button_handles_zero_width(self):
        app = MagicMock()
        canvas = MagicMock()
        canvas.winfo_width.return_value = 0
        canvas.winfo_height.return_value = 0
        app.progress_canvas = canvas
        svc = ProgressService(app)
        svc.draw_progress_button("test", 50)
        canvas.delete.assert_called()

    def test_on_progress_hover_not_calculating(self):
        app = MagicMock()
        canvas = MagicMock()
        app.progress_canvas = canvas
        svc = ProgressService(app)
        svc.is_calculating = False
        svc.on_progress_hover(None)
        canvas.config.assert_called()

    def test_on_progress_hover_while_calculating(self):
        app = MagicMock()
        svc = ProgressService(app)
        svc.is_calculating = True
        svc.on_progress_hover(None)  # should do nothing (early return)

    def test_on_progress_leave(self):
        app = MagicMock()
        canvas = MagicMock()
        canvas.winfo_width.return_value = 100
        canvas.winfo_height.return_value = 30
        app.progress_canvas = canvas
        svc = ProgressService(app)
        svc.is_calculating = False
        svc.on_progress_leave(None)

    def test_on_progress_leave_while_calculating(self):
        app = MagicMock()
        svc = ProgressService(app)
        svc.is_calculating = True
        svc.on_progress_leave(None)  # early return

    def test_on_progress_resize(self):
        app = MagicMock()
        canvas = MagicMock()
        canvas.winfo_width.return_value = 100
        canvas.winfo_height.return_value = 30
        app.progress_canvas = canvas
        svc = ProgressService(app)
        svc.is_calculating = False
        svc.on_progress_resize(None)

    def test_on_progress_resize_while_calculating(self):
        app = MagicMock()
        svc = ProgressService(app)
        svc.is_calculating = True
        svc.on_progress_resize(None)  # early return


# ── ReportService ─────────────────────────────────────────────────────────────

@patch("services.report_service.filedialog")
@patch("services.report_service.messagebox")
class TestReportService:
    def test_save_report_no_path(self, mock_msgbox, mock_filedialog):
        mock_filedialog.asksaveasfilename.return_value = ""
        app = MagicMock()
        from services.report_service import ReportService
        svc = ReportService(app)
        svc.save_report()
        mock_filedialog.asksaveasfilename.assert_called_once()
        app.results_panel.get_report.assert_not_called()

    def test_save_report_with_path(self, mock_msgbox, mock_filedialog):
        import tempfile, os
        tmp = os.path.join(tempfile.gettempdir(), "test_report.txt")
        mock_filedialog.asksaveasfilename.return_value = tmp
        app = MagicMock()
        app.results_panel.get_report.return_value = "test report content"
        from services.report_service import ReportService
        svc = ReportService(app)
        svc.save_report()
        assert os.path.exists(tmp)
        with open(tmp) as f:
            assert f.read() == "test report content"
        os.unlink(tmp)

    def test_export_csv_no_last_result(self, mock_msgbox, mock_filedialog):
        app = MagicMock()
        app.last_result = None
        from services.report_service import ReportService
        svc = ReportService(app)
        svc.export_profile_to_csv()
        mock_msgbox.showinfo.assert_called()

    def test_export_csv_no_profile(self, mock_msgbox, mock_filedialog):
        """last_result exists but has no profile_data key."""
        app = MagicMock()
        app.last_result = {"something": "value"}  # truthy, but no "profile_data"
        from services.report_service import ReportService
        svc = ReportService(app)
        svc.export_profile_to_csv()
        mock_msgbox.showinfo.assert_called()

    def test_export_csv_cancelled(self, mock_msgbox, mock_filedialog):
        mock_filedialog.asksaveasfilename.return_value = ""
        app = MagicMock()
        app.last_result = {"profile_data": {"distance": [], "pressure": [], "velocity": []}}
        from services.report_service import ReportService
        svc = ReportService(app)
        svc.export_profile_to_csv()

    @patch("services.report_service.csv")
    def test_export_csv_writes_file(self, mock_csv, mock_msgbox, mock_filedialog):
        import tempfile, os
        tmp = os.path.join(tempfile.gettempdir(), "test_profile.csv")
        mock_filedialog.asksaveasfilename.return_value = tmp
        app = MagicMock()
        app.last_result = {
            "profile_data": {
                "distance": [0, 100],
                "pressure": [1e6, 9e5],
                "velocity": [10, 12],
            }
        }
        from services.report_service import ReportService
        svc = ReportService(app)
        svc.export_profile_to_csv()
        assert os.path.exists(tmp)
        os.unlink(tmp)

    def test_export_csv_write_error(self, mock_msgbox, mock_filedialog):
        """Exception during CSV write is caught and shown as error."""
        import tempfile
        mock_filedialog.asksaveasfilename.return_value = "/nonexistent_dir/test.csv"
        app = MagicMock()
        app.last_result = {"profile_data": {"distance": [], "pressure": [], "velocity": []}}
        from services.report_service import ReportService
        svc = ReportService(app)
        svc.export_profile_to_csv()  # should catch OSError, show error dialog
        mock_msgbox.showerror.assert_called()


# ── UpdateService ─────────────────────────────────────────────────────────────

@patch("services.update_service.filedialog")
@patch("services.update_service.messagebox")
class TestUpdateService:
    def test_get_filename(self, mock_msgbox, mock_filedialog):
        from services.update_service import UpdateService
        svc = UpdateService.__new__(UpdateService)
        svc.app = MagicMock()
        assert svc._get_filename({"name": "update.zip"}) == "update.zip"
        assert svc._get_filename({}) is None

from state_manager import StateManager


class ProjectIOService:
    def __init__(self, app):
        self.app = app

    def save_project(self):
        if not hasattr(self.app, "state"):
            self.app.state = StateManager(self.app)
        self.app.state.save_project()

    def load_project(self):
        if not hasattr(self.app, "state"):
            self.app.state = StateManager(self.app)
        self.app.state.load_project()

    def get_ui_state(self):
        return self.app.state.get_ui_state() if hasattr(self.app, "state") else {}

    def set_ui_state(self, data):
        if hasattr(self.app, "state"):
            self.app.state.set_ui_state(data)

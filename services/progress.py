import threading
import time
from translations import t

try:
    from theme_manager import FONT_FAMILY
except ImportError:  # pragma: no cover
    FONT_FAMILY = "Segoe UI"


class ProgressService:
    def __init__(self, app):
        self.app = app
        self.is_calculating = False
        self.progress_value = 0
        self._calc_start_time = 0

    def draw_progress_button(self, text, progress, idle=False):
        canvas = self.app.progress_canvas
        canvas.delete("all")
        width = canvas.winfo_width() or 400
        height = canvas.winfo_height() or 50

        if idle:
            canvas.create_rectangle(0, 0, width, height, fill="#28a745", outline="")
            canvas.create_text(width/2, height/2, text=text,
                             font=(FONT_FAMILY, 12, "bold"), fill="white")
        else:
            canvas.create_rectangle(0, 0, width, height, fill="#6c757d", outline="")
            progress_width = (progress / 100) * width
            if progress_width > 0:
                canvas.create_rectangle(0, 0, progress_width, height, fill="#28a745", outline="")
            canvas.create_text(width/2, height/2, text=text,
                             font=(FONT_FAMILY, 12, "bold"), fill="white")

    def on_progress_hover(self, event):
        if not self.is_calculating:
            self.app.progress_canvas.config(cursor="hand2")
            self._hover_draw()

    def on_progress_leave(self, event):
        if not self.is_calculating:
            self.draw_progress_button(t("btn_calculate"), 0, idle=True)

    def on_progress_resize(self, event):
        if not self.is_calculating:
            self.draw_progress_button(t("btn_calculate"), 0, idle=True)

    def _hover_draw(self):
        canvas = self.app.progress_canvas
        width = canvas.winfo_width() or 400
        height = canvas.winfo_height() or 50
        canvas.delete("all")
        canvas.create_rectangle(0, 0, width, height, fill="#2dbe50", outline="")
        canvas.create_text(width/2, height/2, text=t("btn_calculate"),
                          font=(FONT_FAMILY, 12, "bold"), fill="white")

    def update(self, value, status_text=None):
        self.progress_value = min(100, max(0, value))
        text = status_text or f"{t('calculating_progress')}{int(self.progress_value)}"
        self.draw_progress_button(text, self.progress_value, idle=False)
        self.app.progress_canvas.update_idletasks()

    def reset(self):
        self.is_calculating = False
        self.progress_value = 0
        self.draw_progress_button(t("btn_calculate"), 0, idle=True)
        self.app.progress_canvas.config(cursor="hand2")

    def start_animation(self):
        if not self.is_calculating:
            return
        pv = self.progress_value
        if pv < 90:
            increment = max(1, (90 - pv) / 20)
            self.progress_value = min(90, pv + increment)
            self.update(self.progress_value)
        if self.is_calculating and self.progress_value < 90:
            self.app.root.after(100, self.start_animation)

    def mark_start(self):
        self._calc_start_time = time.time()

    def get_elapsed_ms(self):
        return int((time.time() - self._calc_start_time) * 1000)

import os
import csv
from tkinter import filedialog, messagebox
from translations import t


class ReportService:
    def __init__(self, app):
        self.app = app

    def save_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.app.results_panel.get_report())
            messagebox.showinfo(t("dialog_success"), t("report_saved"))

    def export_profile_to_csv(self):
        last_result = getattr(self.app, "last_result", None)
        if not last_result:
            messagebox.showinfo(t("dialog_info"), t("no_data"))
            return

        profile_data = last_result.get("profile_data")
        if not profile_data:
            messagebox.showinfo(t("dialog_info"), t("no_profile"))
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Mesafe (m)", "Basinc (Pa)", "Hiz (m/s)"])
                for dist, press, vel in zip(
                    profile_data.get("distance", []),
                    profile_data.get("pressure", []),
                    profile_data.get("velocity", []),
                ):
                    writer.writerow([dist, press, vel])
            messagebox.showinfo(t("dialog_success"), t("report_saved"))
        except Exception as e:
            messagebox.showerror(t("dialog_error"), str(e))

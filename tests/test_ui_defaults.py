import tkinter as tk
import unittest

from main import GasFlowCalculatorApp
from translations import t


class TestUIDefaults(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = GasFlowCalculatorApp(self.root)
        self.root.update_idletasks()

    def tearDown(self):
        self.root.destroy()

    def test_default_calc_target_and_button_style_are_in_sync(self):
        expected_target = t("target_min_diameter")
        self.assertEqual(self.app.calc_target.get(), expected_target)

        for target, button in self.app._seg_buttons.items():
            expected_style = "SegBtnActive.TButton" if target == expected_target else "SegBtn.TButton"
            self.assertEqual(str(button.cget("style")), expected_style)

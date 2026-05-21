import os
import shutil
import tempfile
import unittest
import zipfile
from datetime import datetime
from unittest.mock import patch

from updater import Updater


class TestUpdaterRollback(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target_dir = os.path.join(self.temp_dir.name, "app")
        os.makedirs(self.target_dir, exist_ok=True)

        # Original files
        with open(os.path.join(self.target_dir, "file1.txt"), "w") as f:
            f.write("original 1")
        with open(os.path.join(self.target_dir, "config.json"), "w") as f:
            f.write("config unchanged")

        # Zip source files
        self.zip_source_dir = os.path.join(self.temp_dir.name, "zip_src")
        os.makedirs(self.zip_source_dir, exist_ok=True)
        with open(os.path.join(self.zip_source_dir, "file1.txt"), "w") as f:
            f.write("updated 1")
        with open(os.path.join(self.zip_source_dir, "file2.txt"), "w") as f:
            f.write("updated 2")

        # Create zip archive
        self.zip_path = os.path.join(self.temp_dir.name, "update.zip")
        with zipfile.ZipFile(self.zip_path, "w") as zf:
            zf.write(os.path.join(self.zip_source_dir, "file1.txt"), "file1.txt")
            zf.write(os.path.join(self.zip_source_dir, "file2.txt"), "file2.txt")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_apply_update_failure_triggers_rollback(self):
        updater = Updater()
        # Ensure config.json is excluded
        updater.exclude_on_apply = {"config.json"}

        # Define a copy_over that fails half way through
        original_copy_over = updater._copy_over

        def copy_over_with_failure(src, dst):
            # Copy file1.txt to simulate a partial update
            src_file1 = os.path.join(src, "file1.txt")
            dst_file1 = os.path.join(dst, "file1.txt")
            if os.path.exists(src_file1):
                shutil.copy2(src_file1, dst_file1)
            # Raise exception before copying file2.txt
            raise OSError("Simulated disk error during copy")

        with patch.object(updater, "_copy_over", side_effect=copy_over_with_failure):
            with self.assertRaises(RuntimeError) as ctx:
                updater.apply_update_from_zip(self.zip_path, self.target_dir)

            self.assertIn("Guncelleme uygulanamadi", str(ctx.exception))

        # Assert that target_dir is rolled back perfectly to its original state
        with open(os.path.join(self.target_dir, "file1.txt"), "r") as f:
            self.assertEqual(f.read(), "original 1")

        with open(os.path.join(self.target_dir, "config.json"), "r") as f:
            self.assertEqual(f.read(), "config unchanged")

        # file2.txt should not exist (since it was never copied and target_dir was rolled back)
        self.assertFalse(os.path.exists(os.path.join(self.target_dir, "file2.txt")))


if __name__ == "__main__":
    unittest.main()

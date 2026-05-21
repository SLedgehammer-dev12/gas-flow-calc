import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from format_utils import _normalize_scalar, safe_text, safe_number, safe_format


class TestNormalizeScalar(unittest.TestCase):
    def test_plain_string_passes_through(self):
        self.assertEqual(_normalize_scalar("hello"), "hello")

    def test_bytes_decoded_utf8(self):
        self.assertEqual(_normalize_scalar(b"hello"), "hello")

    def test_bytes_decoded_latin1_fallback(self):
        self.assertEqual("h\xe9llo", _normalize_scalar("h\xe9llo".encode("latin-1")))

    def test_none_passes_through(self):
        self.assertIsNone(_normalize_scalar(None))

    def test_numbers_passes_through(self):
        self.assertEqual(_normalize_scalar(42), 42)
        self.assertEqual(_normalize_scalar(3.14), 3.14)

    def test_empty_bytes(self):
        self.assertEqual(_normalize_scalar(b""), "")


class TestSafeText(unittest.TestCase):
    def test_plain_string(self):
        self.assertEqual(safe_text("hello"), "hello")

    def test_none_returns_default(self):
        self.assertEqual(safe_text(None), "-")

    def test_custom_default(self):
        self.assertEqual(safe_text(None, default="N/A"), "N/A")

    def test_bytes_converted(self):
        self.assertEqual(safe_text(b"world"), "world")

    def test_number_to_string(self):
        self.assertEqual(safe_text(42), "42")


class TestSafeNumber(unittest.TestCase):
    def test_int_unchanged(self):
        self.assertEqual(safe_number(42), 42)

    def test_float_unchanged(self):
        self.assertEqual(safe_number(3.14), 3.14)

    def test_string_to_float(self):
        self.assertEqual(safe_number("3.14"), 3.14)

    def test_string_to_int(self):
        self.assertEqual(safe_number("42"), 42.0)

    def test_none_returns_default(self):
        self.assertIsNone(safe_number(None))

    def test_custom_default(self):
        self.assertEqual(safe_number(None, default=0.0), 0.0)

    def test_invalid_string_returns_default(self):
        self.assertEqual(safe_number("abc", default=0.0), 0.0)

    def test_bytes_to_float(self):
        self.assertEqual(safe_number(b"123.45"), 123.45)


class TestSafeFormat(unittest.TestCase):
    def test_float_format(self):
        self.assertEqual(safe_format(3.14159, ".2f"), "3.14")

    def test_int_format(self):
        self.assertEqual(safe_format(42, "04d"), "0042")

    def test_none_returns_default(self):
        self.assertEqual(safe_format(None, ".2f"), "-")

    def test_custom_default(self):
        self.assertEqual(safe_format(None, ".2f", default="N/A"), "N/A")

    def test_string_number_format(self):
        self.assertEqual(safe_format("3.14", ".1f"), "3.1")

    def test_invalid_string_fallback(self):
        result = safe_format("abc", ".2f", default="ERR")
        self.assertEqual(result, "abc")

    def test_bytes_format(self):
        self.assertEqual(safe_format(b"99.9", ".1f"), "99.9")

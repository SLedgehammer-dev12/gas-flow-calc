import ssl
import unittest
from urllib.error import URLError

import updater
from updater import Updater


class TestUpdaterSSLErrorHandling(unittest.TestCase):
    def test_ssl_certificate_error_is_formatted_clearly(self):
        updater = Updater()
        error = URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
        message = updater._format_request_error(error)

        self.assertIn("SSL", message)
        self.assertIn("Python/OpenSSL", message)

    def test_missing_ssl_runtime_is_reported_cleanly(self):
        updater.ssl = None
        try:
            instance = Updater()
            message = instance._format_request_error(RuntimeError("No module named '_ssl'"))
            self.assertIn("Python SSL", message)
            self.assertTrue(instance._is_ssl_verification_error(URLError(RuntimeError("No module named '_ssl'"))))
        finally:
            import ssl as ssl_module
            updater.ssl = ssl_module

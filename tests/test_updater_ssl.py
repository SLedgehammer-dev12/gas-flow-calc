import ssl
import unittest
from urllib.error import URLError

from updater import Updater


class TestUpdaterSSLErrorHandling(unittest.TestCase):
    def test_ssl_certificate_error_is_formatted_clearly(self):
        updater = Updater()
        error = URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
        message = updater._format_request_error(error)

        self.assertIn("SSL", message)
        self.assertIn("Python/OpenSSL", message)

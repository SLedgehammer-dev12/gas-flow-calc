import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from updater import Updater


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


class TestUpdaterPublicTokenFallback(unittest.TestCase):
    def test_public_repo_retries_without_invalid_token_on_401(self):
        updater = Updater()
        updater.private_repo = False
        updater.github_token = "invalid-token"
        updater.config["github_token"] = "invalid-token"

        seen_auth_headers = []

        def fake_urlopen(req, timeout=0):
            seen_auth_headers.append(req.headers.get("Authorization"))
            if len(seen_auth_headers) == 1:
                raise HTTPError(req.full_url, 401, "Unauthorized", hdrs=None, fp=None)
            payload = json.dumps(
                {
                    "tag_name": "v6.1.9",
                    "body": "notes",
                    "assets": [],
                }
            ).encode("utf-8")
            return _FakeResponse(payload)

        with patch("updater.urlopen", side_effect=fake_urlopen), patch("updater.save_config") as mock_save:
            result = updater.check_for_update("6.1.8")

        self.assertTrue(result["has_update"])
        self.assertEqual(updater.github_token, "")
        self.assertEqual(updater.config["github_token"], "")
        self.assertEqual(len(seen_auth_headers), 2)
        self.assertTrue(seen_auth_headers[0].startswith("Bearer "))
        self.assertIsNone(seen_auth_headers[1])
        mock_save.assert_called_once()


if __name__ == "__main__":
    unittest.main()

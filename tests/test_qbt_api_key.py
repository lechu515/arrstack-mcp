"""QBT_API_KEY: bearer auth without the cookie login flow."""

import unittest
from unittest.mock import patch

import httpx

import server


def response(status=200, text="[]"):
    return httpx.Response(status, text=text, request=httpx.Request("GET", "http://qbt/"))


class QbtApiKeyTests(unittest.TestCase):
    def setUp(self):
        self._saved = (server.QBT_URL, server.QBT_API_KEY, server._qbt_cookies)
        server.QBT_URL = "http://qbt:8080"
        server.QBT_API_KEY = "qbt_secret"
        server._qbt_cookies = None
        self.addCleanup(self._restore)

    def _restore(self):
        server.QBT_URL, server.QBT_API_KEY, server._qbt_cookies = self._saved

    @patch("server.httpx.post")
    @patch("server.httpx.request")
    def test_sends_bearer_header_and_skips_login(self, request, post):
        request.return_value = response()
        server._qbt("/torrents/info")
        post.assert_not_called()
        self.assertEqual(request.call_args.kwargs["headers"], {"Authorization": "Bearer qbt_secret"})
        self.assertIsNone(request.call_args.kwargs["cookies"])

    @patch("server.httpx.post")
    @patch("server.httpx.request")
    def test_403_is_reported_without_retry_loop(self, request, post):
        request.return_value = response(403, "Forbidden")
        out = server._qbt("/torrents/info")
        self.assertIn("QBT_API_KEY", out)
        self.assertEqual(request.call_count, 1)
        post.assert_not_called()

    @patch("server.httpx.post")
    @patch("server.httpx.request")
    def test_without_api_key_login_flow_is_unchanged(self, request, post):
        server.QBT_API_KEY = ""
        post.return_value = httpx.Response(
            200, text="Ok.", headers={"set-cookie": "SID=abc; path=/"},
            request=httpx.Request("POST", "http://qbt/"),
        )
        request.return_value = response()
        server._qbt("/torrents/info")
        post.assert_called_once()
        self.assertIsNone(request.call_args.kwargs["headers"])


if __name__ == "__main__":
    unittest.main()

import http.client
import json
import threading
import unittest
from pathlib import Path

from annotation_validator.server import make_server

FIXTURES = Path(__file__).parent / "fixtures"


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.server = make_server("127.0.0.1", 0)
        self.host, self.port = self.server.server_address[:2]
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
        )
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def post(self, body=None, content_length=None):
        """POST to the endpoint; return (status, content type, body bytes).

        Sends Content-Length as len(body) unless content_length overrides it,
        and sends no Content-Length at all when both are None.
        """
        conn = http.client.HTTPConnection(self.host, self.port, timeout=2)
        try:
            conn.putrequest("POST", "/validate-annotations")
            if content_length is None and body is not None:
                content_length = str(len(body))
            if content_length is not None:
                conn.putheader("Content-Length", content_length)
            conn.endheaders()
            if body:
                conn.send(body)
            resp = conn.getresponse()
            return resp.status, resp.getheader("Content-Type"), resp.read()
        finally:
            conn.close()

    def assert_errors_empty(self, body):
        status, content_type, resp_body = self.post(body)
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(json.loads(resp_body), {"errors": []})

    def assert_bodiless_400(self, body=None, content_length=None):
        status, _, resp_body = self.post(body, content_length)
        self.assertEqual(status, 400)
        self.assertEqual(resp_body, b"")

    def test_fixtures_return_empty_error_list(self):
        for name in ("sample-import.json", "extended-import.json"):
            with self.subTest(fixture=name):
                self.assert_errors_empty((FIXTURES / name).read_bytes())

    def test_valid_json_that_is_not_an_object_returns_empty_error_list(self):
        for body in (b"[]", b'"hello"'):
            with self.subTest(body=body):
                self.assert_errors_empty(body)

    def test_non_finite_numbers_reach_validation(self):
        for body in (b'{"x": NaN}', b'{"x": Infinity}', b'{"x": -Infinity}'):
            with self.subTest(body=body):
                self.assert_errors_empty(body)

    def test_malformed_json_returns_400(self):
        cases = {
            "truncated": b'{"images": [',
            "invalid UTF-8": b'{"a": "\xe9"}',
        }
        for name, body in cases.items():
            with self.subTest(case=name):
                self.assert_bodiless_400(body)

    def test_missing_content_length_returns_400(self):
        self.assert_bodiless_400()

    def test_invalid_content_length_returns_400(self):
        for value in ("abc", "-5"):
            with self.subTest(content_length=value):
                self.assert_bodiless_400(content_length=value)


if __name__ == "__main__":
    unittest.main()

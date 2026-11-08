import http.client
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from annotation_validator.server import make_server

SAMPLE = Path(__file__).parent / "fixtures" / "sample-import.json"


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.server = make_server("127.0.0.1", 0)
        host, port = self.server.server_address[:2]
        self.base = f"http://{host}:{port}"
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
        )
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path, method, body=None):
        req = urllib.request.Request(
            self.base + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status
        except urllib.error.HTTPError as err:
            return err.code

    def test_post_validate_annotations_returns_200(self):
        self.assertEqual(
            self.request("/validate-annotations", "POST", SAMPLE.read_bytes()), 200
        )

    def test_post_unknown_path_returns_404(self):
        self.assertEqual(self.request("/other", "POST", b"{}"), 404)

    def test_other_methods_on_validate_annotations_return_404(self):
        for method in ("GET", "HEAD", "PUT", "PATCH", "DELETE", "OPTIONS"):
            with self.subTest(method=method):
                self.assertEqual(self.request("/validate-annotations", method), 404)

    def test_invalid_content_length_returns_400(self):
        host, port = self.server.server_address[:2]
        for value in ("abc", "-5"):
            with self.subTest(content_length=value):
                conn = http.client.HTTPConnection(host, port, timeout=2)
                conn.putrequest("POST", "/validate-annotations")
                conn.putheader("Content-Length", value)
                conn.endheaders()
                self.assertEqual(conn.getresponse().status, 400)
                conn.close()


if __name__ == "__main__":
    unittest.main()

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

    def assert_bodiless_400(self, body=None, content_length=None):
        status, _, resp_body = self.post(body, content_length)
        self.assertEqual(status, 400)
        self.assertEqual(resp_body, b"")

    def test_sample_fixture_returns_its_errors(self):
        status, content_type, body = self.post((FIXTURES / "sample-import.json").read_bytes())
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(
            json.loads(body),
            {
                "errors": [
                    {
                        "code": "image_id_unknown",
                        "message": 'Annotation #3: image_id "frame-missing" does not match any image.',
                        "index": 2,
                    },
                    {
                        "code": "label_not_allowed",
                        "message": 'Annotation #4: label "unsupported-label" is not allowed. It must be '
                        'one of: "instrument", "grasper", "tissue", "organ", "reference_marker".',
                        "index": 3,
                    },
                    {
                        "code": "label_missing",
                        "message": "Annotation #5: label is missing. It must be a string.",
                        "index": 4,
                    },
                    {
                        "code": "box_x_negative",
                        "message": "Annotation #6: box.x must be 0 or greater, but it is -5.",
                        "index": 5,
                    },
                    {
                        "code": "box_width_not_positive",
                        "message": "Annotation #7: box.width must be greater than 0, but it is 0.",
                        "index": 6,
                    },
                    {
                        "code": "box_out_of_bounds",
                        "message": "Annotation #8: box (x 180, y 80, width 30, height 20) does not fit "
                        'inside image "frame-002" (width 200, height 100).',
                        "index": 7,
                    },
                    {
                        "code": "box_x_wrong_type",
                        "message": 'Annotation #9: box.x must be a number, but it is a string ("10").',
                        "index": 8,
                    },
                ]
            },
        )

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

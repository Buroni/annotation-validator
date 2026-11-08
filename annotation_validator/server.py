import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer

from annotation_validator.response import ValidationResponse
from annotation_validator.validate import validate

VALIDATE_PATH = "/validate-annotations"


def _reject_constant(name):
    raise ValueError(f"non-standard JSON constant: {name}")


def parse_strict_json(body):
    """Parse JSON bytes, rejecting NaN and Infinity; raise ValueError if malformed."""
    return json.loads(body, parse_constant=_reject_constant)


class Handler(BaseHTTPRequestHandler):
    def _read_body(self):
        """Return the request body, or None if Content-Length is invalid."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None
        if length < 0:
            return None
        return self.rfile.read(length)

    def _send_bad_request(self):
        self.send_response(400)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_json(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = self._read_body()
        if body is None:
            self._send_bad_request()
            return
        try:
            payload = parse_strict_json(body)
        except ValueError:
            self._send_bad_request()
            return
        response = ValidationResponse(errors=tuple(validate(payload)))
        self._send_json(json.dumps(asdict(response)).encode("ascii"))


def make_server(host="127.0.0.1", port=8000):
    return HTTPServer((host, port), Handler)


def main():
    server = make_server()
    host, port = server.server_address[:2]
    print(f"Listening on http://{host}:{port}{VALIDATE_PATH}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

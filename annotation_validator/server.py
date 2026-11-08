"""Stdlib HTTP server exposing POST /validate-annotations."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VALIDATE_PATH = "/validate-annotations"


class Handler(BaseHTTPRequestHandler):
    def _discard_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)

    def _send_status(self, status):
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        self._discard_body()
        self._send_status(200 if self.path == VALIDATE_PATH else 404)

    def _not_found(self):
        self._discard_body()
        self._send_status(404)

    do_GET = do_HEAD = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = _not_found


def make_server(host="127.0.0.1", port=8000):
    return ThreadingHTTPServer((host, port), Handler)


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

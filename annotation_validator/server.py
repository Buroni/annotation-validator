from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VALIDATE_PATH = "/validate-annotations"


class Handler(BaseHTTPRequestHandler):
    def _discard_body(self):
        """Read and drop the request body; return False if Content-Length is invalid."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return False
        if length < 0:
            return False
        if length:
            self.rfile.read(length)
        return True

    def _send_status(self, status):
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        if not self._discard_body():
            self._send_status(400)
        elif self.path == VALIDATE_PATH:
            self._send_status(200)
        else:
            self._send_status(404)

    def _not_found(self):
        self._send_status(404 if self._discard_body() else 400)

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

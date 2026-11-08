from http.server import BaseHTTPRequestHandler, HTTPServer

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
        self._send_status(200 if self._discard_body() else 400)


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

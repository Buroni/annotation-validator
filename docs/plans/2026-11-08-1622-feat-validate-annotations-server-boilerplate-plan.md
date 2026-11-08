---
title: "feat: /validate-annotations server boilerplate (stage 1)"
type: feat
date: 2026-11-08
execution: code
---

# feat: /validate-annotations server boilerplate (stage 1)

## Summary

Add a stdlib-only HTTP server with one route. `POST /validate-annotations` returns 200, and every other path or method returns 404. Stage 1 does not read or check the request body. The handler calls a placeholder `validate(payload)` function that returns no errors, so stage 2 only has to fill in that function.

## Implementation Units

### 1. Validation function

- **Files:** `annotation_validator/__init__.py`, `annotation_validator/validate.py`
- `validate(payload) -> list` returns `[]` for now and imports nothing from the HTTP layer.
- **Tests (`test/test_validate.py`):** load `test/fixtures/sample-import.json` and `test/fixtures/extended-import.json` with `json.load`, and check that `validate` returns a list. This sets up the fixture-loading pattern stage 2 will use.

### 2. HTTP server

- **Files:** `annotation_validator/server.py`
- A `BaseHTTPRequestHandler` subclass:
  - `do_POST` sends 200 when `self.path == "/validate-annotations"` and 404 otherwise.
  - `do_GET`, `do_PUT` and `do_DELETE` send 404, so other methods get a 404 instead of the default 501.
  - Reads and discards `Content-Length` bytes, so the connection is left clean.
- `make_server(host, port)` returns a `ThreadingHTTPServer`.
- `main()` starts it (`python -m annotation_validator.server`, port 8000 by default).
- **Tests (`test/test_server.py`):** use `unittest`. Call `make_server("127.0.0.1", 0)`, run `serve_forever` in a daemon thread, and call `shutdown()` and `server_close()` in teardown. Use `urllib.request` to check that:
  - a POST of the sample fixture to `/validate-annotations` returns 200;
  - a POST to `/other` returns 404;
  - a GET to `/validate-annotations` returns 404 (urllib raises `HTTPError`, so check its `.code`).

## Verification

Run `python3 -m unittest discover -s test` from the repo root.

## Decisions

- Use the standard library's `http.server` with `ThreadingHTTPServer` and `BaseHTTPRequestHandler`. The alternatives were `wsgiref` and plain `asyncio`; `http.server` was chosen as the smallest stdlib option that handles requests on threads.
- No external dependencies (Python 3.15 standard library only).
- Validation stays a pure function, separate from the HTTP handler, so it can be unit-tested against the fixtures without starting a server.

## Deferred to Stage 2

- The response for invalid files: a 200 with a list of errors, or a 4xx.
- The validation rules themselves: type checks; content checks such as an `image_id` that matches no image or a label not in `allowed_labels`; and bounds checks such as a box running past the image's width or height.

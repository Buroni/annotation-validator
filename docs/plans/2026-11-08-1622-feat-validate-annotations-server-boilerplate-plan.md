---
title: "feat: /validate-annotations server boilerplate (stage 1)"
type: feat
date: 2026-11-08
execution: code
---

# feat: /validate-annotations server boilerplate (stage 1)

## Summary

Add a stdlib-only HTTP server that accepts `POST /validate-annotations` and returns 200. Scope is kept minimal: the server does no routing, so a POST to any path returns 200, and other methods get `BaseHTTPRequestHandler`'s default 501. A malformed or negative `Content-Length` returns 400. Stage 1 does not inspect the request body. A placeholder `validate(payload)` function returns no errors and is not yet connected to the handler, so later stages only have to type its return value, fill it in and wire it up.

## Implementation Units

### 1. Validation function

- **Files:** `annotation_validator/__init__.py`, `annotation_validator/validate.py`
- `validate(payload) -> list` returns `[]` for now and imports nothing from the HTTP layer.
- **Tests (`test/test_validate.py`):** load `test/fixtures/sample-import.json` and `test/fixtures/extended-import.json` with `json.load`, and check that `validate` returns a list. This sets up the fixture-loading pattern the validation stage will use.

### 2. HTTP server

- **Files:** `annotation_validator/server.py`
- A `BaseHTTPRequestHandler` subclass:
  - `do_POST` reads and discards `Content-Length` bytes, so the connection is left clean, then sends 200.
  - A malformed or negative `Content-Length` gets a 400.
  - No other `do_<METHOD>` handlers, and no path routing.
- `make_server(host, port)` returns an `HTTPServer`.
- `main()` starts it (`python -m annotation_validator.server`, port 8000 by default).
- **Tests (`test/test_server.py`):** use `unittest`. Call `make_server("127.0.0.1", 0)`, run `serve_forever` in a daemon thread, and call `shutdown()` and `server_close()` in teardown. Use `urllib.request` to check that:
  - a POST of the sample fixture to `/validate-annotations` returns 200;
  - a POST with a `Content-Length` of `abc` or `-5` returns 400.

## Verification

Run `python3 -m unittest discover -s test` from the repo root.

## Decisions

- Use the standard library's `http.server` with `HTTPServer` and `BaseHTTPRequestHandler`. The alternatives were `wsgiref` and plain `asyncio`; `http.server` was chosen as the smallest stdlib option. Plain `HTTPServer` handles one request at a time, which is enough for a local prototype; `ThreadingHTTPServer` was used first and dropped to keep scope tight. A client that stalls mid-upload blocks the whole server until it finishes or disconnects. Switching back is a one-word change.
- No external dependencies (Python 3.15 standard library only).
- Validation stays a pure function, separate from the HTTP handler, so it can be unit-tested against the fixtures without starting a server.

## Later Stages

### Stage 2: typed response shape

- Define the response as types: a `ValidationError` (for example `annotation_id`, `field`, `code`, `message`) and a `ValidationResponse` (for example `valid: bool`, `errors: list[ValidationError]`).
- Type `validate()` to return `list[ValidationError]`; it can keep returning `[]`.
- Open choice: `TypedDict` (serializes straight through `json.dumps`) or frozen `dataclass` (needs `dataclasses.asdict()`).
- Out of scope: the request contract and status codes.

### Stage 3: validation rules

- Type checks; content checks such as an `image_id` that matches no image or a label not in `allowed_labels`; and bounds checks such as a box running past the image's width or height.

### Not yet assigned to a stage

- Routing: returning 404 for unknown paths and 404/405 for other methods. Both were built and then removed during stage 1 to keep scope tight.
- Returning 411 when a POST has no `Content-Length` (currently read as an empty body).
- The status code for invalid files: a 200 with a list of errors, or a 4xx.

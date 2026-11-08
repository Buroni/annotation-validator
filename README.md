# Annotation Validator

## Requirements
Python 3.10+. Standard library only; nothing to install.

## Run
```sh
python3 -m annotation_validator.server   # listens on http://127.0.0.1:8000
python3 -m unittest discover -s test     # tests
```

## Usage
```sh
curl -X POST http://127.0.0.1:8000/validate-annotations \
  -H 'Content-Type: application/json' \
  --data @test/fixtures/sample-import.json
```
Returns `200` with `{summary, errors, warnings}`, or `400` for malformed JSON. Rules are documented in `docs/data-rules.md`.

## AI Disclosure
Claude Opus 5.5 with the `compound-engineering` plugin was used to collaborate on planning, and implement all code in this repo.

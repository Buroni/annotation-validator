import dataclasses
import json
import unittest
from dataclasses import asdict

from annotation_validator.response import (
    ValidationError,
    ValidationResponse,
    ValidationSummary,
    ValidationWarning,
)

EMPTY_SUMMARY = ValidationSummary(total=0, valid=0, invalid=0, invalid_indices=())


class ResponseTest(unittest.TestCase):
    def test_response_serializes_summary_errors_and_warnings_in_order(self):
        response = ValidationResponse(
            summary=ValidationSummary(total=31, valid=30, invalid=1, invalid_indices=(30,)),
            errors=(
                ValidationError(code="example_code", message="Example message", index=30),
            ),
            warnings=(
                ValidationWarning(
                    code="example_warning", message="Example warning", image_id="frame-1"
                ),
            ),
        )
        body = json.dumps(asdict(response))
        self.assertEqual(list(json.loads(body)), ["summary", "errors", "warnings"])
        self.assertEqual(
            json.loads(body),
            {
                "summary": {"total": 31, "valid": 30, "invalid": 1, "invalid_indices": [30]},
                "errors": [{"code": "example_code", "message": "Example message", "index": 30}],
                "warnings": [
                    {"code": "example_warning", "message": "Example warning", "image_id": "frame-1"}
                ],
            },
        )

    def test_error_without_record_serializes_index_as_null(self):
        error = ValidationError(code="example_code", message="Example message", index=None)
        self.assertEqual(json.loads(json.dumps(asdict(error)))["index"], None)

    def test_empty_response_serializes_to_empty_lists(self):
        response = ValidationResponse(summary=EMPTY_SUMMARY, errors=(), warnings=())
        self.assertEqual(
            json.loads(json.dumps(asdict(response))),
            {
                "summary": {"total": 0, "valid": 0, "invalid": 0, "invalid_indices": []},
                "errors": [],
                "warnings": [],
            },
        )

    def test_error_requires_message_and_index(self):
        with self.assertRaises(TypeError):
            ValidationError(code="example_code")
        with self.assertRaises(TypeError):
            ValidationError(code="example_code", message="Example message")

    def test_error_is_frozen(self):
        error = ValidationError(code="example_code", message="Example message", index=0)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            error.message = "Changed"


if __name__ == "__main__":
    unittest.main()

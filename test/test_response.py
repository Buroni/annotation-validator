import dataclasses
import json
import unittest
from dataclasses import asdict

from annotation_validator.response import ValidationError, ValidationResponse


class ResponseTest(unittest.TestCase):
    def test_response_serializes_error_fields(self):
        response = ValidationResponse(
            errors=(
                ValidationError(code="example_code", message="Example message", index=30),
            )
        )
        self.assertEqual(
            json.loads(json.dumps(asdict(response))),
            {"errors": [{"code": "example_code", "message": "Example message", "index": 30}]},
        )

    def test_error_without_record_serializes_index_as_null(self):
        error = ValidationError(code="example_code", message="Example message", index=None)
        self.assertEqual(json.loads(json.dumps(asdict(error)))["index"], None)

    def test_empty_response_serializes_to_empty_list(self):
        self.assertEqual(json.dumps(asdict(ValidationResponse(errors=()))), '{"errors": []}')

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

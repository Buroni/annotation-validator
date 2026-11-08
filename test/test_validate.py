import json
import unittest
from pathlib import Path

from annotation_validator.response import ValidationSummary
from annotation_validator.validate import validate

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    with open(FIXTURES / name) as f:
        return json.load(f)


class ValidateTest(unittest.TestCase):
    def test_sample_fixture_errors(self):
        errors = validate(load_fixture("sample-import.json")).errors
        self.assertEqual(
            [(error.code, error.index) for error in errors],
            [
                ("image_id_unknown", 2),
                ("label_not_allowed", 3),
                ("label_missing", 4),
                ("box_x_negative", 5),
                ("box_width_not_positive", 6),
                ("box_out_of_bounds", 7),
                ("box_x_wrong_type", 8),
            ],
        )

    def test_extended_fixture_flags_each_broken_record(self):
        errors = validate(load_fixture("extended-import.json")).errors
        indices = [error.index for error in errors]
        type_error_indices = {29, 31, 32, 34, 35, 37, 38, *range(40, 49), *range(58, 63)}
        content_error_indices = {30, 33, 36, 39, *range(49, 58)}
        self.assertEqual(set(indices), type_error_indices | content_error_indices)
        self.assertEqual(indices, sorted(indices))

    def test_extended_fixture_content_errors(self):
        errors = validate(load_fixture("extended-import.json")).errors
        type_suffixes = ("_missing", "_wrong_type", "annotation_not_object")
        self.assertEqual(
            [(error.code, error.index) for error in errors if not error.code.endswith(type_suffixes)],
            [
                ("id_empty", 30),
                ("image_id_unknown", 33),
                ("label_not_allowed", 36),
                ("label_not_allowed", 39),
                ("box_x_negative", 49),
                ("box_y_negative", 50),
                ("box_width_not_positive", 51),
                ("box_height_not_positive", 52),
                ("box_width_not_positive", 53),
                ("box_height_not_positive", 54),
                ("box_out_of_bounds", 55),
                ("box_out_of_bounds", 56),
                ("box_x_negative", 57),
            ],
        )
    def test_sample_fixture_summary(self):
        self.assertEqual(
            validate(load_fixture("sample-import.json")).summary,
            ValidationSummary(total=13, valid=6, invalid=7, invalid_indices=(2, 3, 4, 5, 6, 7, 8)),
        )

    def test_extended_fixture_summary_counts_each_invalid_record_once(self):
        self.assertEqual(
            validate(load_fixture("extended-import.json")).summary,
            ValidationSummary(
                total=64, valid=30, invalid=34, invalid_indices=tuple(range(29, 63))
            ),
        )


if __name__ == "__main__":
    unittest.main()

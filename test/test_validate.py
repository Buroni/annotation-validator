import json
import unittest
from pathlib import Path

from annotation_validator.validate import validate

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    with open(FIXTURES / name) as f:
        return json.load(f)


class ValidateTest(unittest.TestCase):
    def test_sample_fixture_errors(self):
        errors = validate(load_fixture("sample-import.json"))
        self.assertEqual(
            [(error.code, error.index) for error in errors],
            [("label_missing", 4), ("box_x_wrong_type", 8)],
        )

    def test_extended_fixture_flags_each_structurally_broken_record(self):
        errors = validate(load_fixture("extended-import.json"))
        indices = [error.index for error in errors]
        self.assertEqual(
            set(indices),
            {29, 31, 32, 34, 35, 37, 38, 40, 41, 42, 43, 44, 45, 46, 47, 48, 58, 59, 60, 61, 62},
        )
        self.assertEqual(indices.count(62), 4)
        self.assertEqual(indices, sorted(indices))


if __name__ == "__main__":
    unittest.main()

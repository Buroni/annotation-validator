import json
import unittest
from pathlib import Path

from annotation_validator.validate import validate

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    with open(FIXTURES / name) as f:
        return json.load(f)


class ValidateTest(unittest.TestCase):
    def test_returns_list_for_each_fixture(self):
        for name in ("sample-import.json", "extended-import.json"):
            with self.subTest(fixture=name):
                self.assertIsInstance(validate(load_fixture(name)), list)


if __name__ == "__main__":
    unittest.main()

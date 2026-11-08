import unittest

from annotation_validator.response import ValidationError
from annotation_validator.type_rules import check_annotation_types


def build_annotation(**overrides):
    annotation = {
        "id": "ann-1",
        "image_id": "img-1",
        "label": "car",
        "box": {"x": 10, "y": 20, "width": 30.5, "height": 40},
    }
    annotation.update(overrides)
    return annotation


def build_box(**overrides):
    box = {"x": 10, "y": 20, "width": 30, "height": 40}
    box.update(overrides)
    return box


def codes(errors):
    return [error.code for error in errors]


class CheckAnnotationTypesTest(unittest.TestCase):
    def test_valid_annotation_has_no_errors(self):
        self.assertEqual(check_annotation_types(build_annotation(), 0), [])

    def test_boolean_box_field_is_wrong_type(self):
        annotation = build_annotation(box=build_box(x=True))
        self.assertEqual(
            check_annotation_types(annotation, 47),
            [
                ValidationError(
                    code="box_x_wrong_type",
                    message="Annotation #48: box.x must be a number, but it is a boolean (true).",
                    index=47,
                )
            ],
        )

    def test_empty_annotation_reports_each_missing_field_once(self):
        errors = check_annotation_types({}, 62)
        self.assertEqual(
            codes(errors), ["id_missing", "image_id_missing", "label_missing", "box_missing"]
        )
        self.assertEqual({error.index for error in errors}, {62})
        self.assertEqual(errors[2].message, "Annotation #63: label is missing. It must be a string.")

    def test_array_box_gives_one_error(self):
        errors = check_annotation_types(build_annotation(box=[10, 10, 20, 20]), 42)
        self.assertEqual(codes(errors), ["box_wrong_type"])
        self.assertEqual(
            errors[0].message,
            "Annotation #43: box must be an object, but it is an array ([10, 10, 20, 20]).",
        )

    def test_non_object_annotation_gives_one_error(self):
        cases = {
            "null": (None, "Annotation #59 must be an object, but it is null."),
            "string": (
                "not-an-annotation-object",
                'Annotation #59 must be an object, but it is a string ("not-an-annotation-object").',
            ),
            "array": (["a", 1], 'Annotation #59 must be an object, but it is an array (["a", 1]).'),
        }
        for name, (annotation, message) in cases.items():
            with self.subTest(case=name):
                self.assertEqual(
                    check_annotation_types(annotation, 58),
                    [ValidationError(code="annotation_not_object", message=message, index=58)],
                )

    def test_null_field_is_wrong_type_not_missing(self):
        errors = check_annotation_types(build_annotation(label=None), 37)
        self.assertEqual(
            errors,
            [
                ValidationError(
                    code="label_wrong_type",
                    message="Annotation #38: label must be a string, but it is null.",
                    index=37,
                )
            ],
        )

    def test_number_id_is_wrong_type(self):
        errors = check_annotation_types(build_annotation(id=33), 0)
        self.assertEqual(codes(errors), ["id_wrong_type"])
        self.assertEqual(
            errors[0].message, "Annotation #1: id must be a string, but it is a number (33)."
        )

    def test_numeric_string_box_field_is_wrong_type(self):
        errors = check_annotation_types(build_annotation(box=build_box(x="10")), 8)
        self.assertEqual(codes(errors), ["box_x_wrong_type"])
        self.assertEqual(
            errors[0].message, 'Annotation #9: box.x must be a number, but it is a string ("10").'
        )

    def test_missing_box_field(self):
        box = build_box()
        del box["x"]
        errors = check_annotation_types(build_annotation(box=box), 0)
        self.assertEqual(codes(errors), ["box_x_missing"])
        self.assertEqual(
            errors[0].message, "Annotation #1: box.x is missing. It must be a number."
        )

    def test_several_problems_reported_in_field_order(self):
        annotation = build_annotation(box=build_box(height=False))
        del annotation["id"]
        self.assertEqual(
            codes(check_annotation_types(annotation, 0)), ["id_missing", "box_height_wrong_type"]
        )


if __name__ == "__main__":
    unittest.main()

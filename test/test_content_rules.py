import unittest

from annotation_validator.content_rules import Lookups, build_lookups, check_annotation_content
from annotation_validator.response import ValidationError

IMAGES = {"img-1": {"id": "img-1", "width": 1280, "height": 720}}


def build_annotation(**overrides):
    annotation = {
        "id": "ann-1",
        "image_id": "img-1",
        "label": "car",
        "box": {"x": 10, "y": 20, "width": 30, "height": 40},
    }
    annotation.update(overrides)
    return annotation


def build_box(**overrides):
    box = {"x": 10, "y": 20, "width": 30, "height": 40}
    box.update(overrides)
    return box


def check(annotation, index=0, failed_fields=frozenset(), lookups=None):
    """Check one annotation; by default its id is unique, img-1 is 1280x720 and
    "car" and "person" are allowed."""
    if lookups is None:
        lookups = Lookups(
            images=IMAGES, allowed_labels=["car", "person"], id_positions={"ann-1": [index]}
        )
    return check_annotation_content(annotation, index, failed_fields, lookups)


def codes(errors):
    return [error.code for error in errors]


class CheckAnnotationContentTest(unittest.TestCase):
    def test_valid_annotation_has_no_errors(self):
        self.assertEqual(check(build_annotation()), [])

    def test_duplicate_and_empty_ids(self):
        annotations = [build_annotation(id=f"ann-{n}") for n in range(22)]
        for index in (3, 7, 12):
            annotations[index]["id"] = "ann-7"
        annotations[20]["id"] = ""
        annotations[21]["id"] = ""
        lookups = build_lookups(
            {"images": list(IMAGES.values()), "allowed_labels": ["car"], "annotations": annotations}
        )
        expected_others = {3: "#8 and #13", 7: "#4 and #13", 12: "#4 and #8"}
        for index, others in expected_others.items():
            with self.subTest(index=index):
                self.assertEqual(
                    check(annotations[index], index, lookups=lookups),
                    [
                        ValidationError(
                            code="id_duplicate",
                            message=f'Annotation #{index + 1}: id "ann-7" is also used by '
                            f"annotations {others}. Each id must be unique.",
                            index=index,
                        )
                    ],
                )
        for index in (20, 21):
            with self.subTest(index=index):
                self.assertEqual(
                    check(annotations[index], index, lookups=lookups),
                    [
                        ValidationError(
                            code="id_empty",
                            message=f"Annotation #{index + 1}: id must not be empty.",
                            index=index,
                        )
                    ],
                )

    def test_duplicate_pair_names_the_single_other_position(self):
        lookups = Lookups(images=IMAGES, allowed_labels=["car"], id_positions={"ann-1": [0, 5]})
        errors = check(build_annotation(), 5, lookups=lookups)
        self.assertEqual(
            errors[0].message,
            'Annotation #6: id "ann-1" is also used by annotation #1. Each id must be unique.',
        )

    def test_duplicate_names_three_or_more_others(self):
        lookups = Lookups(
            images=IMAGES, allowed_labels=["car"], id_positions={"ann-1": [0, 3, 7, 19]}
        )
        errors = check(build_annotation(), 0, lookups=lookups)
        self.assertEqual(
            errors[0].message,
            'Annotation #1: id "ann-1" is also used by annotations #4, #8 and #20. '
            "Each id must be unique.",
        )

    def test_box_outside_image_gives_one_error(self):
        annotation = build_annotation(box=build_box(x=1200, y=10, width=100, height=50))
        self.assertEqual(
            check(annotation, 7),
            [
                ValidationError(
                    code="box_out_of_bounds",
                    message='Annotation #8: box (x 1200, y 10, width 100, height 50) does not fit '
                    'inside image "img-1" (width 1280, height 720).',
                    index=7,
                )
            ],
        )

    def test_box_touching_the_edge_fits(self):
        cases = {
            "right edge": build_box(x=1180, width=100),
            "bottom edge": build_box(y=620, height=100),
        }
        for name, box in cases.items():
            with self.subTest(case=name):
                self.assertEqual(check(build_annotation(box=box)), [])

    def test_unknown_image_skips_fit_check(self):
        annotation = build_annotation(image_id="frame-missing", box=build_box(x=5000))
        errors = check(annotation, 2)
        self.assertEqual(
            errors,
            [
                ValidationError(
                    code="image_id_unknown",
                    message='Annotation #3: image_id "frame-missing" does not match any image.',
                    index=2,
                )
            ],
        )

    def test_failed_type_field_is_skipped_and_others_still_checked(self):
        annotation = build_annotation(label=None, box=build_box(width=-5))
        self.assertEqual(
            check(annotation, 6, failed_fields=frozenset({"label"})),
            [
                ValidationError(
                    code="box_width_not_positive",
                    message="Annotation #7: box.width must be greater than 0, but it is -5.",
                    index=6,
                )
            ],
        )

    def test_non_finite_box_numbers(self):
        annotation = build_annotation(box=build_box(x=float("nan"), height=float("inf")))
        errors = check(annotation, 5)
        self.assertEqual(codes(errors), ["box_x_not_finite", "box_height_not_finite"])
        self.assertEqual(
            errors[0].message, "Annotation #6: box.x must be a finite number, but it is NaN."
        )
        self.assertEqual(
            errors[1].message,
            "Annotation #6: box.height must be a finite number, but it is Infinity.",
        )

    def test_negative_infinity_is_not_finite_rather_than_negative(self):
        annotation = build_annotation(box=build_box(x=float("-inf")))
        self.assertEqual(codes(check(annotation)), ["box_x_not_finite"])

    def test_huge_integer_box_number_is_finite(self):
        huge = 10**400
        annotation = build_annotation(box=build_box(x=huge))
        self.assertEqual(codes(check(annotation)), ["box_out_of_bounds"])

    def test_label_must_match_exactly(self):
        self.assertEqual(
            check(build_annotation(label="Car"), 3),
            [
                ValidationError(
                    code="label_not_allowed",
                    message='Annotation #4: label "Car" is not allowed. '
                    'It must be one of: "car", "person".',
                    index=3,
                )
            ],
        )

    def test_negative_and_zero_box_numbers(self):
        cases = {
            "y -1": (build_box(y=-1), "box_y_negative", "box.y must be 0 or greater, but it is -1."),
            "height 0": (
                build_box(height=0),
                "box_height_not_positive",
                "box.height must be greater than 0, but it is 0.",
            ),
        }
        for name, (box, code, message) in cases.items():
            with self.subTest(case=name):
                self.assertEqual(
                    check(build_annotation(box=box)),
                    [ValidationError(code=code, message=f"Annotation #1: {message}", index=0)],
                )

    def test_several_problems_reported_in_field_order(self):
        annotation = build_annotation(image_id="frame-missing", box=build_box(width=0))
        self.assertEqual(codes(check(annotation)), ["image_id_unknown", "box_width_not_positive"])


if __name__ == "__main__":
    unittest.main()

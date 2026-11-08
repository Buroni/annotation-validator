import unittest

from annotation_validator.qa_rules import check_label_subsets
from annotation_validator.response import ValidationWarning

SUBSETS = [["instrument", "grasper"], ["tissue", "organ"]]


def build_payload(frames, label_subsets=SUBSETS):
    """Build a payload from {frame id: [label, ...]}; annotations follow frame order."""
    images = [{"id": frame, "width": 100, "height": 100} for frame in frames]
    annotations = [
        {"id": f"ann-{n}", "image_id": frame, "label": label}
        for n, (frame, label) in enumerate(
            (frame, label) for frame, labels in frames.items() for label in labels
        )
    ]
    return {"images": images, "label_subsets": label_subsets, "annotations": annotations}


def check(frames, invalid=frozenset(), label_subsets=SUBSETS):
    return check_label_subsets(build_payload(frames, label_subsets), invalid)


class CheckLabelSubsetsTest(unittest.TestCase):
    def test_labels_from_two_subsets_give_one_warning(self):
        self.assertEqual(
            check({"frame-1": ["instrument", "tissue"]}),
            [
                ValidationWarning(
                    code="label_subsets_conflict",
                    message='Frame "frame-1" has labels from 2 subsets that should not appear '
                    'together: "instrument" (subset ["instrument", "grasper"]) and "tissue" '
                    '(subset ["tissue", "organ"]).',
                    image_id="frame-1",
                )
            ],
        )

    def test_frames_without_a_conflict_give_no_warning(self):
        cases = {
            "same subset": ["instrument", "grasper"],
            "incomplete subset": ["instrument"],
            "label in no subset": ["reference_marker"],
            "no labels": [],
        }
        for name, labels in cases.items():
            with self.subTest(case=name):
                self.assertEqual(check({"frame-1": labels}), [])

    def test_invalid_annotations_are_ignored(self):
        self.assertEqual(check({"frame-1": ["instrument", "tissue", "grasper"]}, invalid={1}), [])

    def test_three_subsets_give_one_warning_naming_all_three(self):
        subsets = SUBSETS + [["cautery", "clip"]]
        warnings = check({"frame-1": ["clip", "tissue", "instrument"]}, label_subsets=subsets)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(
            warnings[0].message,
            'Frame "frame-1" has labels from 3 subsets that should not appear together: '
            '"instrument" (subset ["instrument", "grasper"]), "tissue" (subset ["tissue", '
            '"organ"]) and "clip" (subset ["cautery", "clip"]).',
        )

    def test_empty_label_subsets_turns_the_check_off(self):
        self.assertEqual(check({"frame-1": ["instrument", "tissue"]}, label_subsets=[]), [])

    def test_repeated_labels_are_listed_once_in_subset_order(self):
        warnings = check({"frame-1": ["grasper", "instrument", "instrument", "tissue"]})
        self.assertIn(
            '"instrument", "grasper" (subset ["instrument", "grasper"]) and "tissue"',
            warnings[0].message,
        )

    def test_each_frame_is_checked_on_its_own(self):
        self.assertEqual(check({"frame-1": ["instrument"], "frame-2": ["tissue"]}), [])

    def test_conflicting_frames_are_reported_in_images_order(self):
        warnings = check(
            {
                "frame-b": ["organ", "grasper"],
                "frame-ok": ["instrument"],
                "frame-a": ["tissue", "instrument"],
            }
        )
        self.assertEqual([warning.image_id for warning in warnings], ["frame-b", "frame-a"])


if __name__ == "__main__":
    unittest.main()

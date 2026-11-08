from annotation_validator.content_rules import show
from annotation_validator.response import ValidationWarning


def check_label_subsets(payload, invalid_indices) -> list[ValidationWarning]:
    """Return one warning (rule Q1 in docs/data-rules.md) per frame whose valid
    annotations have labels from two or more label subsets."""
    labels_by_frame = {}
    for index, annotation in enumerate(payload["annotations"]):
        if index not in invalid_indices:
            labels_by_frame.setdefault(annotation["image_id"], set()).add(annotation["label"])

    warnings = []
    for image in payload["images"]:
        labels = labels_by_frame.get(image["id"], set())
        present = [subset for subset in payload["label_subsets"] if labels.intersection(subset)]
        if len(present) < 2:
            continue
        parts = [
            f"{', '.join(show(label) for label in subset if label in labels)} "
            f"(subset {show(subset)})"
            for subset in present
        ]
        warnings.append(
            ValidationWarning(
                code="label_subsets_conflict",
                message=f"Frame {show(image['id'])} has labels from {len(present)} subsets "
                f"that should not appear together: {join_with_and(parts)}.",
                image_id=image["id"],
            )
        )
    return warnings


def join_with_and(parts) -> str:
    """Join parts as 'a and b' or 'a, b and c'."""
    return f"{', '.join(parts[:-1])} and {parts[-1]}"

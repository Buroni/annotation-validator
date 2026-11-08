import json
import math
from dataclasses import dataclass

from annotation_validator.response import ValidationError
from annotation_validator.type_rules import BOX_FIELDS


@dataclass(frozen=True)
class Lookups:
    """Request-wide data the content rules check annotations against."""

    images: dict[str, dict]
    allowed_labels: list[str]
    id_positions: dict[str, list[int]]


def build_lookups(payload) -> Lookups:
    id_positions = {}
    for index, annotation in enumerate(payload["annotations"]):
        if isinstance(annotation, dict):
            annotation_id = annotation.get("id")
            if isinstance(annotation_id, str) and annotation_id != "":
                id_positions.setdefault(annotation_id, []).append(index)
    return Lookups(
        images={image["id"]: image for image in payload["images"]},
        allowed_labels=payload["allowed_labels"],
        id_positions=id_positions,
    )


def check_annotation_content(annotation, index, failed_fields, lookups) -> list[ValidationError]:
    """Return every content error (rules C1-C7 in docs/data-rules.md) for one object
    annotation, skipping fields listed in failed_fields."""
    position = index + 1

    def error(code, message):
        return ValidationError(code=code, message=f"Annotation #{position}: {message}", index=index)

    errors = []

    if "id" not in failed_fields:
        annotation_id = annotation["id"]
        if annotation_id == "":
            errors.append(error("id_empty", "id must not be empty."))
        else:
            others = [p for p in lookups.id_positions[annotation_id] if p != index]
            if others:
                errors.append(
                    error(
                        "id_duplicate",
                        f"id {show(annotation_id)} is also used by {name_positions(others)}. "
                        "Each id must be unique.",
                    )
                )

    image = None
    if "image_id" not in failed_fields:
        image = lookups.images.get(annotation["image_id"])
        if image is None:
            errors.append(
                error(
                    "image_id_unknown",
                    f"image_id {show(annotation['image_id'])} does not match any image.",
                )
            )

    if "label" not in failed_fields and annotation["label"] not in lookups.allowed_labels:
        allowed = ", ".join(show(label) for label in lookups.allowed_labels)
        errors.append(
            error(
                "label_not_allowed",
                f"label {show(annotation['label'])} is not allowed. It must be one of: {allowed}.",
            )
        )

    box_is_valid = "box" not in failed_fields
    if box_is_valid:
        for key in BOX_FIELDS:
            if f"box.{key}" in failed_fields:
                box_is_valid = False
                continue
            box_error = check_box_number(key, annotation["box"][key])
            if box_error:
                errors.append(error(*box_error))
                box_is_valid = False

    if box_is_valid and image is not None:
        box = annotation["box"]
        if box["x"] + box["width"] > image["width"] or box["y"] + box["height"] > image["height"]:
            errors.append(
                error(
                    "box_out_of_bounds",
                    f"box (x {show(box['x'])}, y {show(box['y'])}, width {show(box['width'])}, "
                    f"height {show(box['height'])}) does not fit inside image "
                    f"{show(annotation['image_id'])} (width {show(image['width'])}, "
                    f"height {show(image['height'])}).",
                )
            )

    return errors


def check_box_number(key, value):
    """Return (code, message) when a box number breaks C2/C3, else None."""
    name = f"box.{key}"
    if not math.isfinite(value):
        return f"box_{key}_not_finite", f"{name} must be a finite number, but it is {show(value)}."
    if key in ("x", "y") and value < 0:
        return f"box_{key}_negative", f"{name} must be 0 or greater, but it is {show(value)}."
    if key in ("width", "height") and value <= 0:
        return f"box_{key}_not_positive", f"{name} must be greater than 0, but it is {show(value)}."
    return None


def name_positions(indices) -> str:
    """Name 0-based indices as 1-based positions, e.g. 'annotations #8 and #13'."""
    names = [f"#{index + 1}" for index in indices]
    if len(names) == 1:
        return f"annotation {names[0]}"
    return f"annotations {', '.join(names[:-1])} and {names[-1]}"


def show(value) -> str:
    return json.dumps(value, ensure_ascii=False)

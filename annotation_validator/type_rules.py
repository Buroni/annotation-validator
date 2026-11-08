import json

from annotation_validator.response import ValidationError

BOX_FIELDS = ("x", "y", "width", "height")


def check_annotation_types(annotation, index) -> list[ValidationError]:
    """Return every type error (rules T1-T6 in docs/data-rules.md) for one annotation."""
    if not isinstance(annotation, dict):
        return [
            ValidationError(
                code="annotation_not_object",
                message=f"Annotation #{index + 1} must be an object, but it is {describe(annotation)}.",
                index=index,
            )
        ]

    errors = []
    errors += check_field(annotation, "id", "string", index, "id")
    errors += check_field(annotation, "image_id", "string", index, "image_id")
    errors += check_field(annotation, "label", "string", index, "label")
    box_errors = check_field(annotation, "box", "object", index, "box")
    errors += box_errors
    if "box" in annotation and not box_errors:
        for key in BOX_FIELDS:
            errors += check_field(annotation["box"], key, "number", index, f"box.{key}")
    return errors


def check_field(container, key, expected, index, name) -> list[ValidationError]:
    code = name.replace(".", "_")
    position = index + 1
    if key not in container:
        return [
            ValidationError(
                code=f"{code}_missing",
                message=f"Annotation #{position}: {name} is missing. It must be {with_article(expected)}.",
                index=index,
            )
        ]
    value = container[key]
    if json_type(value) != expected:
        return [
            ValidationError(
                code=f"{code}_wrong_type",
                message=f"Annotation #{position}: {name} must be {with_article(expected)}, "
                f"but it is {describe(value)}.",
                index=index,
            )
        ]
    return []


def json_type(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def describe(value) -> str:
    """Name a value's JSON type and show it in full, e.g. 'a boolean (true)'."""
    if value is None:
        return "null"
    return f"{with_article(json_type(value))} ({json.dumps(value, ensure_ascii=False)})"


def with_article(type_name) -> str:
    article = "an" if type_name[0] in "aeiou" else "a"
    return f"{article} {type_name}"

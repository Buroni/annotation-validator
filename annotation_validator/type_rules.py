import json
from dataclasses import dataclass

from annotation_validator.response import ValidationError

BOX_FIELDS = ("x", "y", "width", "height")


@dataclass(frozen=True)
class TypeCheckResult:
    errors: list[ValidationError]
    failed_fields: frozenset[str]


def check_annotation_types(annotation, index) -> TypeCheckResult:
    """Return every type error (rules T1-T6 in docs/data-rules.md) for one annotation,
    and the names of the fields that failed, e.g. "label" or "box.x"."""
    if not isinstance(annotation, dict):
        error = ValidationError(
            code="annotation_not_object",
            message=f"Annotation #{index + 1} must be an object, but it is {describe(annotation)}.",
            index=index,
        )
        return TypeCheckResult(errors=[error], failed_fields=frozenset())

    errors = []
    failed = set()

    def check(container, key, expected, name):
        field_errors = check_field(container, key, expected, index, name)
        if field_errors:
            errors.extend(field_errors)
            failed.add(name)

    check(annotation, "id", "string", "id")
    check(annotation, "image_id", "string", "image_id")
    check(annotation, "label", "string", "label")
    check(annotation, "box", "object", "box")
    if "box" not in failed:
        for key in BOX_FIELDS:
            check(annotation["box"], key, "number", f"box.{key}")
    return TypeCheckResult(errors=errors, failed_fields=frozenset(failed))


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

from annotation_validator.content_rules import build_lookups, check_annotation_content
from annotation_validator.response import ValidationError
from annotation_validator.type_rules import check_annotation_types


def validate(payload) -> list[ValidationError]:
    """Return a list of validation errors for an import payload."""
    lookups = build_lookups(payload)
    errors = []
    for index, annotation in enumerate(payload["annotations"]):
        type_result = check_annotation_types(annotation, index)
        errors += type_result.errors
        if isinstance(annotation, dict):
            errors += check_annotation_content(
                annotation, index, type_result.failed_fields, lookups
            )
    return errors

from annotation_validator.response import ValidationError
from annotation_validator.type_rules import check_annotation_types


def validate(payload) -> list[ValidationError]:
    """Return a list of validation errors for an import payload."""
    errors = []
    for index, annotation in enumerate(payload["annotations"]):
        errors += check_annotation_types(annotation, index).errors
    return errors

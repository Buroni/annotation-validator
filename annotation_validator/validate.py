from annotation_validator.response import ValidationError


def validate(payload) -> list[ValidationError]:
    """Return a list of validation errors for an import payload."""
    return []

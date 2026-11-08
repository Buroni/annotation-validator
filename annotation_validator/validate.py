from annotation_validator.content_rules import build_lookups, check_annotation_content
from annotation_validator.response import ValidationResponse, ValidationSummary
from annotation_validator.type_rules import check_annotation_types


def validate(payload) -> ValidationResponse:
    """Return the validation report for an import payload."""
    lookups = build_lookups(payload)
    errors = []
    for index, annotation in enumerate(payload["annotations"]):
        type_result = check_annotation_types(annotation, index)
        errors += type_result.errors
        if isinstance(annotation, dict):
            errors += check_annotation_content(
                annotation, index, type_result.failed_fields, lookups
            )

    invalid_indices = tuple(sorted({error.index for error in errors}))
    total = len(payload["annotations"])
    summary = ValidationSummary(
        total=total,
        valid=total - len(invalid_indices),
        invalid=len(invalid_indices),
        invalid_indices=invalid_indices,
    )
    return ValidationResponse(summary=summary, errors=tuple(errors), warnings=())

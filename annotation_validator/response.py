from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str
    index: int | None


@dataclass(frozen=True)
class ValidationWarning:
    code: str
    message: str
    image_id: str


@dataclass(frozen=True)
class ValidationSummary:
    total: int
    valid: int
    invalid: int
    invalid_indices: tuple[int, ...]


@dataclass(frozen=True)
class ValidationResponse:
    summary: ValidationSummary
    errors: tuple[ValidationError, ...]
    warnings: tuple[ValidationWarning, ...]

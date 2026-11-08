from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResponse:
    errors: tuple[ValidationError, ...]

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str
    index: int | None


@dataclass(frozen=True)
class ValidationResponse:
    errors: tuple[ValidationError, ...]

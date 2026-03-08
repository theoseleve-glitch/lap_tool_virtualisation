from dataclasses import dataclass


@dataclass
class DomainError(Exception):
    code: str
    message: str
    details: dict | None = None


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class ValidationError(DomainError):
    pass

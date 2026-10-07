"""Domain exceptions for AgentPulse."""


class AgentPulseError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, code: str = "internal_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(AgentPulseError):
    """Resource not found."""

    def __init__(self, message: str, code: str = "not_found") -> None:
        super().__init__(message, code)


class AuthenticationError(AgentPulseError):
    """Authentication failed or credentials missing/invalid."""

    def __init__(self, message: str, code: str = "unauthenticated") -> None:
        super().__init__(message, code)


class AuthorizationError(AgentPulseError):
    """Operation forbidden for the actor's permissions."""

    def __init__(self, message: str, code: str = "forbidden") -> None:
        super().__init__(message, code)


class ValidationError(AgentPulseError):
    """Input validation failure at domain level."""

    def __init__(self, message: str, code: str = "validation_error") -> None:
        super().__init__(message, code)

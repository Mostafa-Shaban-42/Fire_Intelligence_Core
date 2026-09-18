class IncidentDomainException(Exception):
    """Base exception for Incident Domain operations."""
    pass

class InvalidStateTransitionError(IncidentDomainException):
    """Raised when an invalid state machine transition is attempted."""
    pass

class IncidentNotFoundError(IncidentDomainException):
    """Raised when an incident is not found."""
    pass
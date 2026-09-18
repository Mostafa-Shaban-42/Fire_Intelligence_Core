class FireIntelException(Exception):
    """Base exception class for Fire Intelligence Platform errors."""
    pass


class InvalidStateTransitionError(FireIntelException):
    """Raised when an illegal incident state machine transition is attempted."""
    pass


class CameraNotFoundError(FireIntelException):
    """Raised when a requested camera ID does not exist in the active registry."""
    pass


class AuthenticationError(FireIntelException):
    """Raised when API Key authentication fails or authorization headers are missing."""
    pass


class SensorDataInvalidError(FireIntelException):
    """Raised when incoming IoT sensor telemetry fails schema validation."""
    pass
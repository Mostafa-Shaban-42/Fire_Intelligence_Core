class AlertException(Exception):
    """Base exception for Alerts."""
    pass

class DeliveryFailedException(AlertException):
    """Raised when channel delivery permanently fails."""
    pass

class RateLimitExceededException(AlertException):
    """Raised when an alert exceeds throttling limits."""
    pass
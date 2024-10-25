class NotEnoughSourcesException(Exception):
    """Exception raised when there are not enough sources for a summary."""

    def __init__(self, message: str):
        super().__init__(message)

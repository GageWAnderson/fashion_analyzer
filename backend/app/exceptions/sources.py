from pydantic import BaseModel


class NotEnoughSourcesException(BaseModel, Exception):
    """Exception raised when there are not enough sources for a summary."""

    message: str = "Not enough sources found"

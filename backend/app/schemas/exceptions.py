from typing import Any


class UserFriendlyException(Exception):
    """
    A wrapper exception class for displaying user-friendly error messages.
    """

    def __init__(self, message: str, original_exception: Exception = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)

    def __repr__(self) -> str:
        return self.message

    def __str__(self) -> str:
        return self.message

    @classmethod
    def from_exception(
        cls, exception: Exception, user_message: str
    ) -> "UserFriendlyException":
        """
        Create a UserFriendlyException from an existing exception with a custom user message.
        """
        return cls(message=user_message, original_exception=exception)

    def get_original_exception(self) -> Any:
        """
        Retrieve the original exception if it exists.
        """
        return self.original_exception

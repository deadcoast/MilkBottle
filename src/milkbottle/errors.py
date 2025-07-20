"""MilkBottle exception hierarchy."""


class MilkBottleError(Exception):
    """
    Base exception for all MilkBottle errors.
    """


class UserAbort(MilkBottleError):
    """
    Raised when the user aborts an operation intentionally.
    """


class BottleNotFound(MilkBottleError):
    """
    Raised when a requested bottle is not found in the registry.
    """

    def __init__(self, alias: str) -> None:
        super().__init__(f"Bottle not found: {alias}")
        self.alias = alias


class PluginError(MilkBottleError):
    """
    Raised when there's an error with plugin operations.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ValidationError(MilkBottleError):
    """
    Raised when validation fails for configuration or data.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)

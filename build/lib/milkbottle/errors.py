class MilkBottleError(Exception):
    """
    Base exception for all MilkBottle errors.
    """

    pass


class UserAbort(MilkBottleError):
    """
    Raised when the user aborts an operation intentionally.
    """

    pass


class BottleNotFound(MilkBottleError):
    """
    Raised when a requested bottle is not found in the registry.
    """

    def __init__(self, alias: str) -> None:
        super().__init__(f"Bottle not found: {alias}")
        self.alias = alias

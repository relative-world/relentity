class InvalidEventNameError(Exception):
    """
    Exception raised for invalid event names.
    """

    pass


class InvalidEventPatternError(Exception):
    """
    Exception raised for invalid event patterns.
    """

    pass


class UnknownEntityError(Exception):
    pass


class UnknownComponentError(Exception):
    pass

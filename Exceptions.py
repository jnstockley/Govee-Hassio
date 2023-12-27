class UnauthorizedException(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidDeviceException(Exception):
    def __init__(self, message):
        super().__init__(message)

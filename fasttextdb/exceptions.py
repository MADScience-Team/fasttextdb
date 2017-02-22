__all__ = [
    'WebException', 'NotFoundException', 'BadRequestException',
    'UnauthorizedException', 'ForbiddenException'
]


class WebException(Exception):
    def __init__(self, message, status, status_name):
        super(WebException, self).__init__(message)
        self.message = message
        self.status = status
        self.status_name = status_name


class NotFoundException(WebException):
    def __init__(self, message):
        super(NotFoundException, self).__init__(message, 404, 'Not Found')


class BadRequestException(WebException):
    def __init__(self, message):
        super(NotFoundException, self).__init__(message, 400, 'Bad Request')


class UnauthorizedException(WebException):
    def __init__(self, message):
        super(UnauthorizedException, self).__init__(message, 401,
                                                    'Unauthorized')


class ForbiddenException(WebException):
    def __init__(self, message):
        super(ForbiddenException, self).__init__(message, 403, 'Forbidden')

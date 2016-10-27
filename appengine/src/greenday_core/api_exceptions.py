"""
    Defines exceptions which can be caught by the API and be returned in a
    generic format understood by the client app
"""
from endpoints import api_exceptions as endpoints_exceptions

from .constants import ErrorCodes
from .utils import compose_new_type


class GreendayException(object):
    """
        Base Montage exception class

        Formats exception messages
    """
    code = None

    def __init__(self, message=None, *args, **kwargs):
        message = "{0}|{1}".format(self.code or self.http_status, message)

        super(GreendayException, self).__init__(message, *args, **kwargs)


# create some custom exception bases to inherit from
BadRequestException = compose_new_type(
    "BadRequestException",
    endpoints_exceptions.BadRequestException,
    GreendayException)


ForbiddenException = compose_new_type(
    "ForbiddenException",
    endpoints_exceptions.ForbiddenException,
    GreendayException)


InternalServerErrorException = compose_new_type(
    "InternalServerErrorException",
    endpoints_exceptions.InternalServerErrorException,
    GreendayException)


NotFoundException = compose_new_type(
    "NotFoundException",
    endpoints_exceptions.NotFoundException,
    GreendayException)


UnauthorizedException = compose_new_type(
    "UnauthorizedException",
    endpoints_exceptions.UnauthorizedException,
    GreendayException)


class TagNameExistsException(BadRequestException):
    """
        Raised when a tag with the same already exists
    """
    code = ErrorCodes.TAG_NAME_ALREADY_EXISTS


class BadSearchDateFormatException(BadRequestException):
    """
        Raised when the video search cannot parse the
        provided date format
    """
    code = ErrorCodes.BAD_SEARCH_DATE_FORMAT


class BadSearchGeoFormatException(BadRequestException):
    """
        Raised when the video search cannot parse the
        provided location format
    """
    code = ErrorCodes.BAD_SEARCH_GEO_FORMAT


class TagAlreadyAppliedToProject(BadRequestException):
    """
        Raised when a tag has already been related to
        a project
    """
    code = ErrorCodes.TAG_ALREADY_ON_PROJECT

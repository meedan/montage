"""
    Defines enums used through the application
"""
# LIBRARIES
from enum import IntEnum

# GREENDAY
from .utils import choices

CODES_PER_MODEL = 100


def create_kind(model, code):
    """
        Creates a compound event kind from an
        :class:`greenday_core.constants.EventModel <greenday_core.constants.EventModel>`
        and a code unique within that model's kinds
    """
    return model*CODES_PER_MODEL+code


class EventModel(IntEnum):
    """
        Defines models for which events may be recorded
    """
    PROJECT = 0
    VIDEO = 1
    USER = 2
    VIDEO_COLLECTION = 3
    PENDINGUSER = 4
    PROJECT_COMMENT = 5
    TIMED_VIDEO_COMMENT = 6
    TIMED_VIDEO_COMMENT_REPLY = 7
    PROJECT_COMMENT_REPLY = 8


class EventCommonCodes(IntEnum):
    """
        These codes are common to many objects and the values
        are consistent between EventKind values
    """
    CREATED = 0
    UPDATED = 1
    DELETED = 2


@choices
class EventKind(IntEnum):
    """
        A way to uniquely identify a type of event which can happen within the
        system. These should be very specific.

        This *may* look crazy but it does make sense. It allows us to use a
        single value to represent an event on a given model and keep consistent
        values for similar events (create, update, delete).

        Essentially these values are constructed so that the result of dividing
        by CODES_PER_MODEL will give you the EventModel and getting the
        remainder will give you the event code.


        I.e.
            EventKind.VIDEODELETED == 102
            102 / CODES_PER_MODEL == 1 (EventModel.VIDEO)
            102 % CODES_PER_MODEL == 2 (EventCommonCodes.DELETED)

        Better: model, code = divmod(102, CODES_PER_MODEL)
            == (1, 2)
    """

    # PROJECTS 0-99
    PROJECTCREATED = create_kind(EventModel.PROJECT, EventCommonCodes.CREATED)
    PROJECTUPDATED = create_kind(EventModel.PROJECT, EventCommonCodes.UPDATED)
    PROJECTDELETED = create_kind(EventModel.PROJECT, EventCommonCodes.DELETED)
    PROJECTRESTORED = create_kind(EventModel.PROJECT, 50)

    # VIDEOS 100-199
    VIDEOCREATED = create_kind(EventModel.VIDEO, EventCommonCodes.CREATED)
    VIDEOUPDATED = create_kind(EventModel.VIDEO, EventCommonCodes.UPDATED)
    VIDEODELETED = create_kind(EventModel.VIDEO, EventCommonCodes.DELETED)
    VIDEOHIGHLIGHTED = create_kind(EventModel.VIDEO, 50)
    VIDEOUNHIGHLIGHTED = create_kind(EventModel.VIDEO, 51)
    VIDEOARCHIVED = create_kind(EventModel.VIDEO, 52)
    VIDEOUNARCHIVED = create_kind(EventModel.VIDEO, 53)

    # USER 200-299
    USERCREATED = create_kind(EventModel.USER, EventCommonCodes.CREATED)
    USERUPDATED = create_kind(EventModel.USER, EventCommonCodes.UPDATED)
    USERDELETED = create_kind(EventModel.USER, EventCommonCodes.DELETED)
    USERACCEPTEDNDA = create_kind(EventModel.USER, 50)
    USERINVITEDASPROJECTUSER = create_kind(EventModel.USER, 51)
    USERINVITEDASPROJECTADMIN = create_kind(EventModel.USER, 52)
    USERACCEPTEDPROJECTINVITE = create_kind(EventModel.USER, 53)
    USERREJECTEDPROJECTINVITE = create_kind(EventModel.USER, 54)
    USERREMOVED = create_kind(EventModel.USER, 55)
    PROJECTCOLLABORATORONLINE = create_kind(EventModel.USER, 56)
    PROJECTCOLLABORATOROFFLINE = create_kind(EventModel.USER, 57)
    USEREXPORTEDVIDEOS = create_kind(EventModel.USER, 58)

    # COLLECTIONS 300-399
    VIDEOCOLLECTIONCREATED = create_kind(
        EventModel.VIDEO_COLLECTION, EventCommonCodes.CREATED)
    VIDEOCOLLECTIONUPDATED = create_kind(
        EventModel.VIDEO_COLLECTION, EventCommonCodes.UPDATED)
    VIDEOCOLLECTIONDELETED = create_kind(
        EventModel.VIDEO_COLLECTION, EventCommonCodes.DELETED)
    VIDEOADDEDTOCOLLECTION = create_kind(EventModel.VIDEO_COLLECTION, 50)
    VIDEOREMOVEDFROMCOLLECTION = create_kind(EventModel.VIDEO_COLLECTION, 51)

    # PENDING USER 400-499
    PENDINGUSERINVITEDASPROJECTADMIN = create_kind(EventModel.PENDINGUSER, 50)
    PENDINGUSERINVITEDASPROJECTUSER = create_kind(EventModel.PENDINGUSER, 51)
    PENDINGUSERREMOVED = create_kind(EventModel.USER, 52)

    # PROJECT COMMENT 500-599
    PROJECTROOTCOMMENTCREATED = create_kind(
        EventModel.PROJECT_COMMENT, EventCommonCodes.CREATED)
    PROJECTCOMMENTUPDATED = create_kind(
        EventModel.PROJECT_COMMENT, EventCommonCodes.UPDATED)
    PROJECTCOMMENTDELETED = create_kind(
        EventModel.PROJECT_COMMENT, EventCommonCodes.DELETED)
    PROJECTREPLYCOMMENTCREATED = create_kind(
        EventModel.PROJECT_COMMENT_REPLY, EventCommonCodes.CREATED)
    PROJECTREPLYCOMMENTUPDATED = create_kind(
        EventModel.PROJECT_COMMENT_REPLY, EventCommonCodes.UPDATED)
    PROJECTREPLYCOMMENTDELETED = create_kind(
        EventModel.PROJECT_COMMENT_REPLY, EventCommonCodes.DELETED)

    # TIMED VIDEO COMMENT 600-699
    TIMEDVIDEOROOTCOMMENTCREATED = create_kind(
        EventModel.TIMED_VIDEO_COMMENT, EventCommonCodes.CREATED)
    TIMEDVIDEOCOMMENTUPDATED = create_kind(
        EventModel.TIMED_VIDEO_COMMENT, EventCommonCodes.UPDATED)
    TIMEDVIDEOCOMMENTDELETED = create_kind(
        EventModel.TIMED_VIDEO_COMMENT, EventCommonCodes.DELETED)
    TIMEDVIDEOREPLYCOMMENTCREATED = create_kind(
        EventModel.TIMED_VIDEO_COMMENT_REPLY, EventCommonCodes.CREATED)
    TIMEDVIDEOREPLYCOMMENTUPDATED = create_kind(
        EventModel.TIMED_VIDEO_COMMENT_REPLY, EventCommonCodes.UPDATED)
    TIMEDVIDEOREPLYCOMMENTDELETED = create_kind(
        EventModel.TIMED_VIDEO_COMMENT_REPLY, EventCommonCodes.DELETED)

# Don't use HTTP status codes
class ErrorCodes(IntEnum):
    """
        Codes understand by the client application. These are returned in
        the case of exceptions and the client application can react
        appropriately
    """
    TAG_NAME_ALREADY_EXISTS = 1000
    BAD_SEARCH_DATE_FORMAT = 1001
    BAD_SEARCH_GEO_FORMAT = 1002
    TAG_ALREADY_ON_PROJECT = 1003

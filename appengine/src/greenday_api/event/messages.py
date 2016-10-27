"""
    Defines response messages for event API
"""
from protorpc import messages

from greenday_core.models import Event

from django_protorpc import DjangoProtoRPCMessage

from ..comment.messages import CommentResponseMessageSlim
from ..project.messages import ProjectResponseMessageBasic
from ..user.messages import UserResponseBasic
from ..video.messages import (
    CollectionResponseMessageSkinny,
    VideoResponseMessage
)


class EventResponseMessage(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent an application event."""
    class Meta:
        model = Event

    object_type = messages.StringField(1)
    event_type = messages.StringField(2)


class EventListResponse(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent a list of events."""
    events = messages.MessageField(
        EventResponseMessage, 1, repeated=True)

    projects = messages.MessageField(
        ProjectResponseMessageBasic, 2, repeated=True)
    users = messages.MessageField(
        UserResponseBasic, 3, repeated=True)
    video_collections = messages.MessageField(
        CollectionResponseMessageSkinny, 4, repeated=True)
    videos = messages.MessageField(
        VideoResponseMessage, 5, repeated=True)
    project_comments = messages.MessageField(
        CommentResponseMessageSlim, 6, repeated=True)

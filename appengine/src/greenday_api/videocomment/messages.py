"""
    Protorpc messages for video comment API
"""
from protorpc import messages
from django_protorpc import DjangoProtoRPCMessage, nest_message

from greenday_core.models import TimedVideoComment

from ..comment.messages import CommentUserResponse, CommentResponseMessageSlim


class VideoCommentResponseMessageSlim(DjangoProtoRPCMessage):
    """ Message to represent either root or child comments """
    comment = nest_message(CommentResponseMessageSlim, 1)
    user = messages.MessageField(CommentUserResponse, 2)
    start_seconds = messages.FloatField(3)
    project_id = messages.IntegerField(4, variant=messages.Variant.INT32)
    youtube_id = messages.StringField(5)
    duration = messages.IntegerField(6, variant=messages.Variant.INT32)

class VideoCommentResponseMessage(DjangoProtoRPCMessage):
    """ Message to repesent a root level comment """
    comment = nest_message(VideoCommentResponseMessageSlim, 1)

    replies = messages.MessageField(
        VideoCommentResponseMessageSlim, 2, repeated=True)


class VideoCommentListResponse(messages.Message):
    """ Message to represent a list of root-level comments """
    items = messages.MessageField(
        VideoCommentResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)


class VideoCommentRequestMessage(DjangoProtoRPCMessage):
    """
        Message to represent video comment request data
    """
    class Meta:
        model = TimedVideoComment
        fields = (
            'text',
            'start_seconds',
        )


class VideoCommentReplyMessage(DjangoProtoRPCMessage):
    """
        Message to represent a reply to a video comment
    """
    class Meta:
        model = TimedVideoComment
        fields = ('text',)

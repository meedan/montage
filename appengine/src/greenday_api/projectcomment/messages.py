"""
	ProtoRPC messages for specific to the project comment API
"""
from protorpc import messages

from ..comment.messages import CommentResponseMessage
from ..videocomment.messages import VideoCommentResponseMessage


class ProjectCommentListResponse(messages.Message):
    """ Message to represent a list of root-level comments """
    items = messages.MessageField(
        CommentResponseMessage, 1, repeated=True)
    video_comments = messages.MessageField(
        VideoCommentResponseMessage, 2, repeated=True)
    is_list = messages.BooleanField(3)

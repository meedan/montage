"""
    Request data containers for video comment API
"""
import endpoints
from protorpc import messages as api_messages

from .messages import (
    VideoCommentRequestMessage, VideoCommentReplyMessage
)


CreateVideoRootCommentContainer = endpoints.ResourceContainer(
    VideoCommentRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3)
)

UpdateVideoCommentContainer = endpoints.ResourceContainer(
    VideoCommentRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    comment_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32)
)

VideoCommentEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    comment_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32)
)

CreateVideoCommentReplyContainer = endpoints.ResourceContainer(
    VideoCommentReplyMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    comment_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32)
)

UpdateVideoCommentReplyContainer = endpoints.ResourceContainer(
    VideoCommentReplyMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    comment_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32),
    reply_id=api_messages.IntegerField(
        5, variant=api_messages.Variant.INT32)
)

VideoCommentReplyContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    comment_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32),
    reply_id=api_messages.IntegerField(
        5, variant=api_messages.Variant.INT32)
)

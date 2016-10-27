"""
    Request containers for the projet comments API
"""
import endpoints
from protorpc import message_types, messages as api_messages

from ..comment.messages import CommentRequestMessage


ProjectCommentListContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    show_video_comments=api_messages.BooleanField(3, required=False),
    since=message_types.DateTimeField(4, required=False)
)

ProjectCommentEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    comment_id=api_messages.IntegerField(
        3, variant=api_messages.Variant.INT32)
)

CreateProjectRootCommentContainer = endpoints.ResourceContainer(
    CommentRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
)

CreateProjectCommentReplyContainer = endpoints.ResourceContainer(
	CommentRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    comment_id=api_messages.IntegerField(
        3, variant=api_messages.Variant.INT32)
)

UpdateProjectCommentContainer = endpoints.ResourceContainer(
    CommentRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    comment_id=api_messages.IntegerField(
        3, variant=api_messages.Variant.INT32)
)

UpdateProjectCommentReplyContainer = endpoints.ResourceContainer(
    CommentRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    comment_id=api_messages.IntegerField(
        3, variant=api_messages.Variant.INT32),
    reply_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32)
)

ProjectCommentReplyEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    comment_id=api_messages.IntegerField(
        3, variant=api_messages.Variant.INT32),
    reply_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32)
)

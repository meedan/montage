"""
    Utils module for events API
"""
import json
from protorpc.protojson import encode_message

from django.contrib.auth import get_user_model
from django.utils.functional import SimpleLazyObject

from greenday_core.constants import EventModel, CODES_PER_MODEL
from greenday_core.models import Project, PendingUser

from ..mapper import GeneralMapper
from ..comment.mappers import CommentMapper
from ..video.mappers import VideoMapper, VideoCollectionMapper
from ..comment.messages import CommentResponseMessageSlim
from ..project.messages import ProjectResponseMessageBasic
from ..videocomment.messages import VideoCommentResponseMessageSlim
from ..user.messages import UserResponseBasic

MESSAGE_MAPPER_MAP = SimpleLazyObject(lambda: {
    EventModel.PROJECT_COMMENT: CommentMapper(CommentResponseMessageSlim),
    EventModel.PROJECT_COMMENT_REPLY: CommentMapper(CommentResponseMessageSlim),
    EventModel.TIMED_VIDEO_COMMENT: CommentMapper(
        VideoCommentResponseMessageSlim),
    EventModel.TIMED_VIDEO_COMMENT_REPLY: CommentMapper(
        VideoCommentResponseMessageSlim),
    EventModel.PROJECT: GeneralMapper(Project, ProjectResponseMessageBasic),
    EventModel.USER: GeneralMapper(get_user_model(), UserResponseBasic),
    EventModel.PENDINGUSER: GeneralMapper(PendingUser, UserResponseBasic),
    EventModel.VIDEO: VideoMapper(),
    EventModel.VIDEO_COLLECTION: VideoCollectionMapper()
})


def get_model_message(event, model):
    """
        Generic method to map a Django model to a response
        message
    """
    model_enum = EventModel(event.kind / CODES_PER_MODEL)
    mapper = MESSAGE_MAPPER_MAP.get(model_enum)

    if mapper:
        message = mapper.map(model)
        # TODO: don't encode and decode to string
        return json.loads(encode_message(message))

"""
    Mappers for the video comment API
"""
from greenday_core.utils import compose_new_type

from ..comment.mappers import CommentMapper, CommentFullMapper


class VideoCommentMapper(CommentMapper):
    """
        Mapper class to map root
        :class:`TimedVideoComment <greenday_core.models.comment.TimedVideoComment>`
        entities
    """
    def get_message_field_value(
            self, obj, message_field_name, video=None, **extra):
        if message_field_name in ('youtube_id', 'duration',):
            return getattr(video.youtube_video, message_field_name, None)

        return super(VideoCommentMapper, self).get_message_field_value(
            obj, message_field_name, **extra)


VideoCommentFullMapper = compose_new_type(
    "VideoCommentFullMapper", CommentFullMapper, VideoCommentMapper)

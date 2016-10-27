"""
    Generic mappers for the commenting API
"""
from django.contrib.auth import get_user_model

from greenday_core.models import Comment

from ..mapper import GeneralMapper
from .messages import CommentUserResponse, CommentResponseMessageSlim


class CommentMapper(GeneralMapper):
    """
        Mapper class to map any
        :class:`Comment <greenday_core.models.comment.Comment>` entity
    """
    def __init__(self, message_type):
        """
            Creates mapper.

            message_type: The response message to be returned
        """
        self.user_mapper = GeneralMapper(
            get_user_model(), CommentUserResponse)

        super(CommentMapper, self).__init__(Comment, message_type)

    def get_message_field_value(self, obj, message_field_name, **extra):
        """
            Custom mapping behaviour
        """
        if message_field_name == 'user':
            return self.user_mapper.map(obj.user)

        if message_field_name == 'youtube_id':
            return obj.video.youtube_id

        if message_field_name == 'thread_id':
            parent = obj.get_parent()
            return parent.pk if parent else None

        return super(CommentMapper, self).get_message_field_value(
            obj, message_field_name, **extra)


class CommentFullMapper(CommentMapper):
    """
        Mapper class to map root
        :class:`Comment <greenday_core.models.comment.Comment>` entities
        along with their replies
    """
    def __init__(self, message_type, slim_mapper=None, reverse_order=False):
        """
            Creates mapper.

            message_type: The response message to be returned
            slim_mapper: The mapper instance to map nested comment replies.
            reverse_order: Reverses the order of the nested list of comment
                replies.
        """
        self.slim_mapper = slim_mapper or CommentMapper(
            CommentResponseMessageSlim)

        self.reverse_order = reverse_order

        super(CommentFullMapper, self).__init__(message_type)

    def get_message_field_value(self, obj, message_field_name, **extra):
        """
            Custom mapping behaviour
        """
        if message_field_name == 'replies' and obj.is_root():
            return [
                self.slim_mapper.map(c, **extra)
                for c in obj.get_replies(reverse_order=self.reverse_order)]

        return super(CommentFullMapper, self).get_message_field_value(
            obj, message_field_name, **extra)

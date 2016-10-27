"""
    Base definitions of API response messages for comments
"""
from protorpc import messages, message_types
from django_protorpc import DjangoProtoRPCMessage, nest_message

from django.contrib.auth import get_user_model

from greenday_core.models import Comment


class CommentUserResponse(DjangoProtoRPCMessage):
    """ Message to represent a user on a comment """
    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'profile_img_url',
            'google_plus_profile',
        )


class CommentResponseMessageSlim(DjangoProtoRPCMessage):
    """ Message to represent either root or child comments """
    user = messages.MessageField(CommentUserResponse, 1)
    id = messages.IntegerField(
        2, variant=messages.Variant.INT32)
    text = messages.StringField(3)
    created = message_types.DateTimeField(4)
    project_id = messages.IntegerField(
        5, variant=messages.Variant.INT32)
    thread_id = messages.IntegerField(
        6, variant=messages.Variant.INT32)
    modified = message_types.DateTimeField(7)


class CommentResponseMessage(DjangoProtoRPCMessage):
    """ Message to repesent a root level comment """
    comment = nest_message(CommentResponseMessageSlim, 1)

    replies = messages.MessageField(
        CommentResponseMessageSlim, 2, repeated=True)


class CommentListResponse(messages.Message):
    """ Message to represent a list of root-level comments """
    items = messages.MessageField(
        CommentResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)

class CommentRequestMessage(DjangoProtoRPCMessage):
    """
        Message to encapsulate data passed to the API to create/update
        a comment
    """
    class Meta:
        model = Comment
        fields = (
            'text',
        )

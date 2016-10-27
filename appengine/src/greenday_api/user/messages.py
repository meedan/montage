"""
    Protorpc messages for the user API
"""
from protorpc import messages, message_types

from django.contrib.auth import get_user_model

from django_protorpc import DjangoProtoRPCMessage


class UserRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a user to be updated by
        themself.
    """
    first_name = messages.StringField(1)
    last_name = messages.StringField(2)
    email = messages.StringField(3)
    profile_img_url = messages.StringField(4)
    google_plus_profile = messages.StringField(5)
    accepted_nda = messages.BooleanField(6)
    last_login = message_types.DateTimeField(6)


class SuperUserRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a user to be updated by a
        super user.
    """
    class Meta:
        model = get_user_model()
        exclude = ('id', 'date_joined', 'username',)


class UserResponseMessage(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent a user that is stored."""
    class Meta:
        model = get_user_model()
        exclude = (
            'password',
            'actions',
            'owner_of_globaltags',
            'owner_of_projecttags',
            'owner_of_videotags',
            'owner_of_tag_instances',
            'owner_of_videos',
            'related_videos',
            'user_permissions',
            'groups',
            'videos',
            'projectusers',
        )


class UserResponseBasic(DjangoProtoRPCMessage):
    """ Message to return a user's basic data """
    id = messages.IntegerField(
        1, variant=messages.Variant.INT32)
    is_superuser = messages.BooleanField(2)
    gaia_id = messages.StringField(3)
    first_name = messages.StringField(4)
    last_name = messages.StringField(5)
    email = messages.StringField(6)
    profile_img_url = messages.StringField(7)
    google_plus_profile = messages.StringField(8)


class UserListResponse(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent a list of stored users."""
    items = messages.MessageField(UserResponseBasic, 1, repeated=True)
    is_list = messages.BooleanField(2)


class UserStatsResponse(DjangoProtoRPCMessage):
    """Message definition to represent a user's application stats"""
    id = messages.IntegerField(
        1, variant=messages.Variant.INT32)
    videos_watched = messages.IntegerField(
        2, variant=messages.Variant.INT32)
    tags_added = messages.IntegerField(
        3, variant=messages.Variant.INT32)

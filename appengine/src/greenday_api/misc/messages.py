"""
    Response messages for the distinct channels API
"""
from protorpc import messages, message_types


class DistinctChannelMessage(messages.Message):
    """
        Message to represent a channel id/name
    """
    id = messages.StringField(1)
    name = messages.StringField(2)


class DistinctChannelListResponse(messages.Message):
    """
        Message to represent a list of distinct channels
    """
    items = messages.MessageField(
        DistinctChannelMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)


class OnlineCollaboratorMessage(messages.Message):
    """
        Message to represent a user
    """
    id = messages.IntegerField(
        1, variant=messages.Variant.INT32)
    first_name = messages.StringField(2)
    last_name = messages.StringField(3)
    email = messages.StringField(4)
    profile_img_url = messages.StringField(5)
    google_plus_profile = messages.StringField(6)
    timestamp = message_types.DateTimeField(8)
    project_id = messages.IntegerField(9, variant=messages.Variant.INT32)


class OnlineCollaboratorsList(messages.Message):
    """
        Message to represent a list of users on a resource
    """
    items = messages.MessageField(
        OnlineCollaboratorMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)

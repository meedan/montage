"""
    Request data containers for user API
"""
import endpoints
from protorpc import messages as api_messages

from .messages import UserRequestMessage, SuperUserRequestMessage


UserFilterContainer = endpoints.ResourceContainer(
    api_messages.Message,
    q=api_messages.StringField(2)
)

UserCreateContainer = endpoints.ResourceContainer(
    api_messages.Message,
    email=api_messages.StringField(2, required=True)
)

UserUpdateContainer = endpoints.ResourceContainer(
    SuperUserRequestMessage,
    id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32)
)

CurrentUserUpdateContainer = endpoints.ResourceContainer(
    UserRequestMessage)

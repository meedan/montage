"""
    Request containers for the project API
"""
import endpoints
from protorpc import messages as api_messages

from .messages import (
    ProjectRequestMessage,
    ProjectUploadImageMessage,
)


ProjectListRequest = endpoints.ResourceContainer(
    api_messages.Message,
    pending=api_messages.BooleanField(2)
)
ProjectUpdateEntityContainer = endpoints.ResourceContainer(
    ProjectRequestMessage,
    id=api_messages.IntegerField(2, variant=api_messages.Variant.INT32)
)
ProjectUserEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(2, variant=api_messages.Variant.INT32),
    email=api_messages.StringField(3),
    as_admin=api_messages.BooleanField(4)
)
ProjectUserIDEntityContainer = endpoints.ResourceContainer(
    project_id=api_messages.IntegerField(2, variant=api_messages.Variant.INT32),
    id=api_messages.IntegerField(3, variant=api_messages.Variant.INT32),
    as_admin=api_messages.BooleanField(4)
)
ProjectIDContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(2, variant=api_messages.Variant.INT32)
)
ProjectUploadImageContainer = endpoints.ResourceContainer(
    ProjectUploadImageMessage,
    id=api_messages.IntegerField(2, variant=api_messages.Variant.INT32)
)

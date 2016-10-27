"""
    Request containers for the project tag API
"""
import endpoints
from protorpc import messages as api_messages

from .messages import (
    GlobalTagRequestMessage,
    MoveTagRequestMessage
)


ProjectIDContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32)
)
ProjectTagIDContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    project_tag_id=api_messages.IntegerField(
        3, variant=api_messages.Variant.INT32)
)
PutProjectTagContainer = endpoints.ResourceContainer(
    GlobalTagRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    project_tag_id=api_messages.IntegerField(
        3, variant=api_messages.Variant.INT32),
)
CreateProjectTagContainer = endpoints.ResourceContainer(
    GlobalTagRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
)
MoveProjectTagContainer = endpoints.ResourceContainer(
    MoveTagRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    project_tag_id=api_messages.IntegerField(
        3, variant=api_messages.Variant.INT32),
)

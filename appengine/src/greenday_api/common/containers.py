"""
    Defines shared request data containers
"""
import endpoints
from protorpc import messages as api_messages


VideoEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3)
)

IDContainer = endpoints.ResourceContainer(
    api_messages.Message,
    id=api_messages.IntegerField(2, variant=api_messages.Variant.INT32)
)

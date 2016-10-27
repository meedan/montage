"""
	Request containers for Tag API
"""
import endpoints
from protorpc import messages as api_messages


TagEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32)
)

TagSearchEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    q=api_messages.StringField(2, default=None),
    project_id=api_messages.IntegerField(
        3, variant=api_messages.Variant.INT32)
)

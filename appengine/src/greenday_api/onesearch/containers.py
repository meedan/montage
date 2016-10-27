"""
    Defines request containers for the OneSearch API
"""
import endpoints
from protorpc import messages as api_messages


# onesearch entity container
OneSearchEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    q=api_messages.StringField(2, required=False, default=None)
)

# onesearch advanced search entity container.
OneSearchAdvancedVideoEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, required=False, default=None,
        variant=api_messages.Variant.INT32),
    collection_id=api_messages.StringField(3),
    q=api_messages.StringField(4, required=False),
    channel_ids=api_messages.StringField(5),
    date=api_messages.StringField(6),
    location=api_messages.StringField(7),
    tag_ids=api_messages.StringField(8),
    exclude_ids=api_messages.StringField(9, required=False),
    youtube_id=api_messages.StringField(10)
)

# onesearch project context entity container
OneSearchProjectContextEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    q=api_messages.StringField(2, required=False, default=None),
    project_id=api_messages.IntegerField(
        3, required=False, default=None,
        variant=api_messages.Variant.INT32),
    exclude_ids=api_messages.StringField(4, required=False)
)

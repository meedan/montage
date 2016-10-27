import endpoints
from protorpc import messages as api_messages


TokenRequestContainer = endpoints.ResourceContainer(
    api_messages.Message,
    token=api_messages.StringField(1),
    channels=api_messages.StringField(2)
)


ChannelRequestContainer = endpoints.ResourceContainer(
    api_messages.Message,
    channels=api_messages.StringField(1)
)

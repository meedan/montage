from protorpc import messages as api_messages


class ChannelResponseMessage(api_messages.Message):
    """ProtoRPC message definition to represent an application event."""
    items = api_messages.StringField(1)


class SubscribeResponseMessage(api_messages.Message):
    """
        ProtoRPC message definition to represent the response of a
        channel subscription
    """
    token = api_messages.StringField(1)
    channels = api_messages.StringField(2, repeated=True)

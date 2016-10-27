"""
    Defines response messages for the OneSearch API
"""
from protorpc import messages

from django_protorpc import DjangoProtoRPCMessage

from greenday_core.models import Project, YouTubeVideo


# Project
class OneSearchProjectResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a project that is stored.
        This is used in the quick search.
    """
    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'created', 'modified')


# project list
class OneSearchProjectListResponse(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a list of stored projects
        returned in a suitable format for the global search.

        This is used in the quick search
    """
    items = messages.MessageField(
        OneSearchProjectResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)

# Video
class OneSearchVideoResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent an index video that is
        stored.

        This is used in the quick search
    """
    class Meta:
        model = YouTubeVideo
        fields = (
            'name',
            'youtube_id',
            'channel_id',
            'channel_name',
            'publish_date',
            'duration',
        )

    id = messages.IntegerField(
        1, variant=messages.Variant.INT32)
    project_id = messages.IntegerField(
        2, variant=messages.Variant.INT32)
    pretty_duration = messages.StringField(9)
    pretty_publish_date = messages.StringField(10)


# Video list
class OneSearchVideoListResponse(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a list of indexed videos
        returned in a suitable format for the global search.

        This is used in the quick search
    """
    items = messages.MessageField(
        OneSearchVideoResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)


# advanced search video response
class OneSearchAdvancedVideoResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a Video instance that
        is stored.

        This is used in the advanced search.
    """
    class Meta:
        model = YouTubeVideo
        fields = (
            'recorded_date',
            'name',
            'channel_name',
            'channel_id',
            'notes',
            'latitude',
            'longitude',
            'publish_date',
            'playlist_id',
            'playlist_name',
            'duration',
            'youtube_id',
        )

    id = messages.IntegerField(
        1, variant=messages.Variant.INT32)
    project_id = messages.IntegerField(
        2, variant=messages.Variant.INT32)
    tag_count = messages.IntegerField(
        3, variant=messages.Variant.INT32)
    watch_count = messages.IntegerField(
        4, variant=messages.Variant.INT32)
    in_collections = messages.IntegerField(
        5, variant=messages.Variant.INT32, repeated=True)
    favourited = messages.BooleanField(6)
    tag_summary = messages.StringField(7, repeated=True)
    pretty_duration = messages.StringField(9)
    pretty_publish_date = messages.StringField(10)


# advanced search video list response.
class OneSearchAdvancedVideoListResponse(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a list of video instances
        returned in a suitable format for the global search.

        This is used in the advanced search
    """
    items = messages.MessageField(
        OneSearchAdvancedVideoResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)

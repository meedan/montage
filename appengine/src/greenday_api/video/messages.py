"""
    Protorpc messages for video API
"""
from protorpc import messages, message_types

from greenday_core.models import (
    VideoCollection,
    UserVideoDetail,
    VideoTagInstance,
    GlobalTag,
    YouTubeVideo
)
from django_protorpc import DjangoProtoRPCMessage, nest_message


class VideoRequestMessage(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent a video to be inserted."""
    class Meta:
        model = YouTubeVideo
        fields = (
            'recorded_date',
            'latitude',
            'longitude',
        )

    recorded_date_overridden = messages.BooleanField(2)
    location_overridden = messages.BooleanField(3)
    precise_location = messages.BooleanField(4)


class VideoDuplicateRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to patch a video and mark it
        as a duplicate.
    """
    duplicate_of_id = messages.StringField(1)


class VideoResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition for a video response
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
            'missing_from_youtube',
        )

    id = messages.IntegerField(
        1, variant=messages.Variant.INT32)
    project_id = messages.IntegerField(
        2, variant=messages.Variant.INT32)
    recorded_date_overridden = messages.BooleanField(3)
    location_overridden = messages.BooleanField(4)
    archived_at = message_types.DateTimeField(5)
    created = message_types.DateTimeField(6)
    modified = message_types.DateTimeField(7)
    pretty_duration = messages.StringField(8)
    pretty_publish_date = messages.StringField(9)
    pretty_created = messages.StringField(10)
    in_collections = messages.IntegerField(
        11, variant=messages.Variant.INT32, repeated=True)
    favourited = messages.BooleanField(12)
    watch_count = messages.IntegerField(
        13, variant=messages.Variant.INT32)
    watched = messages.BooleanField(14)
    tag_count = messages.IntegerField(
        15, variant=messages.Variant.INT32)
    duplicate_count = messages.IntegerField(
        16, variant=messages.Variant.INT32)
    precise_location = messages.BooleanField(17)


class VideoResponseMessageSlim(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a Video
        in a list view
    """
    video_data = nest_message(VideoResponseMessage, 1)
    order = messages.IntegerField(2, variant=messages.Variant.INT32)


class VideoListResponse(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a list of stored
        video objects.
    """
    items = messages.MessageField(
        VideoResponseMessageSlim, 1, repeated=True)
    is_list = messages.BooleanField(2)

class VideoTagInstanceMessage(DjangoProtoRPCMessage):
    """
        Message to represent a video tag instance
    """
    class Meta:
        model = VideoTagInstance
        fields = ('start_seconds', 'end_seconds', 'user',)

    video_id = messages.IntegerField(
        3, variant=messages.Variant.INT32)
    youtube_id = messages.StringField(4)
    video_name = messages.StringField(5)


class VideoTagResponseMessage(DjangoProtoRPCMessage):
    """
        Message to represent a video tag with videos
        and tag instances nested below them
    """
    class Meta:
        model = GlobalTag
        fields = ('name', 'description', 'image_url',)

    global_tag_id = messages.IntegerField(
        3, variant=messages.Variant.INT32)
    instances = messages.MessageField(
        VideoTagInstanceMessage, 1, repeated=True)


class VideoTagListResponse(DjangoProtoRPCMessage):
    """
        Message to represent a list of tags
    """
    items = messages.MessageField(
        VideoTagResponseMessage, 1, repeated=True)
    is_list = messages.IntegerField(2)

class CollectionRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message to represent a video collection to be inserted
    """
    class Meta:
        model = VideoCollection
        exclude = (
            'id',
            'videos',
            'created',
            'modified',
            'videocollectionvideos')


class CollectionResponseMessageSkinny(DjangoProtoRPCMessage):
    """
        ProtoRPC message to represent a video collection without nested videos
    """
    class Meta:
        model = VideoCollection
        exclude = ('videos', 'videocollectionvideos')


class CollectionResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message to represent a video collection
    """
    meta = nest_message(CollectionResponseMessageSkinny, 1)
    videos = messages.MessageField(
        VideoResponseMessageSlim, 2, repeated=True)


class CollectionListResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message to represent a list of collections
    """
    items = messages.MessageField(
        CollectionResponseMessageSkinny, 1, repeated=True)
    is_list = messages.BooleanField(2)

class MoveCollectionVideoRequestMessage(DjangoProtoRPCMessage):
    """ Message to represent a video move within a collection """
    youtube_id = messages.StringField(1, required=True)

    sibling_youtube_id = messages.StringField(2, required=True)

    before = messages.BooleanField(3, required=False)


class CollectionVideoRequestMessage(messages.Message):
    """
        ProtoRPC message to represent a video to be added
        to a collection
    """
    youtube_id = messages.StringField(1, required=True)


class UserVideoDetailResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message to represent a users interaction
        with a video instance.
    """
    class Meta:
        model = UserVideoDetail


class BooleanFlagRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message to represent a boolean value
        to be stored.
    """
    value = messages.BooleanField(1, required=True)


class BatchVideoRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message to represent an object
        instances to be processed.
    """
    youtube_ids = messages.StringField(1, repeated=True)


class BatchVideoResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message to represent an object
        that was processed via a batch API endpoint
    """
    youtube_id = messages.StringField(1)
    success = messages.BooleanField(2)
    msg = messages.StringField(3)


class BatchListResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message to represent a list of batch objects
    """
    items = messages.MessageField(
        BatchVideoResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)


class VideoBatchListResponseMessage(DjangoProtoRPCMessage):
    """
        Message to represent a list of batched videos
    """
    meta = nest_message(BatchListResponseMessage, 1)
    videos = messages.MessageField(
        VideoResponseMessage, 2, repeated=True)


class SetFavouriteBatchRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC that re-uses the BatchRequestMessage and
        BooleanFlagRequestMessage to create a request message
        to use when setting favourites.
    """
    basic_batch = nest_message(BatchVideoRequestMessage, 1)
    basic_boolean = nest_message(BooleanFlagRequestMessage, 2)

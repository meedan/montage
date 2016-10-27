"""
    Request data containers for the video API
"""
import endpoints
from protorpc import messages as api_messages

from .messages import (
    VideoRequestMessage, VideoDuplicateRequestMessage,
    BooleanFlagRequestMessage,
    CollectionRequestMessage,
    MoveCollectionVideoRequestMessage,
    BatchVideoRequestMessage,
    SetFavouriteBatchRequestMessage,
    CollectionVideoRequestMessage
)


VideoEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
)

VideoInsertEntityContainer = endpoints.ResourceContainer(
    VideoRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
)

VideoUpdateEntityContainer = endpoints.ResourceContainer(
    VideoRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
)

VideoListContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    archived=api_messages.BooleanField(
        3, required=False)
)

VideoDuplicateEntityContainer = endpoints.ResourceContainer(
    VideoDuplicateRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3)
)

VideoBooleanFlagEntityContainer = endpoints.ResourceContainer(
    BooleanFlagRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3)
)

VideoBatchContainer = endpoints.ResourceContainer(
    BatchVideoRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32)
)

ArchiveVideoBatchContainer = endpoints.ResourceContainer(
    BatchVideoRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    unarchive=api_messages.BooleanField(3)
)

VideoIDBatchContainer = endpoints.ResourceContainer(
    BatchVideoRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3)
)

CreateVideoBatchContainer = endpoints.ResourceContainer(
    BatchVideoRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32)
)

VideoFavouriteBatchContainer = endpoints.ResourceContainer(
    SetFavouriteBatchRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32)
)

VideoFilterContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    collection_id=api_messages.StringField(3),
    q=api_messages.StringField(4),
    channel_ids=api_messages.StringField(5),
    date=api_messages.StringField(6),
    location=api_messages.StringField(7),
    tag_ids=api_messages.StringField(8),
    archived=api_messages.BooleanField(
        9, required=False)
)

"""
    Video collection containers
"""
CollectionVideoFilterContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    id=api_messages.IntegerField(3),
    q=api_messages.StringField(4),
    channel_ids=api_messages.StringField(5),
    date=api_messages.StringField(6),
    location=api_messages.StringField(7),
    tag_ids=api_messages.StringField(8),
    archived=api_messages.BooleanField(
        9, required=False)
)
CollectionEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    id=api_messages.IntegerField(3, variant=api_messages.Variant.INT32),
)
CollectionInsertEntityContainer = endpoints.ResourceContainer(
    CollectionRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32)
)
CollectionUpdateEntityContainer = endpoints.ResourceContainer(
    CollectionRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    id=api_messages.IntegerField(3, variant=api_messages.Variant.INT32),
)
CollectionListContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32)
)
CollectionVideoContainer = endpoints.ResourceContainer(
    CollectionVideoRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    id=api_messages.IntegerField(3, variant=api_messages.Variant.INT32)
)
CollectionDeleteVideoContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    id=api_messages.IntegerField(3, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(4, required=True)
)
MoveCollectionVideoContainer = endpoints.ResourceContainer(
    MoveCollectionVideoRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    id=api_messages.IntegerField(3, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(4, required=True)
)
CollectionVideoBatchContainer = endpoints.ResourceContainer(
    BatchVideoRequestMessage,
    project_id=api_messages.IntegerField(
        2, required=True, variant=api_messages.Variant.INT32),
    id=api_messages.IntegerField(3, variant=api_messages.Variant.INT32)
)

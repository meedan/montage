"""
    Request data containers for the video tag API
"""

import endpoints
from protorpc import messages as api_messages

from .messages import (
    VideoTagInstanceRequestMessage, VideoTagRequestMessage
)

"""
    Video
    TODO: Maybe re-use the container held in videos_api.py?
"""

# video tag
VideoEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3)
)

"""
    VideoTag
"""

# video tag
VideoTagEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    video_tag_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32)
)

# video tag insert
VideoTagInsertEntityContainer = endpoints.ResourceContainer(
    VideoTagRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
)

# video tag update
VideoTagUpdateEntityContainer = endpoints.ResourceContainer(
    VideoTagRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    video_tag_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32)
)

"""
    VideoTagInstance
"""

# video tag instance
VideoTagInstanceEntityContainer = endpoints.ResourceContainer(
    api_messages.Message,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    video_tag_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32),
    instance_id=api_messages.IntegerField(
        5, variant=api_messages.Variant.INT32)
)

# video tag instance insert
VideoTagInstanceInsertEntityContainer = endpoints.ResourceContainer(
    VideoTagInstanceRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    video_tag_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32),
)

# video tag instance update
VideoTagInstanceUpdateEntityContainer = endpoints.ResourceContainer(
    VideoTagInstanceRequestMessage,
    project_id=api_messages.IntegerField(
        2, variant=api_messages.Variant.INT32),
    youtube_id=api_messages.StringField(3),
    video_tag_id=api_messages.IntegerField(
        4, variant=api_messages.Variant.INT32),
    instance_id=api_messages.IntegerField(
        5, variant=api_messages.Variant.INT32)
)

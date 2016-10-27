"""
    Protorpc messages for video tag API
"""
from protorpc import messages

from greenday_core.models import GlobalTag, VideoTagInstance
from django_protorpc import DjangoProtoRPCMessage


class VideoTagInstanceResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a video tag instance that
        is stored.
    """
    class Meta:
        model = VideoTagInstance
        fields = (
            'id',
            'start_seconds',
            'end_seconds',
            'video_tag',
            'created',
            'modified'
        )

    youtube_id = messages.StringField(1)
    global_tag_id = messages.IntegerField(
        2, required=False, variant=messages.Variant.INT32)
    video_id = messages.IntegerField(
        3, required=False, variant=messages.Variant.INT32)
    project_id = messages.IntegerField(
        5, required=False, variant=messages.Variant.INT32)
    project_tag_id = messages.IntegerField(
        6, required=False, variant=messages.Variant.INT32)


class VideoTagInstanceListResponse(messages.Message):
    """
        ProtoRPC message definition to represent a list of stored
        video tag instances returned in a suitable format.
    """
    items = messages.MessageField(
        VideoTagInstanceResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)

class ProjectTagResponseMessage(DjangoProtoRPCMessage):
    class Meta:
        model = GlobalTag
        exclude = (
            "user",
            "created_from_project"
        )

    project_id = messages.IntegerField(
        5, required=False, variant=messages.Variant.INT32)
    global_tag_id = messages.IntegerField(
        6, required=False, variant=messages.Variant.INT32)


class VideoTagResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a video tag that is stored.
    """
    id = messages.IntegerField(
        1, required=False, variant=messages.Variant.INT32)
    instances = messages.MessageField(
        VideoTagInstanceResponseMessage, 2, repeated=True)
    video_id = messages.IntegerField(
        3, required=False, variant=messages.Variant.INT32)
    youtube_id = messages.StringField(4)
    project_tag = messages.MessageField(
        ProjectTagResponseMessage, 6, required=False)
    project_tag_id = messages.IntegerField(
        7, required=False, variant=messages.Variant.INT32)
    project_id = messages.IntegerField(
        8, required=False, variant=messages.Variant.INT32)

class VideoTagRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a video tag that is to
        be created.
    """
    global_tag_id = messages.IntegerField(
        1, required=False, variant=messages.Variant.INT32)

    class Meta:
        model = GlobalTag
        never_required = True
        fields = (
            'name',
            'image_url',
            'description',
        )


class VideoTagListResponse(messages.Message):
    """
        ProtoRPC message definition to represent a list of stored
        video tags returned in a suitable format.
    """
    items = messages.MessageField(
        VideoTagResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)


class VideoTagInstanceRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a video tag to be
        updated.
    """
    class Meta:
        model = VideoTagInstance
        fields = (
            'start_seconds',
            'end_seconds',
        )

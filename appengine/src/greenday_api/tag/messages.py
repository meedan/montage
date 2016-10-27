"""
    Tag API protorpc messages
"""
from protorpc import messages

from greenday_core.models import GlobalTag
from django_protorpc import DjangoProtoRPCMessage


class TagResponseMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a tag that is stored.
    """
    class Meta:
        model = GlobalTag
        never_required = True
        fields = (
            'id',
            'name',
            'description',
            'image_url',
        )

    project_id = messages.IntegerField(
        2, required=False, variant=messages.Variant.INT32)


class TagListResponse(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a list of stored tags
        returned in a suitable format.
    """
    items = messages.MessageField(
        TagResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)


class TagSplitListResponse(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a list of stored tags
        returned in a suitable format.
    """
    project_tags = messages.MessageField(
        TagResponseMessage, 1, repeated=True)
    global_tags = messages.MessageField(
        TagResponseMessage, 2, repeated=True)


# others tagged with
class OthersTaggedWithListResponse(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a list of global tags
        that are not currently assigned to a video.
    """
    items = messages.MessageField(TagResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)


class MergeTagRequestMessage(DjangoProtoRPCMessage):
    """
        Mesasge definition to merge two tags
    """
    merging_from_tag_id = messages.IntegerField(
        1, required=True, variant=messages.Variant.INT32)
    merging_into_tag_id = messages.IntegerField(
        2, required=True, variant=messages.Variant.INT32)

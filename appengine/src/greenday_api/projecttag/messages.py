"""
    Defines protorpc messages for the project tag API
"""
from protorpc import messages
from django_protorpc import DjangoProtoRPCMessage, nest_message


class ProjectTagBasic(DjangoProtoRPCMessage):
    """
        Basic structure of a project tag. Intended to be merged
        into other message types
    """
    id = messages.IntegerField(1, variant=messages.Variant.INT32)
    name = messages.StringField(2)
    description = messages.StringField(3)
    image_url = messages.StringField(4)
    order = messages.FloatField(5)
    parent_id = messages.IntegerField(6, variant=messages.Variant.INT32)
    project_id = messages.IntegerField(
        7, variant=messages.Variant.INT32)
    global_tag_id = messages.IntegerField(
        8, variant=messages.Variant.INT32)

class ProjectTagSlimMessage(DjangoProtoRPCMessage):
    """
        Minimal message definition to represent a project tag.

        Intended for use in a list.
    """
    basic_tag = nest_message(ProjectTagBasic, 1)
    video_tag_instance_count = messages.IntegerField(
        2, variant=messages.Variant.INT32)


class ProjectTagListResponse(DjangoProtoRPCMessage):
    """
        Message definition to represent a list of project tags.
    """
    items = messages.MessageField(ProjectTagSlimMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)


class ProjectTagMessage(DjangoProtoRPCMessage):
    """
        Message definition to represent a project tag
    """
    basic_tag = nest_message(ProjectTagBasic, 1)
    videotag_count = messages.IntegerField(2)


class GlobalTagRequestMessage(DjangoProtoRPCMessage):
    """
        Message definition to create or update a global tag
    """
    name = messages.StringField(1, required=True)
    description = messages.StringField(2)
    image_url = messages.StringField(3)
    global_tag_id = messages.IntegerField(
        4, required=False, variant=messages.Variant.INT32)

class MoveTagRequestMessage(DjangoProtoRPCMessage):
    """
        Message definition to move a project tag within the tag hierarchy.
    """
    sibling_tag_id = messages.IntegerField(
        1, required=False, variant=messages.Variant.INT32)
    before = messages.BooleanField(2, required=False)
    parent_tag_id = messages.IntegerField(
        3, required=False, variant=messages.Variant.INT32)

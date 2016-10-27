"""
    Defines response messages for the project API
"""
from protorpc import messages, message_types
from django.contrib.auth import get_user_model

from greenday_core.models import Project, ProjectUser

from django_protorpc import DjangoProtoRPCMessage, nest_message

from ..video.messages import CollectionResponseMessageSkinny


class UserResponseMessage(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent a user that is stored."""
    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'profile_img_url'
        )

    # project-specific field
    is_admin = messages.BooleanField(14)


class ProjectTagResponseMessageSlim(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent project tags.
    """
    taginstance_count = messages.IntegerField(
        1, variant=messages.Variant.INT32)
    name = messages.StringField(2, required=False)
    id = messages.IntegerField(
        3, variant=messages.Variant.INT32)

class ProjectRequestMessage(DjangoProtoRPCMessage):
    """
        ProtoRPC message definition to represent a project to be inserted.
        accepts:
            image_url
            image_gcs_filename
            name
            description
            privacy_project (should be either 2 (PUBLIC) or 1 (PRIVATE)
            privacy_tags (should be either 2 (PUBLIC) or 1 (PRIVATE)
    """
    class Meta:
        model = Project
        fields = (
            'image_url',
            'image_gcs_filename',
            'name',
            'description',
        )

    privacy_project = messages.IntegerField(
        1, variant=messages.Variant.INT32)
    privacy_tags = messages.IntegerField(
        2, variant=messages.Variant.INT32)


class ProjectUserResponseMessage(DjangoProtoRPCMessage):
    """
        Message to hold information about a users relationship with the project
    """
    class Meta:
        model = ProjectUser
        exclude = (
            'user',
            'project',
        )


class ProjectCollaboratorsResponseMessage(DjangoProtoRPCMessage):
    """
        Message to hold information about a users relationship with the
        project. This endpoint is more detailed in that it returns the
        user_id too.
    """
    first_name = messages.StringField(1)
    last_name = messages.StringField(2)
    email = messages.StringField(3)
    profile_img_url = messages.StringField(4)

    class Meta:
        model = ProjectUser
        fields = (
            'id',
            'pending_user',
            'user',
            'created',
            'modified',
            'is_admin',
            'is_assigned',
            'is_owner',
            'is_pending',
            'project',
        )


class ProjectResponseMessageBasic(DjangoProtoRPCMessage):
    """ Message to represent minimal information on a project """
    class Meta:
        model = Project
        fields = (
            'id',
            'name',
            'description',
            'created',
            'modified',
            'image_url',
            'privacy_project',
            'privacy_tags',
            'video_tag_instance_count',
        )


class ProjectResponseMessageSlim(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent a project that is stored."""
    basic_project = nest_message(ProjectResponseMessageBasic, 1)
    video_count = messages.IntegerField(8, variant=messages.Variant.INT32)
    current_user_info = messages.MessageField(
        ProjectUserResponseMessage, 9)


class ProjectResponseMessage(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent a project that is stored."""
    class Meta:
        model = Project
        exclude = (
            'trashed_at',
            'owner',
            'videos',
            'collections',
            'projectusers',
            'users',
            'projecttags',
            'videotags',
        )

    slim_project = nest_message(ProjectResponseMessageSlim, 1)
    collections = messages.MessageField(
        CollectionResponseMessageSkinny, 2, repeated=True)
    admin_ids = messages.IntegerField(
        3, repeated=True, variant=messages.Variant.INT32)
    assigned_user_ids = messages.IntegerField(
        4, repeated=True, variant=messages.Variant.INT32)
    current_user_info = messages.MessageField(
        ProjectUserResponseMessage, 4)
    projecttags = messages.MessageField(
        ProjectTagResponseMessageSlim, 5, repeated=True)
    owner = messages.MessageField(UserResponseMessage, 6)


class ProjectListResponse(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent a list of stored projects."""
    items = messages.MessageField(ProjectResponseMessageSlim, 1, repeated=True)
    is_list = messages.BooleanField(2)


class ProjectUserListResponse(DjangoProtoRPCMessage):
    """ProtoRPC message definition to represent a list of stored users."""
    items = messages.MessageField(
        ProjectCollaboratorsResponseMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)


class ProjectUploadImageMessage(messages.Message):
    """ Message definition to upload a project image *not currently used* """
    image_bytes = messages.BytesField(1)
    image_name = messages.StringField(2)


class GenericProjectUpdateMessage(messages.Message):
    """
        Message definition to represent a project update
        I.e. Video added, tag added, user joined
    """
    id = messages.IntegerField(1, variant=messages.Variant.INT32)
    name = messages.StringField(2)
    timestamp = message_types.DateTimeField(3)


class ProjectUpdatesMessage(messages.Message):
    """
        Message definition to encapsulate a list of project updates
    """
    created_videos = messages.MessageField(
        GenericProjectUpdateMessage, 1, repeated=True)
    users_joined = messages.MessageField(
        GenericProjectUpdateMessage, 2, repeated=True)


class ProjectUpdateCountsMessage(messages.Message):
    """
        Message definition to encapsulate a list of project update counts
    """
    created_videos = messages.IntegerField(1, variant=messages.Variant.INT32)
    users_joined = messages.IntegerField(2, variant=messages.Variant.INT32)


class TagCountMessage(messages.Message):
    """
        Message definition to contain a tag count
    """
    name = messages.StringField(1)
    count = messages.IntegerField(2, variant=messages.Variant.INT32)


class ProjectStatsMessage(messages.Message):
    """
        Message definition to contain a list of project stats
    """
    total_videos = messages.IntegerField(1, variant=messages.Variant.INT32)
    archived_videos = messages.IntegerField(2, variant=messages.Variant.INT32)
    favourited_videos = messages.IntegerField(
        3, variant=messages.Variant.INT32)
    video_tags = messages.IntegerField(4, variant=messages.Variant.INT32)
    watched_videos = messages.IntegerField(5, variant=messages.Variant.INT32)

    total_tags = messages.IntegerField(6, variant=messages.Variant.INT32)
    top_tags = messages.MessageField(TagCountMessage, 7, repeated=True)


class DistinctChannelMessage(messages.Message):
    """
        Message to represent a channel id/name
    """
    id = messages.StringField(1)
    name = messages.StringField(2)


class DistinctChannelListResponse(messages.Message):
    """
        Message to represent a list of distinct channels
    """
    items = messages.MessageField(
        DistinctChannelMessage, 1, repeated=True)
    is_list = messages.BooleanField(2)

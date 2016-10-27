"""
    Mapper classes for the video tag API
"""
from greenday_core.models import VideoTagInstance, VideoTag, ProjectTag

from ..mapper import GeneralMapper
from .messages import VideoTagInstanceResponseMessage, ProjectTagResponseMessage


class ProjectTagMapper(GeneralMapper):
    """
        Mapper class to map any
        :class:`ProjectTag <greenday_core.models.tag.ProjectTag>` entity
    """
    def __init__(self, message_type):
        """
            Creates mapper

            message_type: The response message to be returned
        """
        model_type = ProjectTag
        super(ProjectTagMapper, self).__init__(
            model_type, message_type)

    def get_message_field_value(self, obj, message_field_name):
        """
            Custom mapping behaviour
        """
        if message_field_name in ('name', 'description', 'image_url'):
            return getattr(obj.global_tag, message_field_name)

        return super(ProjectTagMapper, self).get_message_field_value(
            obj, message_field_name)


class VideoTagInstanceMapper(GeneralMapper):
    """
        Mapper class to map any
        :class:`VideoTagInstance <greenday_core.models.tag.VideoTagInstance>` entity
    """
    def __init__(self, message_type):
        """
            Creates mapper

            message_type: The response message to be returned
        """
        model_type = VideoTagInstance
        super(VideoTagInstanceMapper, self).__init__(
            model_type, message_type)

    def get_message_field_value(self, obj, message_field_name):
        """
            Custom mapping behaviour
        """
        if message_field_name == 'global_tag_id':
            return obj.video_tag.project_tag.global_tag_id

        if message_field_name == 'project_tag_id':
            return obj.video_tag.project_tag_id

        if message_field_name == 'youtube_id':
            return obj.video.youtube_id

        if message_field_name == 'project_id':
            return obj.video.project_id

        return super(VideoTagInstanceMapper, self).get_message_field_value(
            obj, message_field_name)


class VideoTagMapper(GeneralMapper):
    """
        Mapper class to map any
        :class:`VideoTag <greenday_core.models.tag.VideoTag>` entity
    """
    def __init__(self, message_type):
        """
            Creates mapper

            message_type: The response message to be returned
        """
        model_type = VideoTag
        self.instance_mapper = VideoTagInstanceMapper(
            VideoTagInstanceResponseMessage)
        self.project_tag_mapper = ProjectTagMapper(
            ProjectTagResponseMessage)

        super(VideoTagMapper, self).__init__(
            model_type, message_type)

    def get_message_field_value(self, obj, message_field_name):
        """
            Custom mapping behaviour
        """
        if message_field_name == 'youtube_id':
            return obj.video.youtube_id

        if message_field_name == 'project_tag':
            return self.project_tag_mapper.map(obj.project_tag)

        if message_field_name == "instances":
            instances = []
            for tag_instance in obj.tag_instances.all():
                tag_instance.video = obj.video
                instances.append(self.instance_mapper.map(tag_instance))
            return instances

        return super(VideoTagMapper, self).get_message_field_value(
            obj, message_field_name)

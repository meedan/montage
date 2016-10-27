"""
    Defines mappers for the project tag API
"""
from greenday_core.models import ProjectTag

from ..mapper import GeneralMapper


class ProjectTagMapper(GeneralMapper):
    """
        Mapper class to map
        :class:`ProjectTag <greenday_core.models.tag.ProjectTag>`
        entities
    """
    def __init__(self, message_type):
        """
            Creates mapper.

            message_type: The response message to be returned
        """
        model_type = ProjectTag
        super(ProjectTagMapper, self).__init__(
            model_type, message_type)

    def get_message_field_value(self, obj, message_field_name):
        """
            Custom mapping behaviour
        """
        if message_field_name in ('name', 'description', 'image_url',):
            # get value from GlobalTag
            return getattr(obj.global_tag, message_field_name)

        if message_field_name == 'parent_id':
            parent = obj.get_parent()
            return parent.pk if parent else None

        if message_field_name == 'video_tag_instance_count':
            return obj.taginstance_sum

        return super(ProjectTagMapper, self).get_message_field_value(
            obj, message_field_name)

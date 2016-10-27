"""
    Tag API mappers
"""
from ..mapper import GeneralMapper
from .messages import TagResponseMessage


class TagMapper(GeneralMapper):
    """
        Custom TagMapper to map any
        :class:`GlobalTag <greenday_core.models.tag.GlobalTag>`
        entity to a
        :class:`TagResponseMessage <greenday_api.tag.messages.TagResponseMessage>`
    """
    def __init__(self, *args, **kwargs):
        """
            Creates mapper
        """
        super(TagMapper, self).__init__(
            None, TagResponseMessage)

    def get_message_field_value(
            self, obj, message_field_name, project_id=None):
        """
            Override so that we can suitably cast id and user_id
            from their response format (which is a string from the AtomField)
            to int format.
        """
        if message_field_name in ("id", "user_id",):
            return int(getattr(obj, message_field_name) or 0)

        if message_field_name == "project_id":
            if project_id and obj.project_ids and (
               project_id in [int(pid) for pid in obj.project_ids.split(" ")]):
                return project_id

        return super(TagMapper, self).get_message_field_value(
            obj, message_field_name)

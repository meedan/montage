"""
    Defines mapper classes for the OneSearch API
"""
from greenday_core.models import Video
from ..video.mappers import VideoMapper
from ..video.utils import format_date, format_duration
from ..mapper import GeneralMapper
from .messages import (
    OneSearchProjectResponseMessage, OneSearchVideoResponseMessage,
    OneSearchAdvancedVideoResponseMessage
)


# OneSearchProject searcg mapper
class OneSearchProjectIndexMapper(GeneralMapper):
    """
        Custom mapper to map project documents from
        appengine search API
    """
    def __init__(self, *args, **kwargs):
        super(OneSearchProjectIndexMapper, self).__init__(
            None, OneSearchProjectResponseMessage)

    def get_message_field_value(self, obj, message_field_name):
        """
            Override so that we can suitably cast id and owner_id
            from their response format (which is a string from the AtomField)
            to int format.
        """
        if message_field_name in ("id", "owner_id",):
            return int(getattr(obj, message_field_name) or 0)
        return super(
            OneSearchProjectIndexMapper, self).get_message_field_value(
                obj, message_field_name)


# OneSearchVideo search mapper
class OneSearchVideoIndexMapper(GeneralMapper):
    """
        Custom mapper to map project documents from
        appengine video API
    """
    def __init__(self, *args, **kwargs):
        super(OneSearchVideoIndexMapper, self).__init__(
            None, OneSearchVideoResponseMessage)

    def get_message_field_value(self, obj, message_field_name):
        """
            Override so that we can suitably cast id, project_ID,
            and channel_id

            from their response format (which is a string from the AtomField)
            to int format.
        """
        if message_field_name in ("id", "project_id",):
            return int(getattr(obj, message_field_name) or 0)

        if message_field_name == 'pretty_duration':
            return format_duration(getattr(obj, 'duration'))

        if message_field_name == 'pretty_publish_date':
            return format_date(getattr(obj, 'publish_date'))

        return super(OneSearchVideoIndexMapper, self).get_message_field_value(
            obj, message_field_name)


# onesearch video mapper
class OneSearchVideoFilterMapper(VideoMapper):
    """
        Custom mapper to map a
        :class:`Video <greenday_core.models.video.Video>`
        to a response message

        Subclasses the video filter mapper for the time being as the
        responses are identitical. If either response branches off and becomes
        more unique, then this class should extend GeneralMapper instead and
        define its own OneSearch specific mapping logic.
    """
    def __init__(self, *args, **kwargs):
        super(OneSearchVideoFilterMapper, self).__init__(
            model=Video, message_cls=OneSearchAdvancedVideoResponseMessage)

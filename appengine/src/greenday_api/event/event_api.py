"""
    Defines the Events API
"""
# FRAMEWORK
import endpoints
import datetime
from protorpc import messages as api_messages
from django.contrib.auth import get_user_model

# GREENDAY
from greenday_core.api_exceptions import UnauthorizedException
from greenday_core.constants import EventKind
from greenday_core.models import (
    Event,
    Project,
    Video,
    VideoCollection
)
from greenday_core import eventbus

from ..project.mappers import ProjectMapper

from ..mapper import GeneralMapper
from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required
)
from ..comment.mappers import CommentMapper
from ..comment.messages import CommentResponseMessageSlim
from ..project.messages import ProjectResponseMessageBasic
from ..user.messages import UserResponseBasic
from ..video.messages import (
    CollectionResponseMessageSkinny,
    VideoResponseMessage
)

from .messages import EventResponseMessage, EventListResponse

EventRequestContainer = endpoints.ResourceContainer(
    api_messages.Message,

    # UTC timestamp in seconds since epoch
    ts=api_messages.IntegerField(2, required=True),
    id=api_messages.IntegerField(3, variant=api_messages.Variant.INT32),
    kind=api_messages.IntegerField(4, variant=api_messages.Variant.INT32),
    project_id=api_messages.IntegerField(5, variant=api_messages.Variant.INT32)
)


@greenday_api.api_class(
    resource_name='event', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class EventAPI(BaseAPI):
    """
        API for application events

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        """
            Creates the API. Instantiates mapper classes.
        """
        super(EventAPI, self).__init__(*args, **kwargs)

        self.event_mapper = GeneralMapper(Event, EventResponseMessage)
        self.project_mapper = ProjectMapper(
            Project, ProjectResponseMessageBasic)
        self.user_mapper = GeneralMapper(get_user_model(), UserResponseBasic)
        self.video_mapper = GeneralMapper(Video, VideoResponseMessage)
        self.video_collection_mapper = GeneralMapper(
            VideoCollection, CollectionResponseMessageSkinny)
        self.comment_mapper = CommentMapper(CommentResponseMessageSlim)

    @greenday_method(EventRequestContainer, EventListResponse,
                      path='event', http_method='GET', name='list',
                      pre_middlewares=[auth_required])
    def event_list(self, request):
        """
            Lists application events.

            Returns events along with the associated objects in separate lists
        """
        timestamp = datetime.datetime.utcfromtimestamp(request.ts)

        kind = EventKind(request.kind) if request.kind else None

        events, objects = eventbus.get_events_with_objects(
            timestamp,
            kind=kind,
            object_id=request.id,
            project_id=request.project_id
        )

        message_args = {
            'events': map(self.event_mapper.map, events),
            'projects': map(self.project_mapper.map, objects['project']),
            'users': map(self.user_mapper.map, objects['user']),
            'videos': map(self.video_mapper.map, objects['video']),
            'video_collections': map(
                self.video_collection_mapper.map, objects['video_collection']),
            'project_comments': map(self.comment_mapper.map, objects['project_comment'])
        }

        return EventListResponse(**message_args)

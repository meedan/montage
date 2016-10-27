"""
    Functionity related to the recording and publishing of
    application events
"""
# import python deps
import functools
import logging
from collections import Iterable

from google.appengine.api import taskqueue

# FRAMEWORK
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils.functional import SimpleLazyObject

# GREENDAY
from .models import (
    Event,
    Project,
    Video,
    VideoCollection,
    PendingUser,
    ProjectComment,
    TimedVideoComment
)
from .constants import EventModel, EventCommonCodes, CODES_PER_MODEL

# import django deps
from django.utils import timezone


def noop(*args):  # pragma: no cover
    pass


EVENT_KIND_MODEL_TO_MODEL = SimpleLazyObject(lambda: {
    EventModel.PROJECT: Project.objects,
    EventModel.VIDEO: Video.objects.select_related("youtube_video"),
    EventModel.USER: get_user_model().objects,
    EventModel.VIDEO_COLLECTION: VideoCollection.objects,
    EventModel.PENDINGUSER: PendingUser.objects,
    EventModel.PROJECT_COMMENT: ProjectComment.objects.select_related('user'),
    EventModel.PROJECT_COMMENT_REPLY: ProjectComment.objects.select_related('user'),
    EventModel.TIMED_VIDEO_COMMENT: TimedVideoComment.objects.select_related('user'),
    EventModel.TIMED_VIDEO_COMMENT_REPLY: TimedVideoComment.objects.select_related('user')
})


class EventDecorator(object):
    """
        Decorate a method to record an event

        @appevent(constants.EventKind.Foo, id_getter=lambda id=None: id)
        def foo(id=None):
            ...
    """

    def __init__(
            self,
            kind,
            id_getter=None,
            project_id_getter=None,
            video_id_getter=None,
            meta_getter=None,
            user_getter=None,
            id_getter_post=None,
            project_id_getter_post=None,
            video_id_getter_post=None,
            meta_getter_post=None,
            user_getter_post=None,
            *args,
            **kwargs):
        self.kind = kind

        self.id_getter = id_getter or noop
        self.project_id_getter = project_id_getter or noop
        self.video_id_getter = video_id_getter or noop
        self.meta_getter = meta_getter or noop
        self.user_getter = user_getter or noop

        self.id_getter_post = id_getter_post or noop
        self.project_id_getter_post = project_id_getter_post or noop
        self.video_id_getter_post = video_id_getter_post or noop
        self.meta_getter_post = meta_getter_post or noop
        self.user_getter_post = user_getter_post or noop

    def __call__(self, fn):
        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            # evaluate values before request is handled
            object_id = self.id_getter(*args, **kwargs)
            project_id = self.project_id_getter(
                *args, **kwargs)
            video_id = self.video_id_getter(
                *args, **kwargs)
            meta = self.meta_getter(*args, **kwargs)
            user = self.user_getter(*args, **kwargs)

            ret = fn(*args, **kwargs)

            post_args = args + (ret,)

            # evaluate _post values after the request is handled
            object_id = object_id or self.id_getter_post(*post_args, **kwargs)
            project_id = project_id or self.project_id_getter_post(
                *post_args, **kwargs)
            video_id = video_id or self.video_id_getter_post(
                *post_args, **kwargs)
            meta = meta or self.meta_getter_post(*post_args, **kwargs)
            user = user or self.user_getter_post(*post_args, **kwargs)

            # check if we are working with a batch request. If we are then
            # object_id will be iterable.
            if isinstance(object_id, Iterable):
                for obj in object_id:
                    try:
                        publish_appevent(
                            self.kind,
                            object_id=obj,
                            project_id=project_id,
                            video_id=video_id,
                            meta=meta,
                            user=user)
                    except Exception as e:  # pragma: no cover
                        logging.exception(e)
            else:
                try:
                    publish_appevent(
                        self.kind,
                        object_id=object_id,
                        project_id=project_id,
                        video_id=video_id,
                        meta=meta,
                        user=user)
                except Exception as e:  # pragma: no cover
                    logging.exception(e)
            return ret
        return decorated


appevent = EventDecorator


def publish_appevent(
        kind,
        **kwargs):
    """
        Creates an application event object
    """
    event = Event.objects.create(
        timestamp=timezone.now(),
        kind=kind.value,
        **kwargs
    )

    taskqueue.add(
        url=reverse(
            "channel:publish_event_task",
            kwargs={"event_id": event.pk}),
        queue_name="publish-event",
        countdown=1
    )


def get_event(event_id):
    """
        Gets an event by its ID along with the model for which it
        was recorded
    """
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return None, None

    model_enum = EventModel(event.kind / CODES_PER_MODEL)
    if event.object_id and model_enum in EVENT_KIND_MODEL_TO_MODEL:
        qs = EVENT_KIND_MODEL_TO_MODEL[model_enum]
        try:
            model = qs.get(pk=event.object_id)
        except qs.model.DoesNotExist:
            model = None
    else:
        model = None

    return event, model


def get_events(
        timestamp,
        kind=None,
        object_id=None,
        project_id=None,
        event_kind=None,
        object_kind=None):
    """
        Gets a list of filtered application events
    """
    qry = Event.objects.filter(timestamp__gte=timestamp)

    if kind is not None:
        if hasattr(kind, '__iter__'):
            qry = qry.filter(kind__in=[k.value for k in kind])
        else:
            qry = qry.filter(kind=kind.value)
    else:
        if event_kind is not None:
            if not isinstance(event_kind, EventCommonCodes):
                event_kind = EventCommonCodes(event_kind)
            qry = qry.filter(event_kind=event_kind.value)
        if object_kind is not None:
            if not isinstance(object_kind, EventModel):
                object_kind = EventCommonCodes(object_kind)
            qry = qry.filter(object_kind=object_kind.value)

    if project_id:
        qry = qry.filter(project_id=project_id)

    if object_id:
        qry = qry.filter(object_id=object_id)

    return qry


def get_events_with_objects(*args, **kwargs):
    """
        Gets application events grouped by the event model and returns the
        related objects

        Takes same arguments as get_events()
    """
    events = get_events(*args, **kwargs)

    model_ids = {
        EventModel[enum].value: set() for enum in EventModel.__members__}

    for event in events:
        model_enum_value, event_code = divmod(event.kind, CODES_PER_MODEL)
        model_enum = EventModel(model_enum_value)

        if event.object_id and model_enum in EVENT_KIND_MODEL_TO_MODEL:
            model_ids[model_enum].add(event.object_id)

    models = {}
    for model_enum_value, object_ids in model_ids.items():
        model_enum = EventModel(model_enum_value)
        qs = EVENT_KIND_MODEL_TO_MODEL[model_enum]

        models[model_enum.name.lower()] = list(qs.filter(
            pk__in=object_ids))

    return events, models


def get_event_counts(*args, **kwargs):
    """
        Gets a count of application events grouped by the event model

        Takes same arguments as get_events()
    """
    events = (
        get_events(*args, **kwargs)
        .values("object_kind")
        .annotate(Count("object_kind"))
    )

    return {
        EventModel(object_aggr["object_kind"]).name.lower():
            object_aggr["object_kind__count"]
        for object_aggr in events
    }

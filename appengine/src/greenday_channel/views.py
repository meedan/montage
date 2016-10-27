"""
    Defines request handlers for the channels package
"""
from django.http import (
    HttpResponse,
    Http404
)
from django.views.decorators.csrf import csrf_exempt

from greenday_core.eventbus import get_event
from greenday_api.event.utils import get_model_message

from .channel import GreendayChannelManager


def _get_project_channel(channels):
    return next(
        (c.lstrip('projectid-') for c in channels
            if c.startswith('projectid-')),
        None)


@csrf_exempt
def publish_event_task_handler(request, event_id=None):
    """
        Task handler to push an event out to all necessary channels
    """
    event, model = get_event(event_id)

    if not event:
        raise Http404

    if model:
        model_dict = get_model_message(event, model)
    else:
        model_dict = None

    if event.video_id:
        channel = "videoid-{0}".format(event.video_id)
    elif event.project_id:
        # only publish project messages if there isn't a video ID
        channel = "projectid-{0}".format(event.project_id)
    else:
        channel = "generic"

    manager = GreendayChannelManager(channels=[channel])

    manager.publish_message({
        "event": event.to_dict(),
        "model": model_dict
    })

    return HttpResponse()

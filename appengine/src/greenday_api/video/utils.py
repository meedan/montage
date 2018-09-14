"""
    Utils module for video API
"""
from datetime import timedelta

from .messages import BatchVideoResponseMessage


def make_batch_response_message(
        youtube_id, not_found=False, forbidden=False, success=False, error=False):
    """
        Creates a response item for a batch request indicating the status of a
        single item processed in the request
    """
    assert sum(map(int, [not_found, forbidden, success, bool(error)])) == 1, "Exactly one of not_found, forbidden, success, error must be passed"

    if not_found:
        message = 'Video with youtube_id %s does not exist' % youtube_id
    elif forbidden:
        message = 'Permission Denied!'
    elif success:
        message = 'ok'
    elif error:
        message = error
    else:
        raise Exception

    return BatchVideoResponseMessage(
        youtube_id=youtube_id or "", success=success, msg=message)


def has_video_search_args(request):
    """
        Returns whether the object has any video search filter args in it
    """
    search_kws = (
        "q",
        "location",
        "channel_ids",
        "collection_id",
        "tag_ids",
        "date",)

    for kw in search_kws:
        if getattr(request, kw, None) is not None:
            return True


def format_duration(duration):
    """
        Formats passed duration in total seconds into a format that the front
        end can display without the need for filters or directives.
    """
    sequence = []
    duration = timedelta(seconds=duration)
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        sequence.append(u'%s' % hours)

    if minutes < 10:
        sequence.append(u'0%s' % minutes)
    else:
        sequence.append(u'%s' % minutes)

    if seconds < 10:
        sequence.append(u'0%s' % seconds)
    else:
        sequence.append(u'%s' % seconds)

    return u':'.join(sequence)


def format_date(date):
    """
        Formats passed date in datetime into a format that the front
        end can display without the need for filters or directives.
    """
    if date:
        return date.strftime("%b %d, %Y")

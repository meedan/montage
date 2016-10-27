"""
    Provides various utility methods for the channels package
"""
import logging
import time

from google.appengine.runtime.apiproxy_errors import DeadlineExceededError

from django.core.exceptions import PermissionDenied

from greenday_core.models import Video, Project


def retry_until_truthy(fn, max_retries=100, sleep=0.1, args=(), kwargs=None):
    """
        Retries the given method until it returns a truthy value or max_retries is hit
    """
    kwargs = kwargs or {}

    retries = 0
    while retries < max_retries:
        retries += 1

        try:
            ret = fn(*args, **kwargs)
        except DeadlineExceededError:
            logging.warning("Got DeadlineExceededError whilst executing %s", fn)
            ret = None

        if ret:
            return ret

        if sleep:
            time.sleep(sleep)


def clean_channels(user, channels):
    """
        Raises a PermissionDenied error if the user cannot access any channel

        Returns a list of valid channels
    """
    valid_channels = []
    can_access_projects = []

    def _check_project(project):
        if project.id in can_access_projects:
            return True

        if user.is_superuser or project.is_assigned(user):
            can_access_projects.append(project.id)
            return True

        raise PermissionDenied

    for channel in channels:
        if channel.startswith('projectid'):
            project_id = channel.lstrip('projectid-')
            try:
                project = Project.objects.get(pk=project_id)
            except Project.DoesNotExist:
                continue

            _check_project(project)

        elif channel.startswith('videoid'):
            video_id = channel.lstrip('videoid-')
            try:
                video = Video.objects.get(pk=video_id)
            except Video.DoesNotExist:
                continue

            _check_project(video.project)

        valid_channels.append(channel)

    return valid_channels




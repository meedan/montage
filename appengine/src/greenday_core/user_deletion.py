"""
    User deletion functionality
"""
import datetime
import logging

from google.appengine.ext import deferred
from django.contrib.auth import get_user_model
from django.utils import timezone
import deferred_manager

from .constants import EventKind
from .eventbus import publish_appevent
from .email_templates import USER_DELETED
from .models import get_sentinel_user
from .utils import send_email


def delete_storyful_optouts(optout_users):
    """
    deferred tasks to remove users who opted out of being migrated to Storyful
    """
    User = get_user_model()
    optouts = User.objects.filter(email__in=optout_users)
    for user in optouts:
        delete_user(user.id, deleted_by_user_id=None, email_user=False)


def defer_delete_user(user, deleted_by_user=None, email_user=True):
    """
        Calls :func:`greenday_core.user_deletion.delete_user <greenday_core.user_deletion.delete_user>`
        via a deferred task
    """
    deferred_manager.defer(
        delete_user,
        user.pk,
        deleted_by_user_id=deleted_by_user.pk if deleted_by_user else None,
        email_user=email_user,
        task_reference="user-{0:d}".format(user.pk),
        unique_until=timezone.now() + datetime.timedelta(hours=2),
        _queue="user-deletion")


def delete_user(user_id, deleted_by_user_id=None, email_user=True):
    """
        Deletes the given user and emails them when complete
    """
    if user_id == deleted_by_user_id:
        deleted_by_user_id = None

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logging.warning(
            "User {0:d} does not exist. Cannot delete.".format(user_id))
        raise deferred.PermanentTaskFailure

    user.delete()

    deleted_by_user = None
    if deleted_by_user_id:
        try:
            deleted_by_user = User.objects.get(pk=deleted_by_user_id)
        except:
            pass

    publish_appevent(
        EventKind.USERDELETED,
        object_id=user_id,
        user=deleted_by_user or get_sentinel_user()
    )

    if email_user:
        send_email(
            "Your Montage account has been deleted",
            USER_DELETED,
            user.email)

    logging.info("User {0:d} ({1}) deleted".format(user_id, user.email))

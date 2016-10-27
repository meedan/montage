"""
    Defines utilities and decorators related to user authentication

    Much of this will be redundant when the app is released to the public
"""
import logging
import functools
from google.appengine.api import urlfetch
import json
import copy

from google.appengine.api import users

from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.conf import settings

from greenday_core.models import PendingUser


def auth_user(fn):
    """
        Decorator to force user to be logged in with GAE
    """
    @functools.wraps(fn)
    def _wrapped(request, *args, **kwargs):
        temp_request = request
        bearer = request.META['HTTP_AUTHORIZATION']
        url = "https://www.googleapis.com/userinfo/v2/me"
        result = urlfetch.fetch(url=url,
            method=urlfetch.GET,
            headers={"Authorization" : bearer})
        contents = json.loads(result.content)
        gae_user = users.get_current_user()
        is_admin = users.is_current_user_admin()

        User = get_user_model()
        django_user = None
        try:
            logging.debug("Getting django user")
            django_user = User.objects.get(
                email=contents['email'])
        except User.DoesNotExist:
            logging.info("User does not exist in Montage. Checking pending users")
            try:
                pending_user = PendingUser.objects.get(
                    email=contents['email'])
            except PendingUser.DoesNotExist:
                logging.info("No pending user record for this email")
                user, created = get_user_model().objects.get_or_create(
                    email=email,
                    defaults={
                        'username': email.split('@')[0],
                        'is_active': True
                    }
                )
                return user
            else:
                logging.info("Pending user record found. Activating user.")
                django_user = activate_pending_user(
                    pending_user, gae_user, is_admin)
        except AttributeError:
            return HttpResponseForbidden()

        else:
            logging.info("User found. Updating gaia_id and superuser status")
            request = temp_request
            # update_user(django_user, is_admin)

        if django_user:
            request.user = django_user
        else:
            return HttpResponseForbidden()

        return fn(request, *args, **kwargs)
    return _wrapped


def update_user(django_user, is_admin):
    """
        Updates the system user with information from the users API
    """
    updated = False

    # if django_user.gaia_id != gae_user.user_id():
    #     django_user.gaia_id = gae_user.user_id()
    #     updated = True

    # update admin status
    if is_admin and not django_user.is_superuser:
        django_user.is_superuser = True
        updated = True
    elif not is_admin and django_user.is_superuser:
        django_user.is_superuser = False
        updated = True

    if updated:
        django_user.save()


def activate_pending_user(pending_user, gae_user, is_admin):
    """
        Converts a pending user into a full user
    """
    logging.info("Activating pending user {0}".format(pending_user.email))
    user = create_user(gae_user, is_admin, pending_user.is_whitelisted)
    logging.info("Created new user object for {0}".format(gae_user.email))

    count = pending_user.projectusers.update(user=user, is_pending=True)
    logging.info("Activated pending user on {0} projects".format(count))
    pending_user.delete()
    logging.info("Deleted pending user account for {0}".format(
        pending_user.email))

    user.gaia_id = gae_user.user_id()
    user.save()

    return user


def create_user(gae_user, is_admin, is_whitelisted):
    """
        Creates a new user from a users API object
    """
    return get_user_model().objects.create(
        username=gae_user.user_id(),
        email=gae_user.email(),
        is_active=True,
        is_superuser=is_admin,
        is_whitelisted=is_whitelisted
    )

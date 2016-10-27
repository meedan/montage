"""
Experiment to see if Endpoints will be able to serve the channels functionality
"""

import endpoints
import json
from protorpc import remote

from google.appengine.runtime import DeadlineExceededError

from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import PermissionDenied

from greenday_api.api import greenday_api
from greenday_core.api_exceptions import (
    ForbiddenException,
    InternalServerErrorException,
    BadRequestException
)

from ..channel import GreendayChannelManager
from ..onlinecollaborators import OnlineCollaboratorsManager
from ..utils import clean_channels

from .containers import TokenRequestContainer, ChannelRequestContainer
from .messages import ChannelResponseMessage, SubscribeResponseMessage


@greenday_api.api_class(
    resource_name='channel', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class ChannelsAPI(remote.Service):
    """
        API for channels
    """

    @endpoints.method(
        TokenRequestContainer,
        ChannelResponseMessage,
        path='channels/pull',
        http_method='GET')
    def pull(self, request):
        """
        Pops the latest messages off the queue for the given client token
        """
        get_current_user()

        channels = request.channels.split(',')

        manager = GreendayChannelManager(channels=channels)

        try:
            messages = manager.pop_messages(request.token)

            project_channel = _get_project_channel(channels)
            if project_channel:
                online_collaborator_manager = OnlineCollaboratorsManager(
                        project_channel.lstrip('projectid-'))
                online_collaborator_manager.refresh_collaborator(request.token)
                online_collaborator_manager.purge_expired_collaborators()

        except DeadlineExceededError:
            # swallow DeadlineExceededError - client will retry
            return ChannelResponseMessage()

        if messages is False:
            # internal loop exhausted
            return ChannelResponseMessage()
        else:
            return ChannelResponseMessage(items=json.dumps(messages, cls=DjangoJSONEncoder))

    @endpoints.method(
        ChannelRequestContainer,
        SubscribeResponseMessage,
        path='channels/subscribe',
        http_method='POST')
    def subscribe(self, request):
        """
            Creates a client in memcache which will have events published to it
        """
        user = get_current_user()

        try:
            channels = clean_channels(user, request.channels.split(','))
        except PermissionDenied:
            raise ForbiddenException

        if not channels:
            raise BadRequestException

        manager = GreendayChannelManager(channels=channels)

        new_token = manager.create_client_token()

        project_channel = _get_project_channel(channels)
        if project_channel:
            online_collaborator_manager = OnlineCollaboratorsManager(
                project_channel)
            online_collaborator_manager.add_collaborator(user, new_token)

        if manager.add_client(new_token):
            return SubscribeResponseMessage(
                token=new_token,
                channels=channels
            )
        else:
            # internal loop exhausted
            raise InternalServerErrorException(
                "Failed to subscribe. Please retry")

    @endpoints.method(
        TokenRequestContainer,
        SubscribeResponseMessage,
        path='channels/unsubscribe',
        http_method='POST')
    def unsubscribe(self, request):
        """
            Removes a subscribed client
        """
        get_current_user()

        channels = request.channels.split(',')

        project_channel = _get_project_channel(channels)
        if project_channel:
            online_collaborator_manager = OnlineCollaboratorsManager(
                project_channel)
            online_collaborator_manager.remove_collaborator(request.token)

        manager = GreendayChannelManager(channels=channels)
        manager.remove_client(request.token)

        return SubscribeResponseMessage(
            token=None,
            channels=channels
        )

def get_current_user():
    current_user = endpoints.get_current_user()
    if not current_user:
        raise ForbiddenException
    else:
        User = get_user_model()
        try:
            return User.objects.get(email=current_user.email())
        except User.DoesNotExist:
            raise ForbiddenException


def _get_project_channel(channels):
    return next(
        (c.lstrip('projectid-') for c in channels
            if c.startswith('projectid-')),
        None)

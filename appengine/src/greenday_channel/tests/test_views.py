"""
    Tests for :mod:`greenday_channel.views <greenday_channel.views>`
"""
import os
import json
import signal
from milkman.dairy import milkman

from google.appengine.api import memcache

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import timezone

from greenday_core.api_exceptions import (
    ForbiddenException,
    BadRequestException
)
from greenday_core.constants import EventKind
from greenday_core.models import (
    Event,
    Project,
    ProjectComment,
    TimedVideoComment)
from greenday_core.tests.base import AppengineTestBed

from greenday_api.tests.base import ApiTestCase

from ..endpoints_api.api import ChannelsAPI
from ..endpoints_api.containers import (
    TokenRequestContainer,
    ChannelRequestContainer
)
from ..channel import GreendayChannelManager


def subscribe(channel):
    """
        Helper method to get a subscription token for a given channel
    """
    manager = GreendayChannelManager(channels=[channel])
    token = manager.create_client_token()
    manager.add_client(token)
    return token


def publish(channel, data):
    """
        Helper method to publish data to a given channel
    """
    manager = GreendayChannelManager(channels=[channel])
    manager.publish_message(data)


class PublishEventHandlerViewTestCase(AppengineTestBed):
    """
        Tests for :func:`greenday_channel.views.publish_event_task <greenday_channel.views.publish_event_task>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(PublishEventHandlerViewTestCase, self).setUp()

        self.project = milkman.deliver(Project)

        User = get_user_model()
        self.user = milkman.deliver(
            User,
            email="user@example.com")

    def assertEvent(self, event, message):
        """
            Assert that the given message matches the given event
        """
        self.assertEqual(event.pk, message['event']['id'])
        self.assertEqual(event.object_type, message['event']['object_type'])
        self.assertEqual(event.event_type, message['event']['event_type'])
        self.assertEqual(event.object_id, message['event']['object_id'])
        self.assertEqual(event.project_id, message['event']['project_id'])
        self.assertEqual(event.meta, message['event']['meta'])

    def test_project_comment_event(self):
        """
            Publish a project comment event.

            Check that subscribed channels receive the event
        """
        comment = ProjectComment.add_root(project=self.project, user=self.user)

        event = Event.objects.create(
            kind=EventKind.PROJECTROOTCOMMENTCREATED,
            object_id=comment.pk,
            project_id=self.project.pk,
            meta="foo",
            user=self.user,
            timestamp=timezone.now()
        )

        channel = 'projectid-{0}'.format(self.project.pk)
        token = subscribe(channel)

        url = reverse(
            "channel:publish_event_task",
            kwargs={"event_id": event.pk})

        self.client.post(url)

        messages = memcache.get(token, namespace="channel-buckets")
        self.assertEqual(1, len(messages))

        message = messages[0]['message']
        self.assertEvent(event, message)

        self.assertEqual(comment.pk, message['model']['id'])
        self.assertEqual(comment.text, message['model']['text'])
        self.assertTrue(message['model']['created'])
        self.assertEqual(self.user.pk, message['model']['user']['id'])
        self.assertEqual(
            self.user.first_name, message['model']['user']['first_name'])
        self.assertEqual(
            self.user.last_name, message['model']['user']['last_name'])
        self.assertEqual(self.user.email, message['model']['user']['email'])

    def test_video_comment_event(self):
        """
            Publish a video comment event.

            Check that subscribed channels receive the event
        """
        video = self.create_video(project=self.project)
        comment = TimedVideoComment.add_root(
            video=video, user=self.user, start_seconds=42)

        event = Event.objects.create(
            kind=EventKind.TIMEDVIDEOROOTCOMMENTCREATED,
            object_id=comment.pk,
            video_id=video.pk,
            project_id=self.project.pk,
            meta="foo",
            user=self.user,
            timestamp=timezone.now()
        )

        channel = 'videoid-{0}'.format(video.pk)
        token = subscribe(channel)

        url = reverse(
            "channel:publish_event_task",
            kwargs={"event_id": event.pk})

        self.client.post(url)

        messages = memcache.get(token, namespace="channel-buckets")
        self.assertEqual(1, len(messages))

        message = messages[0]['message']
        self.assertEvent(event, message)

        self.assertEqual(comment.pk, message['model']['id'])
        self.assertEqual(comment.text, message['model']['text'])
        self.assertEqual(
            comment.start_seconds, message['model']['start_seconds'])
        self.assertTrue(message['model']['created'])
        self.assertEqual(self.user.pk, message['model']['user']['id'])
        self.assertEqual(
            self.user.first_name, message['model']['user']['first_name'])
        self.assertEqual(
            self.user.last_name, message['model']['user']['last_name'])
        self.assertEqual(self.user.email, message['model']['user']['email'])

    def test_event_missing(self):
        """
            Call the event publisher with an event ID that
            does not relate to an event in the database
        """
        url = reverse(
            "channel:publish_event_task",
            kwargs={"event_id": 99999})

        response = self.client.post(url)

        self.assertEqual(404, response.status_code)

    def test_model_missing(self):
        """
            The PROJECTCOMMENTDELETED event in the database references a
            project comment which is deleted
        """
        event = Event.objects.create(
            kind=EventKind.PROJECTCOMMENTDELETED,
            object_id=99999,
            project_id=self.project.pk,
            meta="foo",
            user=self.user,
            timestamp=timezone.now()
        )

        channel = 'projectid-{0}'.format(self.project.pk)
        token = subscribe(channel)

        url = reverse(
            "channel:publish_event_task",
            kwargs={"event_id": event.pk})

        self.client.post(url)

        messages = memcache.get(token, namespace="channel-buckets")
        self.assertEqual(1, len(messages))

        message = messages[0]['message']
        self.assertEvent(event, message)
        self.assertFalse(message['model'])


class PullViewTestCase(ApiTestCase):
    """
        Tests for :func:`greenday_channel.endpoints_api.api.ChannelsAPI.pull <Tests for :func:`greenday_channel.endpoints_api.api.ChannelsAPI.pull>`
    """
    api_type = ChannelsAPI

    def test_ok(self):
        """
            Long poll request for events on a given channel
        """
        self._sign_in(self.user)

        channel = 'dummy-channel'
        token = subscribe(channel)

        data = {"foo": 42}
        publish(channel, data)

        request = TokenRequestContainer.combined_message_class(
            token=token, channels=channel)

        response = self.api.pull(request)
        self.assertEqual(data, json.loads(response.items)[0]['message'])

        # check that a subsequent call doesn't return
        # adding a manual timeout here so that it doesn't stall the tests
        class TimeoutError(Exception):
            pass

        def handler(*args):
            raise TimeoutError

        signal.signal(signal.SIGALRM, handler)
        signal.alarm(1) # wait for 1 sec

        try:
            self.assertRaises(TimeoutError, self.api.pull, request)
        finally:
            signal.alarm(0)


class SubscribeViewTestCase(ApiTestCase):
    """
        Tests for :func:`greenday_channel.endpoints_api.api.ChannelsAPI.subscribe <greenday_channel.endpoints_api.api.ChannelsAPI.subscribe>`
    """
    api_type = ChannelsAPI

    def test_ok(self):
        """
            Subscribe to a channel
        """
        project = milkman.deliver(Project)
        channel = 'projectid-{0}'.format(project.pk)

        self._sign_in(self.user)

        project.add_assigned(self.user, pending=False)

        request = ChannelRequestContainer.combined_message_class(
            channels=channel)
        response = self.api.subscribe(request)

        channel_clients = memcache.get(channel, namespace="channel-clients")
        self.assertIn(response.token, channel_clients)

        self.assertEqual([channel], response.channels)

    def test_no_token(self):
        """
            Subscribe to a channel without passing an oauth token
        """
        request = ChannelRequestContainer.combined_message_class(
            channels='')
        self.assertRaises(ForbiddenException, self.api.subscribe, request)

    def test_forbidden(self):
        """
            Subscribe to a channel passing an oauth token which does
            not relate to a Montage user
        """
        os.environ['ENDPOINTS_AUTH_EMAIL'] = "invalid@example.com"
        os.environ['ENDPOINTS_AUTH_DOMAIN'] = "@example.com"

        request = ChannelRequestContainer.combined_message_class(
            channels='')
        self.assertRaises(ForbiddenException, self.api.subscribe, request)

    def test_invalid_channel(self):
        """
            Subscribe to a project channel for a project ID that does
            not exist
        """
        channel = 'projectid-99999'

        self._sign_in(self.user)

        request = ChannelRequestContainer.combined_message_class(
            channels=channel)
        self.assertRaises(BadRequestException, self.api.subscribe, request)

    def test_user_not_assigned_to_project(self):
        """
            Subscribe to a project channel where the user has no access
            to the project
        """
        project = milkman.deliver(Project)
        channel = 'projectid-{0}'.format(project.pk)

        self._sign_in(self.user)

        request = ChannelRequestContainer.combined_message_class(
            channels=channel)
        self.assertRaises(ForbiddenException, self.api.subscribe, request)


class UnsubscribeViewTestCase(ApiTestCase):
    """
        Tests for :func:`greenday_channel.views.unsubscribe_view <greenday_channel.views.unsubscribe_view>`
    """
    api_type = ChannelsAPI

    def test_ok(self):
        """
            Unsubscribe from a given channel
        """
        self._sign_in(self.user)
        channel = 'dummy-channel'
        token = subscribe(channel)

        request = TokenRequestContainer.combined_message_class(
            token=token, channels=channel)
        response = self.api.unsubscribe(request)

        self.assertFalse(response.token)
        self.assertEqual([channel], response.channels)

        channel_clients = memcache.get(channel, namespace="channel-clients")
        self.assertNotIn(token, channel_clients)

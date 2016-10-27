"""
    Tests for :mod:`greenday_api.event.event_api <greenday_api.event.event_api>`
"""
# LIBRARIES
import datetime
import time
from milkman.dairy import milkman

# FRAMEWORK
from django.contrib.auth import get_user_model
from django.utils import timezone

# GREENDAY
from greenday_core.api_exceptions import UnauthorizedException
from greenday_core.models import (
    Event,
    Project,
    VideoCollection,
    ProjectComment
)
from greenday_core.constants import EventKind

from .base import ApiTestCase
from ..event.event_api import (
    EventAPI,
    EventRequestContainer
)


class GeneralEventAPITests(ApiTestCase):
    """
        Test case for
        :class:`greenday_api.event.event_api.EventAPI <greenday_api.event.event_api.EventAPI>`

        Tests generic events behaviour
    """
    api_type = EventAPI

    def setUp(self):
        """
            Bootstrap with event objects
        """
        super(GeneralEventAPITests, self).setUp()

        self.now = timezone.now()
        self.now_event = milkman.deliver(
            Event, timestamp=self.now,
            kind=EventKind.PROJECTCREATED)
        self.oldish_event = milkman.deliver(
            Event,
            timestamp=self.now-datetime.timedelta(hours=2),
            kind=EventKind.PROJECTCREATED)
        self.very_old_event = milkman.deliver(
            Event,
            timestamp=self.now-datetime.timedelta(days=7),
            kind=EventKind.PROJECTCREATED)

        # timestamp to check against
        since = self.now - datetime.timedelta(hours=3)
        self.ts = long(time.mktime(since.timetuple()))

    def test_not_logged_in(self):
        """
            No signed in user
        """
        request = EventRequestContainer.combined_message_class(
            ts=self.ts)
        self.assertRaises(
            UnauthorizedException, self.api.event_list, request)

    def test_timestamp_only(self):
        """
            All events after a given timestamp
        """
        self._sign_in(self.user)
        request = EventRequestContainer.combined_message_class(
            ts=self.ts)

        with self.assertNumQueries(2):
            response = self.api.event_list(request)

        self.assertEqual(len(response.events), 2)

    def test_kind(self):
        """
            Events of a given kind
        """
        self._sign_in(self.user)
        self.now_event.kind = EventKind.PROJECTUPDATED
        self.now_event.save()

        request = EventRequestContainer.combined_message_class(
            ts=self.ts, kind=EventKind.PROJECTUPDATED)

        with self.assertNumQueries(2):
            response = self.api.event_list(request)

        self.assertEqual(len(response.events), 1)
        self.assertEqual(
            response.events[0].id, self.now_event.pk)

    def test_object_id(self):
        """
            Events for a given object ID
        """
        self._sign_in(self.user)
        self.now_event.object_id = 42
        self.now_event.save()

        request = EventRequestContainer.combined_message_class(
            ts=self.ts, id=42)

        with self.assertNumQueries(3):
            response = self.api.event_list(request)

        self.assertEqual(len(response.events), 1)
        self.assertEqual(
            response.events[0].id, self.now_event.pk)

    def test_project_id(self):
        """
            Events for a given project ID
        """
        self._sign_in(self.user)
        self.now_event.project_id = 42
        self.now_event.save()

        request = EventRequestContainer.combined_message_class(
            ts=self.ts, project_id=42)

        with self.assertNumQueries(2):
            response = self.api.event_list(request)

        self.assertEqual(len(response.events), 1)
        self.assertEqual(
            response.events[0].id, self.now_event.pk)


class SpecificEventAPITests(ApiTestCase):
    """
        Test case for
        :class:`greenday_api.event.event_api.EventAPI <greenday_api.event.event_api.EventAPI>`

        Tests specific event response data
    """
    api_type = EventAPI

    def setUp(self):
        self.now = timezone.now()

        # timestamp to check against
        since = self.now - datetime.timedelta(hours=3)
        self.ts = long(time.mktime(since.timetuple()))
        super(SpecificEventAPITests, self).setUp()

    def test_project_events(self):
        """
            Project events responses
        """
        self._sign_in(self.user)

        project = milkman.deliver(Project)
        project.set_owner(self.user)
        event = milkman.deliver(
            Event,
            timestamp=self.now,
            kind=EventKind.PROJECTCREATED,
            object_id=project.pk
        )

        request = EventRequestContainer.combined_message_class(
            ts=self.ts)

        with self.assertNumQueries(3):
            response = self.api.event_list(request)

        self.assertEqual(len(response.events), 1)
        self.assertEqual(len(response.projects), 1)
        self.assertEqual(response.events[0].id, event.pk)
        self.assertEqual(
            response.projects[0].id, project.pk)

    def test_video_events(self):
        """
            Video events responses
        """
        self._sign_in(self.user)

        video = self.create_video()
        created_event = milkman.deliver(
            Event,
            timestamp=self.now,
            kind=EventKind.VIDEOCREATED,
            object_id=video.pk
        )

        updated_event = milkman.deliver(
            Event,
            timestamp=self.now,
            kind=EventKind.VIDEOUPDATED,
            object_id=video.pk
        )

        video2 = self.create_video()
        created_event2 = milkman.deliver(
            Event,
            timestamp=self.now,
            kind=EventKind.VIDEOCREATED,
            object_id=video2.pk
        )

        request = EventRequestContainer.combined_message_class(
            ts=self.ts)

        with self.assertNumQueries(3):
            response = self.api.event_list(request)

        self.assertEqual(len(response.events), 3)
        self.assertEqual(len(response.videos), 2)
        self.assertEqual(response.events[0].id, created_event2.pk)
        self.assertEqual(response.videos[0].id, video.pk)

    def test_user_events(self):
        """
            User event responses
        """
        self._sign_in(self.user)

        user = milkman.deliver(get_user_model())
        event = milkman.deliver(
            Event,
            timestamp=self.now,
            kind=EventKind.USERCREATED,
            object_id=user.pk
        )

        request = EventRequestContainer.combined_message_class(
            ts=self.ts)

        with self.assertNumQueries(3):
            response = self.api.event_list(request)

        self.assertEqual(len(response.events), 1)
        self.assertEqual(len(response.users), 1)
        self.assertEqual(response.events[0].id, event.pk)
        self.assertEqual(response.users[0].id, user.pk)

    def test_video_collection_events(self):
        """
            Video collection event responses
        """
        self._sign_in(self.user)

        video_collection = milkman.deliver(VideoCollection)
        event = milkman.deliver(
            Event,
            timestamp=self.now,
            kind=EventKind.VIDEOCOLLECTIONCREATED,
            object_id=video_collection.pk
        )

        request = EventRequestContainer.combined_message_class(
            ts=self.ts)

        with self.assertNumQueries(3):
            response = self.api.event_list(request)

        self.assertEqual(len(response.events), 1)
        self.assertEqual(len(response.video_collections), 1)
        self.assertEqual(
            response.events[0].id, event.pk)
        self.assertEqual(
            response.video_collections[0].id,
            video_collection.pk)

    def test_project_comment_events(self):
        """
            Project comment event responses
        """
        self._sign_in(self.user)

        project = milkman.deliver(Project)
        project.set_owner(self.admin)

        root_comment = ProjectComment.add_root(
            project=project, user=self.admin, text="foo")

        event = milkman.deliver(
            Event,
            timestamp=self.now,
            kind=EventKind.PROJECTROOTCOMMENTCREATED,
            object_id=root_comment.pk,
            project_id=project.pk
        )

        request = EventRequestContainer.combined_message_class(
            ts=self.ts)

        with self.assertNumQueries(3):
            response = self.api.event_list(request)

        self.assertEqual(len(response.events), 1)
        self.assertEqual(len(response.project_comments), 1)
        self.assertEqual(
            response.events[0].id, event.pk)
        self.assertEqual(
            response.project_comments[0].id,
            root_comment.pk)

"""
    Tests for
    :func:`greenday_api.project.project_api.ProjectAPI.project_updates_user <greenday_api.project.project_api.ProjectAPI.project_updates_user>`
    and :func:`greenday_api.project.project_api.ProjectAPI.update_last_viewed <greenday_api.project.project_api.ProjectAPI.update_last_viewed>`
"""
# LIBRARIES
import datetime
from milkman.dairy import milkman

# FRAMEWORK
from django.utils import timezone

# GREENDAY
from greenday_core.models import (
    Project,
    Video,
    Event
)
from greenday_core.constants import EventKind

from .base import ApiTestCase, TestEventBusMixin

from ..project.project_api import (
    ProjectAPI,
    ProjectIDContainer
)


class ProjectUpdateTestMixin(object):
    """
        Defines some shared test case methods
    """
    def create_videos(self, count):
        """
            Creates 1 video per hour for the last <count> hours along with a
            created event
        """
        for i in range(1, count):
            video = milkman.deliver(
                Video,
                project=self.project,
                user=self.admin
            )
            yield video

            Event.objects.create(
                timestamp=self.now - datetime.timedelta(hours=i),
                kind=EventKind.VIDEOCREATED,
                project_id=self.project.pk,
                object_id=video.pk
            )

    def users_accept_invite(self, *users):
        """
            Accepts all users invitations to the project
        """
        for u in users:
            projectuser = self.project.get_user_relation(u)
            projectuser.is_pending = False
            projectuser.save()

            Event.objects.create(
                timestamp=self.now - datetime.timedelta(hours=1),
                kind=EventKind.USERACCEPTEDPROJECTINVITE,
                project_id=self.project.pk,
                object_id=u.pk
            )


class ProjectUpdateTests(
        TestEventBusMixin, ProjectUpdateTestMixin, ApiTestCase):
    """
        General tests for
        :func:`greenday_api.project.project_api.ProjectAPI.project_updates_user <greenday_api.project.project_api.ProjectAPI.project_updates_user>`
        and :func:`greenday_api.project.project_api.ProjectAPI.update_last_viewed <greenday_api.project.project_api.ProjectAPI.update_last_viewed>`
    """
    api_type = ProjectAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectUpdateTests, self).setUp()

        self.now = timezone.now()

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

    def test_last_viewed_updated(self):
        """
            Update the time that a user viewed their latest updates
        """
        self._sign_in(self.admin)

        self.project.set_updates_viewed(
            self.admin, self.now - datetime.timedelta(hours=1))
        project_user = self.project.get_user_relation(self.admin)
        original_last_updates_viewed = project_user.last_updates_viewed

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.id)

        with self.assertNumQueries(5):
            response = self.api.update_last_viewed(request)

        project_user = self.reload(project_user)

        self.assertGreater(
            project_user.last_updates_viewed, original_last_updates_viewed)

    def test_videos_created(self):
        """
            Videos created since last viewing updates
        """
        self._sign_in(self.admin)

        videos = list(self.create_videos(5))

        self.project.set_updates_viewed(
            self.admin, last_viewed_at=self.now - datetime.timedelta(hours=3))

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)

        with self.assertNumQueries(6):
            response = self.api.project_updates_user(request)

        self.assertEqual(3, len(response.created_videos))
        self.assertEqual(
            [v.id for v in response.created_videos],
            [v.id for v in videos[:3]]
        )

        # check that a last viewed timestamp after the last update
        # causes no updates to be returned
        self.project.set_updates_viewed(
            self.admin)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)

        with self.assertNumQueries(4):
            response = self.api.project_updates_user(request)

        self.assertEqual(0, len(response.created_videos))

    def test_users_joined(self):
        """
            Users joined since last viewing updates
        """
        self._sign_in(self.admin)
        self.project.set_updates_viewed(
            self.admin, last_viewed_at=self.now - datetime.timedelta(hours=3))

        # add pending users
        self.project.add_admin(self.user)
        self.project.add_assigned(self.user2)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)

        with self.assertNumQueries(5):
            response = self.api.project_updates_user(request)

        self.assertEqual(0, len(response.users_joined))

        self.users_accept_invite(self.user, self.user2)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)

        with self.assertNumQueries(5):
            response = self.api.project_updates_user(request)

        self.assertEqual(2, len(response.users_joined))

        self.assertEqual(self.user.pk, response.users_joined[0].id)
        self.assertEqual(self.user2.pk, response.users_joined[1].id)


class ProjectUpdateCountsTests(
        TestEventBusMixin, ProjectUpdateTestMixin, ApiTestCase):
    """
        Tests for
        :func:`greenday_api.project.project_api.ProjectAPI.project_update_counts_user <greenday_api.project.project_api.ProjectAPI.project_update_counts_user>`
    """
    api_type = ProjectAPI

    def setUp(self):
        """
            Bootstrap data
        """
        super(ProjectUpdateCountsTests, self).setUp()

        self.now = timezone.now()

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

    def test_videos_created_count(self):
        """
            Number of videos created since updates last viewed
        """
        videos = list(self.create_videos(5))

        self.project.set_updates_viewed(
            self.admin, last_viewed_at=self.now - datetime.timedelta(hours=3))

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)

        self._sign_in(self.admin)
        with self.assertNumQueries(5):
            response = self.api.project_update_counts_user(request)

        self.assertEqual(3, response.created_videos)

        # check that a last viewed timestamp after the last update
        # causes no updates to be returned
        self.project.set_updates_viewed(self.admin)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)

        self._sign_in(self.admin)
        with self.assertNumQueries(5):
            response = self.api.project_update_counts_user(request)

        self.assertEqual(0, response.created_videos)

    def test_users_joined_count(self):
        """
            Number of users joined since updates last viewed
        """
        self.project.set_updates_viewed(
            self.admin, last_viewed_at=self.now - datetime.timedelta(hours=3))

        # add pending users
        self.project.add_admin(self.user)
        self.project.add_assigned(self.user2)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)

        self._sign_in(self.admin)
        with self.assertNumQueries(5):
            response = self.api.project_update_counts_user(request)

        self.assertEqual(0, response.users_joined)

        self.users_accept_invite(self.user, self.user2)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)

        self._sign_in(self.admin)
        with self.assertNumQueries(5):
            response = self.api.project_update_counts_user(request)

        self.assertEqual(2, response.users_joined)

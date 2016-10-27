"""
    Tests for :mod:`greenday_api.user.user_api <greenday_api.user.user_api>`
"""
# LIBRARIES
import mock
from milkman.dairy import milkman

# FRAMEWORK
from protorpc import message_types
from django.contrib.auth import get_user_model

# GREENDAY
from greenday_core.api_exceptions import ForbiddenException
from greenday_core.models import (
    Project,
    UserVideoDetail,
    GlobalTag,
    ProjectTag,
    VideoTag,
    VideoTagInstance,
)
from greenday_core.constants import EventKind

from .base import ApiTestCase, TestEventBusMixin
from ..user.messages import (
    UserListResponse, UserResponseMessage)
from ..user.user_api import UserAPI
from ..user.containers import (
    UserFilterContainer,
    UserCreateContainer,
    UserUpdateContainer,
    CurrentUserUpdateContainer,
)


class UserAPITests(TestEventBusMixin, ApiTestCase):
    """
        Tests for :class:`greenday_api.user.UserAPI <greenday_api.user.UserAPI>`
    """
    api_type = UserAPI

    def create_test_users(self):
        """
            Override creation of test users
        """
        User = get_user_model()

        # override
        self.admin = milkman.deliver(
            User, email="admin@foobar.com", is_superuser=True)
        self.user = milkman.deliver(User, email="user@example.com")
        self.user2 = milkman.deliver(User, email="user2@example.com")

    def test_filter_users(self):
        """ Test that the correct users are returned when doing partial filters
            on the first_name, last_name and email fields
        """
        User = get_user_model()

        # Users with some overlapping details
        charlie_brown = milkman.deliver(
            User, first_name="Charlie", last_name="Brown",
            email="charliebrown@example.com")
        charlie_brooker = milkman.deliver(
            User, first_name="Charlie", last_name="Brooker",
            email="screenwipe@example.com")
        someone_brooker = milkman.deliver(
            User, first_name="Someone", last_name="Brooker",
            email="someone@example.com")

        def _check_filtered_users(q, *users):
            self._sign_in(self.admin)

            response = self.api.users_filter(
                UserFilterContainer.combined_message_class(q=q))
            self.assertIsInstance(response, UserListResponse)
            items_pks = [item.id for item in response.items]

            self.assertEqual(len(users), len(items_pks))
            for user in users:
                self.assertTrue(user.pk in items_pks)

        # Filter on 'example.com' first, it should return all 5 users
        with self.assertNumQueries(2):
            _check_filtered_users(
                'example', charlie_brown, charlie_brooker,
                someone_brooker, self.user, self.user2)

        # Test some more restrictive filters
        with self.assertNumQueries(2):
            _check_filtered_users('charlie', charlie_brown, charlie_brooker)
        # partial matches work as well
        with self.assertNumQueries(2):
            _check_filtered_users('charl', charlie_brown, charlie_brooker)
        with self.assertNumQueries(2):
            _check_filtered_users('brooker', charlie_brooker, someone_brooker)
        with self.assertNumQueries(2):
            _check_filtered_users('someone', someone_brooker)
        with self.assertNumQueries(3):
            _check_filtered_users('Charlie Brooker', charlie_brooker)
        with self.assertNumQueries(3):
            _check_filtered_users('Charlie Brown', charlie_brown)
        # no results
        with self.assertNumQueries(3):
            _check_filtered_users('Someone Brown')

        # no search term and not admin user - should raise forbidden.
        self._sign_out()
        self._sign_in(self.user)
        self.assertRaises(
            ForbiddenException,
            self.api.users_filter,
            UserFilterContainer.combined_message_class(q=None)
        )

    def test_create_user(self):
        """
            Create a new user
        """
        # Check that a normal user can't create other users
        self._sign_in(self.user)
        self.assertRaises(
            ForbiddenException,
            self.api.users_create, UserCreateContainer.combined_message_class(
                email="new_user@example.com")
        )

        # But a superuser can
        self._sign_in(self.admin)
        with self.assertEventRecorded(
                EventKind.USERCREATED,
                object_id=True), self.assertNumQueries(6):
            response = self.api.users_create(
                UserCreateContainer.combined_message_class(
                    email="new_user@example.com"))
        self.assertIsInstance(response, UserResponseMessage)
        new_user = get_user_model().objects.get(email="new_user@example.com")
        self.assertEqual(new_user.pk, response.id)

        # Admins of projects can't
        project = milkman.deliver(Project)
        project.set_owner(self.user)
        project.add_admin(self.user2, pending=False)
        self._sign_in(self.user)
        self.assertRaises(
            ForbiddenException,
            self.api.users_create, UserCreateContainer.combined_message_class(
                email="another_user@example.com")
        )

    def test_update_user(self):
        """
            Update a user's profile
        """
        user = get_user_model().objects.create(
            username="123",
            email="test@example.com",
            is_active=False
        )

        request = UserUpdateContainer.combined_message_class(
            id=user.id,
            first_name="foo",
            last_name="bar",
            email="foobar@example.com",
            is_superuser=True,
            is_staff=True,
            profile_img_url="http://example.com/a.jpg",
            google_plus_profile="http://plus.google.com/foobar",
            accepted_nda=True,
            is_active=True
        )

        # normal user can't update users - even themselves
        self._sign_in(user)
        self.assertRaises(
            ForbiddenException,
            self.api.users_update, request
        )

        # But a superuser can
        self._sign_in(self.admin)
        with self.assertEventRecorded(
                EventKind.USERUPDATED,
                object_id=user.pk), self.assertNumQueries(4):
            response = self.api.users_update(request)

        self.assertIsInstance(response, UserResponseMessage)
        user = get_user_model().objects.get(pk=user.pk)
        self.assertEqual(user.pk, response.id)
        self.assertEqual(user.email, request.email)
        self.assertEqual(user.first_name, response.first_name)
        self.assertEqual(user.last_name, response.last_name)
        self.assertEqual(user.is_superuser, response.is_superuser)
        self.assertEqual(user.is_staff, response.is_staff)
        self.assertEqual(user.profile_img_url, response.profile_img_url)
        self.assertEqual(
            user.google_plus_profile, response.google_plus_profile)
        self.assertEqual(user.accepted_nda, response.accepted_nda)
        self.assertEqual(user.is_active, response.is_active)

    def test_update_current_user(self):
        """
            Update the currently logged in user's profile
        """
        User = get_user_model()

        user = User.objects.create(
            username="123",
            email="test@example.com",
            is_active=False
        )
        self._sign_in(user)

        request = CurrentUserUpdateContainer.combined_message_class(
            first_name="foo",
            last_name="bar",
            email="foobar@example.com",
            profile_img_url="http://example.com/a.jpg",
            google_plus_profile="http://plus.google.com/foobar",
            accepted_nda=True
        )

        with self.assertNumQueries(2):
            response = self.api.update_current_user(request)

        self.assertIsInstance(response, UserResponseMessage)
        user = User.objects.get(pk=user.pk)
        self.assertEqual(user.pk, response.id)
        self.assertEqual(user.email, request.email)
        self.assertEqual(user.first_name, response.first_name)
        self.assertEqual(user.last_name, response.last_name)
        self.assertEqual(user.profile_img_url, response.profile_img_url)
        self.assertEqual(
            user.google_plus_profile, response.google_plus_profile)
        self.assertEqual(user.accepted_nda, response.accepted_nda)

    @mock.patch("greenday_api.user.user_api.defer_delete_user")
    def test_delete_self(self, mock_defer_delete_user):
        """
            User deleting themselves
        """
        self._sign_in(self.user)

        self.api.delete_current_user(message_types.VoidMessage())

        mock_defer_delete_user.called_once_with(self.user, self.user)


    def test_get_current_user(self):
        """
            Get the current logged in user
        """
        self._sign_in(self.user)

        request = message_types.VoidMessage()
        with self.assertNumQueries(1):
            response = self.api.get_current_user(request)

        self.assertIsInstance(response, UserResponseMessage)
        self.assertEqual(self.user.pk, response.id)


class UserAPIStatsTests(ApiTestCase):
    """
        Tests for :func:`greenday_api.user.UserAPI.get_current_user_stats <greenday_api.user.UserAPI.get_current_user_stats>`
    """
    api_type = UserAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(UserAPIStatsTests, self).setUp()

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)
        self.video = self.create_video(owner=self.admin)

        self.globaltag = milkman.deliver(
            GlobalTag, name="tag2", description="buzz", image_url="img.jpg")
        self.projecttag = ProjectTag.add_root(
            project=self.project, global_tag=self.globaltag)
        self.videotag = VideoTag.objects.create(
            project=self.project,
            project_tag=self.projecttag,
            video=self.video)
        self.videotaginstance = VideoTagInstance.objects.create(
            video_tag=self.videotag,
            user=self.user
        )

    def test_get_self_stats(self):
        """
            Get current user's statistics
        """
        self._sign_in(self.user)

        UserVideoDetail.objects.create(
            user=self.user,
            video=self.video,
            watched=True
        )

        with self.assertNumQueries(3):
            response = self.api.get_current_user_stats(
                message_types.VoidMessage())

        self.assertEqual(response.id, self.user.pk)
        self.assertEqual(response.videos_watched, 1)
        self.assertEqual(response.tags_added, 1)

    def test_get_self_stats_no_data(self):
        """
            Get current user's statistics - no stats available
        """
        self._sign_in(self.user2)

        with self.assertNumQueries(3):
            response = self.api.get_current_user_stats(
                message_types.VoidMessage())

        self.assertEqual(response.id, self.user2.pk)
        self.assertEqual(response.videos_watched, 0)
        self.assertEqual(response.tags_added, 0)

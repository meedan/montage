"""
    Tests for :mod:`greenday_api.project.project_api <greenday_api.project.project_api>`
"""
# LIBRARIES
import datetime
import mock
from milkman.dairy import milkman

# FRAMEWORK
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

# GREENDAY
from greenday_core.api_exceptions import ForbiddenException, NotFoundException
from greenday_core.models import (
    Project,
    UserVideoDetail,
    PendingUser
)
from greenday_core.tests.base import TestCaseTagHelpers
from greenday_core.constants import EventKind
from greenday_core.email_templates import (
    NEW_USER_INVITED,
    EXISTING_USER_INVITED
)

from .base import ApiTestCase, TestEventBusMixin
from ..common.containers import IDContainer
from ..project.messages import (
    ProjectRequestMessage,
    ProjectResponseMessage,
    ProjectCollaboratorsResponseMessage
)
from ..project.project_api import ProjectAPI
from ..project.containers import (
    ProjectListRequest,
    ProjectUserEntityContainer,
    ProjectIDContainer,
    ProjectUpdateEntityContainer,
    ProjectUserIDEntityContainer
)

class ProjectAPITestsMixin(object):
    """
        Provides common behaviours for project test cases
    """
    def assert_project_list_cache_invalidated(self, m_cache_manager, user):
        """
            Asserts that the project list cache has been cleared

            Requires memoize_cache.cache_manager to be mocked and passed
        """
        m_cache_manager.delete_many.assert_called_with((
            "greenday_api.project.project_api._project_list_user",
            (user, True),
            {}
        ), (
            "greenday_api.project.project_api._project_list_user",
            (user, False),
            {}
        ), (
            "greenday_api.project.project_api._project_list_user",
            (user, None),
            {}
        ))


class ProjectAPITests(TestEventBusMixin, TestCaseTagHelpers, ProjectAPITestsMixin, ApiTestCase):
    """
        Test case for
        :class:`greenday_api.project.project_api.ProjectAPI <greenday_api.project.project_api.ProjectAPI>`
    """
    api_type = ProjectAPI

    def setUp(self):
        """
            Bootstrap with project data
        """
        super(ProjectAPITests, self).setUp()

        self.pending_user = milkman.deliver(
            PendingUser, email="pendingu@example.com")

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_admin(self.user, pending=False)
        self.project.add_assigned(self.user2, pending=False)
        self.project.add_assigned(self.pending_user, pending=True)

        self.favourited_video = self.create_video(
            project=self.project, favourited=True)

        self.tagged_video = self.create_video(project=self.project)

        self.archived_video = self.create_video(project=self.project)
        self.archived_video.archive()

        self.deleted_video = self.create_video(project=self.project)
        self.deleted_video.delete()

        self.tag, _, video_tag, _ = self.create_video_instance_tag(
            name='Foo',
            project=self.project,
            video=self.tagged_video)

        self.create_video_instance_tag(
            video_tag=video_tag,
            start_seconds=0,
            end_seconds=42)

        self.tag2, _, _, _ = self.create_video_instance_tag(
            name='Bar', project=self.project, video=self.tagged_video)

    @mock.patch("greenday_api.project.caching.cache_manager")
    def test_insert_project_not_whitelisted(self, m_cache_manager):
        """ A New user can create a project """
        self._sign_in(self.user)

        request = ProjectRequestMessage(
            name="test",
            description="bla bla",
            image_url="http://example.com/file.jpg",
            image_gcs_filename="/gcs/bucket/file.jpg",
            privacy_project=2,  # public
            privacy_tags=1  # private
        )

        with self.assertEventRecorded(
                EventKind.PROJECTCREATED,
                object_id=True,
                project_id=True), self.assertNumQueries(10):
            response = self.api.project_insert(request)

        project = Project.objects.get(pk=response.id)
        self.assertEqual(response.name, project.name)
        self.assertEqual(response.privacy_project, project.privacy_project)
        self.assertEqual(response.privacy_tags, project.privacy_tags)
        self.assertEqual(response.description, project.description)
        self.assertTrue(
            request.image_url, project.image_url)
        self.assertEqual(
            request.image_gcs_filename, project.image_gcs_filename)

        self.assert_project_list_cache_invalidated(m_cache_manager, self.user)

    def test_delete_project_not_owner(self):
        """
            Delete a project as admin user
        """
        self._sign_in(self.user)
        self.assertRaises(
            ForbiddenException,
            self.api.project_delete,
            IDContainer.combined_message_class(id=self.project.id)
        )

    def test_delete_project(self):
        """
            Delete a project as the project owner
        """
        project = milkman.deliver(Project)
        project.set_owner(self.user)

        self._sign_in(self.user)
        with self.assertEventRecorded(
                EventKind.PROJECTDELETED,
                object_id=project.id,
                project_id=project.id), self.assertNumQueries(13):
            self.api.project_delete(
                IDContainer.combined_message_class(id=project.id))
        self.assertObjectAbsent(project, Project.objects)

    @mock.patch("greenday_api.project.caching.cache_manager")
    def test_insert_project(self, m_cache_manager):
        """
            Insert a project
        """
        self._sign_in(self.admin)

        request = ProjectRequestMessage(
            name="test",
            description="bla bla",
            image_url="http://example.com/file.jpg",
            image_gcs_filename="/gcs/bucket/file.jpg",
            privacy_project=2,  # public
            privacy_tags=1  # private
        )

        with self.assertEventRecorded(
                EventKind.PROJECTCREATED,
                object_id=True,
                project_id=True), self.assertNumQueries(10):
            response = self.api.project_insert(request)

        project = Project.objects.get(pk=response.id)
        self.assertEqual(response.name, project.name)
        self.assertEqual(response.privacy_project, project.privacy_project)
        self.assertEqual(response.privacy_tags, project.privacy_tags)
        self.assertEqual(response.description, project.description)
        self.assertTrue(
            request.image_url, project.image_url)
        self.assertEqual(
            request.image_gcs_filename, project.image_gcs_filename)

        self.assert_project_list_cache_invalidated(m_cache_manager, self.admin)

    def test_my_projects(self):
        """
            Get list of projects assigned to a user or they have been invited to
        """
        project2 = milkman.deliver(
            Project,
            created=timezone.now() - datetime.timedelta(hours=1))
        project2.set_owner(self.admin)
        project2.add_admin(self.user, pending=False)

        project3 = milkman.deliver(
            Project,
            created=timezone.now() - datetime.timedelta(hours=2))
        project3.set_owner(self.user)

        project4 = milkman.deliver(
            Project,
            created=timezone.now() - datetime.timedelta(hours=3))
        project4.set_owner(self.admin)
        project4.add_assigned(self.user)

        self._sign_in(self.user)

        with self.assertNumQueries(4):
            response = self.api.project_list_user(
                ProjectListRequest.combined_message_class())
        self.assertEqual(4, len(response.items))

        assigned_project_resp = response.items[0]
        self.assertEqual(self.project.pk, assigned_project_resp.id)
        self.assertTrue(assigned_project_resp.current_user_info.is_assigned)
        self.assertFalse(assigned_project_resp.current_user_info.is_owner)
        self.assertTrue(assigned_project_resp.current_user_info.is_admin)
        self.assertFalse(assigned_project_resp.current_user_info.is_pending)
        self.assertEqual(2, assigned_project_resp.video_count)

        self.assertEqual(response.items[0].video_tag_instance_count, 3)

        admin_project_resp = response.items[1]
        self.assertEqual(project2.pk, admin_project_resp.id)
        self.assertTrue(admin_project_resp.current_user_info.is_assigned)
        self.assertFalse(admin_project_resp.current_user_info.is_owner)
        self.assertTrue(admin_project_resp.current_user_info.is_admin)
        self.assertFalse(admin_project_resp.current_user_info.is_pending)

        owner_project_resp = response.items[2]
        self.assertEqual(project3.pk, owner_project_resp.id)
        self.assertTrue(owner_project_resp.current_user_info.is_assigned)
        self.assertTrue(owner_project_resp.current_user_info.is_owner)
        self.assertTrue(owner_project_resp.current_user_info.is_admin)
        self.assertFalse(owner_project_resp.current_user_info.is_pending)

        pending_project_resp = response.items[3]
        self.assertEqual(project4.pk, pending_project_resp.id)
        self.assertTrue(pending_project_resp.current_user_info.is_assigned)
        self.assertFalse(pending_project_resp.current_user_info.is_owner)
        self.assertFalse(pending_project_resp.current_user_info.is_admin)
        self.assertTrue(pending_project_resp.current_user_info.is_pending)

    def test_my_projects_pending(self):
        """
            Get list of projects the user has been invited to
        """
        user3 = milkman.deliver(get_user_model(), email="user3@example.com")
        self._sign_in(user3)

        self.project.add_assigned(user3, pending=True)

        project2 = milkman.deliver(
            Project,
            created=timezone.now() - datetime.timedelta(hours=1))
        project2.set_owner(self.admin)
        project2.add_admin(user3, pending=False)

        request = ProjectListRequest.combined_message_class(pending=True)
        with self.assertNumQueries(4):
            response = self.api.project_list_user(request)
        self.assertEqual(1, len(response.items))

        self.assertEqual(self.project.pk, response.items[0].id)

    def test_my_projects_not_pending(self):
        """
            Get list of projects the user is assigned to
        """
        self._sign_in(self.user)

        project2 = milkman.deliver(
            Project,
            created=timezone.now() - datetime.timedelta(hours=1))
        project2.set_owner(self.admin)
        project2.add_admin(self.user, pending=True)

        request = ProjectListRequest.combined_message_class(pending=False)
        with self.assertNumQueries(4):
            response = self.api.project_list_user(request)
        self.assertEqual(1, len(response.items))

        self.assertEqual(self.project.pk, response.items[0].id)

    def test_get_project(self):
        """
            Get a specific project
        """
        other_user = milkman.deliver(
            get_user_model(), email="unauth@example.com")
        self._sign_in(other_user)
        self.assertRaises(
            ForbiddenException,
            self.api.project_get,
            IDContainer.combined_message_class(id=self.project.pk)
        )

        self._sign_in(self.user)
        with self.assertNumQueries(6):
            response = self.api.project_get(
                IDContainer.combined_message_class(
                    id=self.project.pk))

        self.assertIsInstance(response, ProjectResponseMessage)
        self.assertEqual(self.project.pk, response.id)
        self.assertEqual(2, response.video_count)
        self.assertEqual([self.admin.pk, self.user.pk], response.admin_ids)
        self.assertEqual(
            [self.admin.pk, self.user.pk, self.user2.pk],
            response.assigned_user_ids)
        self.assertEqual(len(response.projecttags), 2)
        self.assertEqual(
            response.projecttags[0].id, self.tag.pk)
        self.assertEqual(
            response.projecttags[0].name, self.tag.name)
        self.assertEqual(
            response.projecttags[1].id, self.tag2.pk)
        self.assertEqual(
            response.projecttags[1].name, self.tag2.name)

    @mock.patch("greenday_api.project.caching.cache_manager")
    def test_update_project(self, m_cache_manager):
        """
            Update a project
        """
        self._sign_in(self.user)

        with self.assertEventRecorded(
                EventKind.PROJECTUPDATED,
                project_id=self.project.pk,
                object_id=self.project.pk), self.assertNumQueries(8):
            response = self.api.project_update(
                ProjectUpdateEntityContainer.combined_message_class(
                    id=self.project.pk, name="version 2", privacy_project=1,
                    privacy_tags=2)
            )
        self.project = self.reload(self.project)
        self.assertEqual(response.name, self.project.name)
        self.assertEqual(
            response.privacy_project, self.project.privacy_project)
        self.assertEqual(response.privacy_tags, self.project.privacy_tags)

        self.assert_project_list_cache_invalidated(m_cache_manager, self.user)

    def test_update_project_new_image(self):
        """
            Update a project with a new image
        """
        project = milkman.deliver(
            Project,
            image_url="http://example.com/myimage.png",
            image_gcs_filename="gc_bucket/myimage")
        project.set_owner(self.user)
        self._sign_in(self.user)

        request = ProjectUpdateEntityContainer.combined_message_class(
            id=project.pk,
            name=project.name,
            image_url="http://example.com/myimage2.png",
            image_gcs_filename="gc_bucket/myimage2"
        )

        response = self.api.project_update(request)

        project = self.reload(project)
        self.assertEqual(request.image_url, project.image_url)
        self.assertEqual(
            request.image_gcs_filename, project.image_gcs_filename)

    @mock.patch("greenday_api.project.caching.cache_manager")
    def test_patch_project(self, m_cache_manager):
        """
            Patch a project
        """
        self._sign_in(self.user)

        name = self.project.name

        with self.assertEventRecorded(
                EventKind.PROJECTUPDATED,
                project_id=self.project.pk,
                object_id=self.project.pk), self.assertNumQueries(8):
            response = self.api.project_patch(
                ProjectUpdateEntityContainer.combined_message_class(
                    id=self.project.pk, description="foobarbuzz")
            )
        self.project = self.reload(self.project)
        self.assertEqual(name, self.project.name)
        self.assertEqual("foobarbuzz", self.project.description)

        self.assert_project_list_cache_invalidated(m_cache_manager, self.user)

    @mock.patch("greenday_api.project.caching.cache_manager")
    def test_restore_project(self, m_cache_manager):
        """
            Restore a soft-deleted project
        """
        self.assertIsNone(self.project.trashed_at)
        container = IDContainer.combined_message_class(
            id=self.project.pk)

        self.project.delete()

        # tests that a 403 is raised if non superuser or somebody that is
        # not the project owner tries to restore the project.
        self._sign_in(self.user)
        self.assertRaises(
            ForbiddenException,
            self.api.project_restore,
            container,
        )

        # now sign in a user who does have permission
        self._sign_in(self.admin)
        with self.assertEventRecorded(
                EventKind.PROJECTRESTORED,
                project_id=self.project.pk,
                object_id=self.project.pk), self.assertNumQueries(11):
            response = self.api.project_restore(container)
        self.assertIsInstance(response, ProjectResponseMessage)
        self.project = self.reload(self.project)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
        self.assertIsNone(self.project.trashed_at)

        self.assert_project_list_cache_invalidated(m_cache_manager, self.admin)

    def test_404_is_raised(self):
        """
            Get a project that doesn't exist
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.project_get,
            IDContainer.combined_message_class(id=9999)
        )

        self.assertRaises(
            NotFoundException,
            self.api.project_restore,
            IDContainer.combined_message_class(id=9999)
        )

    def test_project_stats(self):
        """
            Get a project's statistics
        """
        watched_video = self.create_video(project=self.project)
        UserVideoDetail.objects.create(
            user=self.user,
            video=watched_video,
            watched=True
        )

        self._sign_in(self.user)
        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)
        with self.assertNumQueries(8):
            response = self.api.get_project_stats(request)

        self.assertEqual(4, response.total_videos)
        self.assertEqual(1, response.archived_videos)
        self.assertEqual(1, response.favourited_videos)
        self.assertEqual(3, response.video_tags)
        self.assertEqual(1, response.watched_videos)

        self.assertEqual(3, response.total_tags)
        self.assertEqual("Foo", response.top_tags[0].name)
        self.assertEqual(2, response.top_tags[0].count)
        self.assertEqual("Bar", response.top_tags[1].name)
        self.assertEqual(1, response.top_tags[1].count)


class ProjectAPIUserTests(TestEventBusMixin, ApiTestCase, ProjectAPITestsMixin):
    """
        Test case for
        :class:`greenday_api.project.project_api.ProjectAPI <greenday_api.project.project_api.ProjectAPI>`

        Tests user/collaborators endpoints
    """
    api_type = ProjectAPI

    def setUp(self):
        """
            Bootstrap data
        """
        super(ProjectAPIUserTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.owner_user_relation = self.project.set_owner(self.admin)

    def test_list_users(self):
        """
            Get assigned users as an admin
        """
        admin_user_relation = self.project.add_admin(
            self.user, pending=False)
        assigned_pending_user_relation = self.project.add_assigned(
            self.user2, pending=True)

        self._sign_in(self.admin)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)
        with self.assertNumQueries(4):
            response = self.api.project_users(request)

        self.assertEqual(3, len(response.items))

        for user_relation in (
                self.owner_user_relation,
                admin_user_relation,
                assigned_pending_user_relation):
            item = next(
                i for i in response.items if i.id == user_relation.pk)
            self.assertEqual(user_relation.user.first_name, item.first_name)
            self.assertEqual(user_relation.user.last_name, item.last_name)
            self.assertEqual(user_relation.user.email, item.email)
            self.assertEqual(user_relation.user.profile_img_url, item.profile_img_url)

            self.assertEqual(user_relation.user_id, item.user_id)
            self.assertEqual(user_relation.project_id, item.project_id)

            self.assertEqual(user_relation.is_admin, item.is_admin)
            self.assertEqual(user_relation.is_assigned, item.is_assigned)
            self.assertEqual(user_relation.is_owner, item.is_owner)
            self.assertEqual(user_relation.is_pending, item.is_pending)

            self.assertFalse(item.pending_user_id)

    def test_list_users_non_admin(self):
        """
            Get assigned users as a collaborator
        """
        user_relation = self.project.add_assigned(
            self.user, pending=False)
        assigned_pending_user_relation = self.project.add_assigned(
            self.user2, pending=True)

        self._sign_in(self.user)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)
        with self.assertNumQueries(4):
            response = self.api.project_users(request)

        self.assertEqual(2, len(response.items))

    def test_add_user_non_admin(self):
        """
            Non-admin on project adds a project user.
        """
        self.project.add_assigned(self.user, pending=False)

        self._sign_in(self.user)
        request = ProjectUserEntityContainer.combined_message_class(
            project_id=self.project.pk, email=self.user2.email)
        self.assertRaises(
            ForbiddenException,
            self.api.project_add_user,
            request)

    @mock.patch("greenday_api.project.project_api.send_email")
    def test_add_user(self, send_email_mock):
        """
            Add a project user
        """
        self.project.add_admin(self.user, pending=False)

        # Test the add user method
        self._sign_in(self.admin)
        request = ProjectUserEntityContainer.combined_message_class(
            project_id=self.project.pk, email=self.user2.email)
        with self.assertEventRecorded(
                EventKind.USERINVITEDASPROJECTUSER,
                project_id=self.project.pk,
                object_id=self.user2.pk), self.assertNumQueries(9):
            response = self.api.project_add_user(request)

        self.assertIsInstance(response, ProjectCollaboratorsResponseMessage)

        # check that the user is pending
        projectuser = self.project.get_user_relation(self.user2)
        self.assertTrue(projectuser.is_pending)
        self.assertTrue(projectuser.is_assigned)

        # check that the user isn't yet in the assigned_users list
        assigned_users = self.project.assigned_users
        self.assertEqual(2, len(assigned_users))
        self.assertEqual(self.admin.pk, assigned_users[0].pk)
        self.assertEqual(self.user.pk, assigned_users[1].pk)

        send_email_mock.assert_called_with(
            "You've been invited to collaborate on a Montage project",
            EXISTING_USER_INVITED.format(
                project_name=self.project.name,
                home_link=settings.HOME_LINK),
            self.user2.email
        )

    @mock.patch("greenday_api.project.project_api.send_email")
    def test_add_new_user(self, send_email_mock):
        """
            Add a user not in the database
        """
        self.project.add_admin(self.user, pending=False)

        # Test the add user method
        self._sign_in(self.admin)
        request = ProjectUserEntityContainer.combined_message_class(
            project_id=self.project.pk, email="hansolo@example.com")
        with self.assertEventRecorded(
                EventKind.PENDINGUSERINVITEDASPROJECTUSER,
                project_id=self.project.pk,
                object_id=True,
                meta=request.email), self.assertNumQueries(13):
            response = self.api.project_add_user(request)

        self.assertIsInstance(response, ProjectCollaboratorsResponseMessage)

        new_user = PendingUser.objects.get(email=request.email)

        # check that the user is pending
        projectuser = self.project.get_user_relation(new_user)
        self.assertTrue(projectuser.is_pending)
        self.assertTrue(projectuser.is_assigned)

        # check that the user isn't yet in the assigned_users list
        assigned_users = self.project.assigned_users
        self.assertEqual(2, len(assigned_users))
        self.assertEqual(self.admin.pk, assigned_users[0].pk)
        self.assertEqual(self.user.pk, assigned_users[1].pk)

        send_email_mock.assert_called_with(
            "You've been invited to join Montage",
            NEW_USER_INVITED.format(
                project_name=self.project.name,
                home_link=settings.HOME_LINK),
            new_user.email
        )

    def test_remove_user(self):
        """
            Remove an assigned user
        """
        self.project.add_admin(self.user, pending=False)
        project_user = self.project.add_assigned(self.user2, pending=False)

        request = ProjectUserIDEntityContainer.combined_message_class(
            project_id=self.project.pk, id=project_user.pk)

        # Test the remove user from project method
        # A a normal user doesn't have the permission
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.project_remove_user, request
        )
        self._sign_in(self.user)  # but the owner/admin can

        with self.assertEventRecorded(
                EventKind.USERREMOVED,
                project_id=self.project.pk,
                object_id=self.user2.pk), self.assertNumQueries(6):
            self.api.project_remove_user(request)

        projectuser = self.project.get_user_relation(self.user2)
        self.assertFalse(projectuser)

    def test_add_admin(self):
        """
            Add an admin to a project
        """
        self.project.add_admin(self.user, pending=False)
        self._sign_in(self.user)

        # Test the add admin method
        request = ProjectUserEntityContainer.combined_message_class(
            project_id=self.project.pk, email=self.user2.email, as_admin=True)
        with self.assertEventRecorded(
                EventKind.USERINVITEDASPROJECTADMIN,
                project_id=self.project.pk,
                object_id=self.user2.pk), self.assertNumQueries(9):
            response = self.api.project_add_user(request)

        self.assertIsInstance(response, ProjectCollaboratorsResponseMessage)

        # check that the user is pending
        projectuser = self.project.get_user_relation(self.user2)
        self.assertTrue(projectuser.is_pending)
        self.assertTrue(projectuser.is_admin)

        # check that the user isn't yet in the admin list
        admins = self.project.admins
        self.assertEqual(2, len(admins))
        self.assertEqual(self.admin.pk, admins[0].pk)
        self.assertEqual(self.user.pk, admins[1].pk)

    def test_remove_admin(self):
        """
            Remove an admin
        """
        self.project.add_admin(self.user, pending=False)
        project_user = self.project.add_admin(self.user2, pending=False)

        request = ProjectUserIDEntityContainer.combined_message_class(
            project_id=self.project.pk, id=project_user.pk, as_admin=True)

        self._sign_in(self.admin)
        with self.assertEventRecorded(
                EventKind.USERREMOVED,
                project_id=self.project.pk,
                object_id=self.user2.pk), self.assertNumQueries(6):
            self.api.project_remove_user(request)

        projectuser = self.project.get_user_relation(self.user2)
        self.assertFalse(projectuser)

    def test_remove_pendinguser(self):
        """
            Remove a user with a pending invitation
        """
        pending_user = milkman.deliver(
            PendingUser, email="pendingu@example.com")

        project_user = self.project.add_assigned(pending_user, pending=True)

        request = ProjectUserIDEntityContainer.combined_message_class(
            project_id=self.project.pk, id=project_user.pk)

        self._sign_in(self.admin)
        with self.assertEventRecorded(
                EventKind.PENDINGUSERREMOVED,
                project_id=self.project.pk,
                object_id=pending_user.pk), self.assertNumQueries(6):
            self.api.project_remove_user(request)

        projectuser = self.project.get_user_relation(pending_user)
        self.assertFalse(projectuser)

    @mock.patch("greenday_api.project.caching.cache_manager")
    def test_accept_invitation(self, m_cache_manager):
        """
            Accept an invitation to collaborate
        """
        self._sign_in(self.user)

        self.project.add_assigned(self.user)

        # set the updates viewed timestamp to sometime further away as it
        # should be updated
        projectuser = self.project.get_user_relation(self.user)
        self.assertTrue(projectuser.is_pending)

        original_last_updates_viewed = timezone.now() - datetime.timedelta(
            hours=1)
        projectuser.last_updates_viewed = original_last_updates_viewed
        projectuser.save()

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)
        with self.assertEventRecorded(
                EventKind.USERACCEPTEDPROJECTINVITE,
                project_id=self.project.pk,
                object_id=self.user.pk), self.assertNumQueries(8):
            response = self.api.accept_project_invitation(request)

        self.assertEqual(self.project.pk, response.id)
        self.assertFalse(response.current_user_info.is_pending)

        projectuser = self.reload(projectuser)

        self.assertFalse(projectuser.is_pending)
        self.assertGreater(
            projectuser.last_updates_viewed, original_last_updates_viewed)

        self.assert_project_list_cache_invalidated(m_cache_manager, self.user)

    def test_accept_invitation_new_user(self):
        """
            New user accepts an invitation
        """
        pending_user = PendingUser.objects.create(email="hansolo@example.com")
        self.project.add_assigned(pending_user)

        projectuser = self.project.get_user_relation(pending_user)
        self.assertTrue(projectuser.is_pending)

        # user object will be automatically created when user accesses site
        # and will be linked to the logged in user
        user = get_user_model().objects.create(
            email=pending_user.email,
            username="hansolo",
            gaia_id="hansolo"
        )
        pending_user.user = user
        pending_user.save()

        pending_user.projectusers.all().update(user=user, is_pending=True)

        self._sign_in(user)
        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)
        with self.assertEventRecorded(
                EventKind.USERACCEPTEDPROJECTINVITE,
                project_id=self.project.pk,
                object_id=user.pk), self.assertNumQueries(10):
            response = self.api.accept_project_invitation(request)

        self.assertEqual(self.project.pk, response.id)
        self.assertFalse(response.current_user_info.is_pending)

        projectuser = self.reload(projectuser)
        self.assertEqual(user, projectuser.user)
        self.assertFalse(projectuser.is_pending)

    @mock.patch("greenday_api.project.caching.cache_manager")
    def test_reject_invitation(self, m_cache_manager):
        """
            Reject an invitation to collaborate
        """
        self._sign_in(self.user)

        self.project.add_assigned(self.user)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)
        with self.assertEventRecorded(
                EventKind.USERREJECTEDPROJECTINVITE,
                project_id=self.project.pk,
                object_id=self.user.pk), self.assertNumQueries(5):
            self.api.reject_project_invitation(request)

        # TODO: email?
        self.assertFalse(self.project.get_user_relation(self.user))

        self.assert_project_list_cache_invalidated(m_cache_manager, self.user)


class ProjectChannelAPITests(ApiTestCase):
    """
        Test case for
        :func:`greenday_api.project.project_api.ProjectAPI.get_distinct_channels <greenday_api.project.project_api.ProjectAPI.get_distinct_channels>`
    """
    api_type = ProjectAPI

    def setUp(self):
        """
            Bootstrap data
        """
        super(ProjectChannelAPITests, self).setUp()

        self.pending_user = milkman.deliver(
            PendingUser, email="pendingu@example.com")

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

        self.video_1 = self.create_video(
            channel_id="123", channel_name="foo", project=self.project)

        self.video_2 = self.create_video(
            channel_id="123", channel_name="fez", project=self.project)

        self.video_3 = self.create_video(
            channel_id="456", channel_name="bar", project=self.project)

        self.other_video = self.create_video(
            channel_id="999", channel_name="buzz")

    def test_get_distinct_channels(self):
        """
            Get distinct list of channels for videos belonging to project
        """
        self._sign_in(self.admin)

        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)
        response = self.api.get_distinct_channels(request)

        self.assertEqual(2, len(response.items))

        channel_123_resp = next(r for r in response.items if r.id == "123")
        self.assertEqual("fez", channel_123_resp.name)

        channel_456_resp = next(r for r in response.items if r.id == "456")
        self.assertEqual("bar", channel_456_resp.name)

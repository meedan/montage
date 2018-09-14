"""
    Tests for :mod:`greenday_core.models <greenday_core.models>`
"""
# import lib deps
from milkman.dairy import milkman
from django.utils import timezone

# import project deps
from ..models import (
    User,
    Project,
    Video,
    ProjectUser,
    PendingUser,
    Event,
    GlobalTag,
    ProjectTag,
    VideoTag,
    VideoTagInstance,
    TimedVideoComment,
    DuplicateVideoMarker,
    get_sentinel_user)
from ..api_exceptions import TagNameExistsException, BadRequestException
from .base import AppengineTestBed, TestCaseTagHelpers


# user model test suite
class UserModelTestCase(TestCaseTagHelpers, AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.user.User <greenday_core.models.user.User>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(UserModelTestCase, self).setUp()
        self.user = milkman.deliver(User, email="user@example.com")
        self.admin = milkman.deliver(
            User, email="admin@example.com", is_superuser=True, is_googler=True)

    def test_is_external_property(self):
        """
            Check the is_external member
        """
        self.assertFalse(self.admin.is_external)
        self.assertTrue(self.user.is_external)

    def test_ldap_property(self):
        """
            Check the ldap member
        """
        self.assertEqual(self.admin.ldap, 'admin')
        self.assertEqual(self.user.ldap, 'user')

    def test_delete_cascade(self):
        """
            Check delete cascade behaviour of users
        """
        project = milkman.deliver(Project)
        project.set_owner(self.admin)

        user_project = milkman.deliver(Project)
        user_project.set_owner(self.user)

        video = self.create_video(project=project, user=self.user)

        pending_user = PendingUser.objects.create(
            email=self.user.email, user=self.user)

        event = milkman.deliver(Event, user=self.user)

        global_tag, project_tag, video_tag, video_instance_tag = \
            self.create_video_instance_tag(
                project=project,
                video=video,
                user=self.user,
                start_seconds=0,
                end_seconds=1)

        # create child tags - these all get deleted as well
        _, project_tag_2, video_tag_2, video_instance_tag_2 = \
            self.create_video_instance_tag(
                video_tag=video_tag,
                user=self.admin,
                start_seconds=0,
                end_seconds=1)

        comment = TimedVideoComment.add_root(
            video=video, user=self.user, start_seconds=0)
        # all child replies get deleted
        other_reply = comment.add_reply("foo", self.admin)

        other_comment = TimedVideoComment.add_root(
            video=video, user=self.admin, start_seconds=0)
        reply = other_comment.add_reply("bar", self.user)

        self.user.delete()

        # delete project is user is the project owner
        self.assertObjectAbsent(user_project)

        self.assertObjectAbsent(video)
        self.assertObjectAbsent(pending_user)

        self.assertObjectAbsent(global_tag)
        self.assertObjectAbsent(project_tag)
        self.assertObjectAbsent(video_tag)
        self.assertObjectAbsent(video_instance_tag)

        self.assertObjectAbsent(project_tag_2)
        self.assertObjectAbsent(video_tag_2)
        self.assertObjectAbsent(video_instance_tag_2)

        self.assertObjectAbsent(comment)
        self.assertObjectAbsent(other_reply)

        self.assertObjectAbsent(other_comment)
        self.assertObjectAbsent(reply)

        event = self.reload(event)
        self.assertEqual(event.user, get_sentinel_user())


# project model test suite
class ProjectModelTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.project.Project <greenday_core.models.project.Project>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectModelTestCase, self).setUp()
        self.user = milkman.deliver(User, email="user@example.com")
        self.admin = milkman.deliver(
            User, email="admin@example.com", is_superuser=True, is_googler=True)
        self.project_owner = milkman.deliver(User, email="project_owner@example.com")
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.project_owner)
        self.project.add_admin(self.admin, pending=False)
        self.project.add_assigned(self.user, pending=False)

    def test_is_owner_or_admin_instance_method(self):
        """
            Check method to tell if user is owner or admin of project
        """
        self.assertFalse(self.project.is_owner_or_admin(self.user))
        self.assertTrue(self.project.is_owner_or_admin(self.project_owner))
        self.assertTrue(self.project.is_owner_or_admin(self.admin))

    def test_is_assigned_instance_method(self):
        """
            Check method to tell if user is assigned to the project
        """
        self.assertTrue(self.project.is_assigned(self.user))
        self.assertTrue(self.project.is_assigned(self.project_owner))
        self.assertTrue(self.project.is_assigned(self.admin))

    def test_is_admin_instance_method(self):
        """
            Check method to tell if user is an admin of the project
        """
        self.assertFalse(self.project.is_admin(self.user))
        self.assertTrue(self.project.is_admin(self.project_owner))
        self.assertTrue(self.project.is_admin(self.admin))

    def test_set_owner(self):
        """
            Check method to set user as owner
        """
        # already has an owner
        self.assertRaises(AssertionError, self.project.set_owner, self.user)

        # get rid of current owner
        owner_relation = ProjectUser.objects.get(
            project=self.project, user=self.project.owner)
        owner_relation.is_owner = False
        owner_relation.save()

        self.project.set_owner(self.admin)

        self.assertEqual(self.admin, self.project.owner)

    def test_add_admin(self):
        """
            Check method to add user as admin admin
        """
        self.project.add_admin(self.user, pending=False)

        self.assertIn(self.user, self.project.admins)

    def test_remove_admin(self):
        """
            Remove an admin user
        """
        self.project.remove_user(self.admin)

        self.assertNotIn(self.admin, self.project.admins)

    def test_add_assigned(self):
        """
            Add an assigned user
        """
        self.project.add_assigned(self.admin, pending=False)

        self.assertIn(self.admin, self.project.assigned_users)

    def test_remove_assigned(self):
        """
            Remove an assigned user
        """
        self.project.remove_user(self.user)

        self.assertNotIn(self.user, self.project.assigned_users)


class VideoModelTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.video.Video <greenday_core.models.video.Video>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoModelTestCase, self).setUp()
        self.project_owner = milkman.deliver(User, email="admin@example.com")
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.project_owner)
        self.video = self.create_video(project=self.project)

    def test_video_archived(self):
        """
            Check queryset managers return correct videos in based on
            trashed/archived status
        """
        archived_video = self.create_video(
            project=self.project, archived_at=timezone.now())
        deleted_video = self.create_video(
            project=self.project, trashed_at=timezone.now())
        archived_and_deleted_video = self.create_video(
            project=self.project, archived_at=timezone.now(),
            trashed_at=timezone.now())

        # one active video
        self.assertEqual(self.video.pk, Video.objects.get().pk)

        # one archived video (that hasn't also been deleted)
        self.assertEqual(archived_video.pk, Video.archived_objects.get().pk)

        # two deleted videos
        deleted_ids = [v.id for v in Video.trash.all()]
        self.assertIn(deleted_video.pk, deleted_ids)
        self.assertIn(archived_and_deleted_video.pk, deleted_ids)

        # all videos
        self.assertEqual(4, Video.all_objects.count())


class VideoTagInstanceTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.tag.VideoTagInstance <greenday_core.models.tag.VideoTagInstance>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagInstanceTestCase, self).setUp()

        self.project = milkman.deliver(Project)
        self.video = self.create_video(project=self.project)
        self.globaltag = milkman.deliver(GlobalTag)
        self.projecttag = ProjectTag.add_root(
            project=self.project, global_tag=self.globaltag)
        self.videotag = VideoTag.objects.create(
            project=self.project,
            project_tag=self.projecttag,
            video=self.video)

        self.instance = VideoTagInstance.objects.create(
            video_tag=self.videotag,
            start_seconds=3.14,
            end_seconds=13.37)

    def test_generic_relation_on_save(self):
        """
            Each tag instance should save a generic FK to the video.

            For VideoTagInstance models this is derived from the
            associated VideoTag
        """
        self.assertEqual(self.instance.tagged_content_object, self.video)

    def test_properties_created(self):
        """
            Getters and setters should be created for the instance
        """
        self.assertEqual(self.video, self.instance.video)

        video2 = self.create_video(project=self.project)
        self.instance.video = video2

        self.assertEqual(video2, self.instance.video)


class VideoTagTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.tag.VideoTag <greenday_core.models.tag.VideoTag>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagTestCase, self).setUp()

        self.project = milkman.deliver(Project)
        self.video = self.create_video(project=self.project)
        self.globaltag = milkman.deliver(GlobalTag)
        self.projecttag = ProjectTag.add_root(
            project=self.project, global_tag=self.globaltag)
        self.videotag = VideoTag.objects.create(
            project=self.project,
            project_tag=self.projecttag,
            video=self.video)

    def test_tag_video(self):
        """
            Tag a video with a tag instance
        """
        with self.assertNumQueries(4):
            tag_instance = self.videotag.tag_video(
                start_seconds=3.14, end_seconds=13.37)

        persisted_tag_instance = self.videotag.tag_instances.get()
        self.assertEqual(tag_instance, persisted_tag_instance)

        self.assertEqual(tag_instance.start_seconds, 3.14)
        self.assertEqual(tag_instance.end_seconds, 13.37)

    def test_tag_video_seconds_overlap(self):
        """
            Tag a video where the new tag instance overlaps an
            existing instance
        """
        self.videotag.tag_video(
            start_seconds=3, end_seconds=5)

        self.assertRaises(
            BadRequestException,
            self.videotag.tag_video,
            start_seconds=4,
            end_seconds=6)
        self.assertRaises(
            BadRequestException,
            self.videotag.tag_video,
            start_seconds=1,
            end_seconds=4)

        self.videotag.tag_video(start_seconds=5, end_seconds=6)


class GlobalTagTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.tag.GlobalTag <greenday_core.models.tag.GlobalTag>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(GlobalTagTestCase, self).setUp()

        self.private_tag_project_1 = milkman.deliver(
            Project, privacy_tags=Project.PRIVATE)
        self.private_tag_project_2 = milkman.deliver(
            Project, privacy_tags=Project.PRIVATE)
        self.public_tag_project_1 = milkman.deliver(
            Project, privacy_tags=Project.PUBLIC)
        self.public_tag_project_2 = milkman.deliver(
            Project, privacy_tags=Project.PUBLIC)

    def test_duplicate_private_tag_of_public_tag(self):
        """
            Private tag can be created with same name as public tag
        """
        GlobalTag.objects.create(
            name="foo",
            created_from_project=self.public_tag_project_1)

        GlobalTag.objects.create(
            name="foo",
            created_from_project=self.private_tag_project_1)

    def test_duplicate_public_tag_of_public_tag(self):
        """
            Public tag cannot be created if public tag already exists with
            same name
        """
        GlobalTag.objects.create(
            name="foo",
            created_from_project=self.public_tag_project_1)

        self.assertRaises(
            TagNameExistsException,
            GlobalTag.objects.create,
            name="foo",
            created_from_project=self.public_tag_project_2)

    def test_duplicate_private_tag_of_private_tag_same_project(self):
        """
            Private tag cannot be created if creation project already has a
            tag with the same name
        """
        GlobalTag.objects.create(
            name="foo",
            created_from_project=self.private_tag_project_1)

        self.assertRaises(
            TagNameExistsException,
            GlobalTag.objects.create,
            name="foo",
            created_from_project=self.private_tag_project_1)

    def test_duplicate_private_tag_of_private_tag_different_project(self):
        """
            Private tag can be created if a tag exists on a different project
            with private tags
        """
        GlobalTag.objects.create(
            name="foo",
            created_from_project=self.private_tag_project_1)

        GlobalTag.objects.create(
            name="foo",
            created_from_project=self.private_tag_project_2)

    def test_save_self_private(self):
        """
            Create a private tag and then make sure it can be saved
            without errors
        """
        tag = GlobalTag.objects.create(
            name="foo",
            created_from_project=self.private_tag_project_1)

        tag.save()

    def test_save_self_public(self):
        """
            Create a public tag and then make sure it can be saved
            without errors
        """
        tag = GlobalTag.objects.create(
            name="foo",
            created_from_project=self.public_tag_project_1)

        tag.save()

    def test_rename_public_conflict(self):
        """
            Rename a public name to a name already in use by a public tag
        """
        GlobalTag.objects.create(
            name="foo",
            created_from_project=self.public_tag_project_1)

        tag2 = GlobalTag.objects.create(
            name="bar",
            created_from_project=self.public_tag_project_2)

        tag2.name = "foo"
        self.assertRaises(
            TagNameExistsException,
            tag2.save)


class DuplicateVideoTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.video.DuplicateVideoMarker <greenday_core.models.video.DuplicateVideoMarker>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(DuplicateVideoTestCase, self).setUp()

        self.project = milkman.deliver(Project)
        self.video_1 = self.create_video(project=self.project)
        self.video_2 = self.create_video(project=self.project)

    def test_get_duplicates(self):
        """
            Get a video's duplicates
        """
        DuplicateVideoMarker.objects.create(
            video_1=self.video_1, video_2=self.video_2)

        with self.assertNumQueries(1):
            dupe_videos = self.video_1.get_duplicates()

        self.assertEqual(1, len(dupe_videos))
        self.assertEqual(self.video_2, dupe_videos[0])

        with self.assertNumQueries(1):
            dupe_videos = self.video_2.get_duplicates()

        self.assertEqual(1, len(dupe_videos))
        self.assertEqual(self.video_1, dupe_videos[0])

    def test_get_duplicates_ids_only(self):
        """
            Get a video's duplicates - only return the video IDs
        """
        DuplicateVideoMarker.objects.create(
            video_1=self.video_2, video_2=self.video_1)

        with self.assertNumQueries(1):
            dupe_videos = self.video_1.get_duplicates(ids_only=True)

        self.assertEqual(1, len(dupe_videos))
        self.assertEqual(self.video_2.pk, dupe_videos[0])

        with self.assertNumQueries(1):
            dupe_videos = self.video_2.get_duplicates(ids_only=True)

        self.assertEqual(1, len(dupe_videos))
        self.assertEqual(self.video_1.pk, dupe_videos[0])

    def test_add_marker(self):
        """
            Add a duplicate marker between two videos
        """
        self.assertTrue(
            DuplicateVideoMarker.add_marker(self.video_1, self.video_2))

        marker = DuplicateVideoMarker.objects.get()
        self.assertEqual(self.video_1, marker.video_1)
        self.assertEqual(self.video_2, marker.video_2)

    def test_add_marker_exists(self):
        """
            Adds a duplicate marker for two videos already marked as duplicates
        """
        DuplicateVideoMarker.objects.create(
            video_1=self.video_1, video_2=self.video_2)

        self.assertFalse(
            DuplicateVideoMarker.add_marker(self.video_1, self.video_2))

        self.assertFalse(
            DuplicateVideoMarker.add_marker(self.video_2, self.video_1))

    def test_add_marker_multiple(self):
        """
            Add multiple duplicate markers
        """
        video_3 = self.create_video(project=self.project)

        self.assertTrue(
            DuplicateVideoMarker.add_marker(self.video_1, self.video_2))
        self.assertTrue(
            DuplicateVideoMarker.add_marker(self.video_1, video_3))

        self.assertEqual(2, len(self.video_1.get_duplicates()))

"""
    Tests for :mod:`greenday_core.models.comment <greenday_core.models.comment>`
"""
from milkman.dairy import milkman
from django.utils import timezone

from ..models import (
    User,
    Project,
    TimedVideoComment,
    ProjectComment
)

from .base import AppengineTestBed


class TimedVideoCommentTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.comment.TimedVideoComment <greenday_core.models.comment.TimedVideoComment>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(TimedVideoCommentTestCase, self).setUp()

        self.project = milkman.deliver(Project)
        self.video = self.create_video(project=self.project)

        self.user1 = milkman.deliver(User, email="user1@example.com")
        self.user2 = milkman.deliver(User, email="user2@example.com")

    def test_add_reply(self):
        """
            Add a reply to a comment
        """
        with self.assertNumQueries(5):
            root = TimedVideoComment.add_root(
                video=self.video, text="foo", user=self.user1, start_seconds=0)

        with self.assertNumQueries(5):
            reply = root.add_reply("bar", self.user2)

        # cannot reply to replies - we only allow a single level of comments
        self.assertRaises(AssertionError, reply.add_reply, "baz", None)

    def test_get_root_comments(self):
        """
            Get all root comment threads for a video
        """
        for i in range(0, 5):
            (
                TimedVideoComment.add_root(
                    video=self.video,
                    text="foo{0}".format(i),
                    user=self.user1,
                    start_seconds=0
                ).add_reply("baz{0}".format(i), user=self.user1)
            )

        # add some comments to another video
        other_video = self.create_video(project=self.project)
        for i in range(0, 5):
            TimedVideoComment.add_root(
                video=other_video,
                text="bar{0}".format(i),
                user=self.user1,
                start_seconds=0)

        with self.assertNumQueries(2):
            video_comments = list(TimedVideoComment.get_root_comments_for(
                self.video))

        self.assertEqual(5, len(video_comments))

        with self.assertNumQueries(2):
            video_comments = TimedVideoComment.get_root_comments_for(
                self.video, prefetch_replies=True)

        self.assertEqual(5, len(video_comments))

    def test_created_modified_updated(self):
        """
            Check that created and modified dates are updated correctly
        """
        # because these are quite important for comments
        start = timezone.now()
        root = TimedVideoComment.add_root(
            video=self.video, text="foo", user=self.user1, start_seconds=0)

        self.assertGreater(root.created, start)
        self.assertGreater(root.modified, start)

        created, modified = root.created, root.modified

        root.save()

        self.assertEqual(created, root.created)
        self.assertGreater(root.modified, modified)


class ProjectCommentTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.comment.ProjectComment <greenday_core.models.comment.ProjectComment>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectCommentTestCase, self).setUp()

        self.project = milkman.deliver(Project)

        self.user1 = milkman.deliver(User, email="user1@example.com")
        self.user2 = milkman.deliver(User, email="user2@example.com")

    def test_add_reply(self):
        """
            Add a comment reply
        """
        with self.assertNumQueries(5):
            root = ProjectComment.add_root(
                project=self.project, text="foo", user=self.user1)

        with self.assertNumQueries(4):
            reply = root.add_reply("bar", self.user2)

        # cannot reply to replies - we only allow a single level of comments
        self.assertRaises(AssertionError, reply.add_reply, "baz", None)

    def test_get_root_comments(self):
        """
            Get all root comment thread for a project
        """
        for i in range(0, 5):
            (
                ProjectComment.add_root(
                    project=self.project,
                    text="foo{0}".format(i),
                    user=self.user1,
                ).add_reply("baz{0}".format(i), user=self.user1)
            )

        # add some comments to another project
        other_project = milkman.deliver(Project)
        for i in range(0, 5):
            ProjectComment.add_root(
                project=other_project,
                text="bar{0}".format(i),
                user=self.user1)

        with self.assertNumQueries(1):
            project_comments = list(ProjectComment.get_root_comments_for(
                self.project))

        self.assertEqual(5, len(project_comments))

        with self.assertNumQueries(1):
            project_comments = ProjectComment.get_root_comments_for(
                self.project, prefetch_replies=True)

        self.assertEqual(5, len(project_comments))

    def test_created_modified_updated(self):
        """
            Check that created and modified dates are updated correctly
        """
        # because these are quite important for comments
        start = timezone.now()
        root = ProjectComment.add_root(
            project=self.project, text="foo", user=self.user1)

        self.assertGreater(root.created, start)
        self.assertGreater(root.modified, start)

        created, modified = root.created, root.modified

        root.save()

        self.assertEqual(created, root.created)
        self.assertGreater(root.modified, modified)

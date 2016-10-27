"""
    Tests for :mod:`greenday_api.videocomment.videocomment_api <greenday_api.videocomment.videocomment_api>`
"""
from milkman.dairy import milkman
from django.contrib.auth import get_user_model

from greenday_core.api_exceptions import BadRequestException, ForbiddenException
from greenday_core.constants import EventKind
from greenday_core.models import (
    Project, TimedVideoComment
)

from .base import ApiTestCase, TestEventBusMixin
from ..common.containers import VideoEntityContainer

from ..videocomment.videocomment_api import VideoCommentAPI
from ..videocomment.containers import (
    VideoCommentEntityContainer,
    CreateVideoRootCommentContainer,
    UpdateVideoCommentContainer,
    CreateVideoCommentReplyContainer,
    UpdateVideoCommentReplyContainer,
    VideoCommentReplyContainer
)


class VideoCommentAPITestCase(ApiTestCase, TestEventBusMixin):
    """
        Test case for
        :class:`greenday_api.videocomment.videocomment_api.VideoCommentAPI <greenday_api.videocomment.videocomment_api.VideoCommentAPI>`
    """
    api_type = VideoCommentAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoCommentAPITestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)
        self.video = self.create_video(project=self.project, duration=42)
        self.video_2 = self.create_video(project=self.project, duration=48)

    def test_list_comments(self):
        """
            List all video comments
        """
        self._sign_in(self.user)

        # create root comments
        expected_comments = [
            TimedVideoComment.add_root(
                video=self.video,
                user=self.user,
                text="foo{0}".format(i),
                start_seconds=0)
            for i in range(0, 5)
        ]

        other_comments = [
            TimedVideoComment.add_root(
                video=self.video_2,
                user=self.user,
                text="bar{0}".format(i),
                start_seconds=0)
            for i in range(0, 5)
        ]

        # add some replies to the first root comment
        replies = [
            comment.add_reply("baz{0}".format(i), self.admin)
            for i, comment in enumerate(expected_comments)
        ]

        request = VideoEntityContainer.combined_message_class(
            project_id=self.project.pk, youtube_id=self.video.youtube_id)

        with self.assertNumQueries(6):
            response = self.api.list_comments(request)

        self.assertEqual(len(expected_comments), len(response.items))

        first_comment_obj, reply_comment_obj = expected_comments[0], replies[0]

        first_comment = response.items[0]
        self.assertEqual(first_comment_obj.text, first_comment.text)
        self.assertEqual(first_comment_obj.user_id, first_comment.user.id)
        self.assertTrue(first_comment.modified)
        self.assertEqual(
            first_comment_obj.start_seconds, first_comment.start_seconds)
        self.assertEqual(
            first_comment_obj.video.youtube_id, first_comment.youtube_id)
        self.assertEqual(
            first_comment_obj.video.youtube_video.duration, first_comment.duration)
        self.assertEqual(
            first_comment_obj.video.project_id, first_comment.project_id)

        self.assertEqual(1, len(first_comment.replies))
        self.assertEqual(
            reply_comment_obj.text, first_comment.replies[0].text)
        self.assertTrue(first_comment.replies[0].modified)
        self.assertEqual(
            reply_comment_obj.user_id, first_comment.replies[0].user.id)
        self.assertEqual(
            reply_comment_obj.start_seconds,
            first_comment.replies[0].start_seconds)
        self.assertEqual(
            reply_comment_obj.video.youtube_id,
            first_comment.replies[0].youtube_id)
        self.assertEqual(
            reply_comment_obj.video.project_id,
            first_comment.replies[0].project_id)

    def test_get_comment(self):
        """
            Get a comment thread
        """
        self._sign_in(self.user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)

        replies = [
            comment.add_reply("baz{0}".format(i), self.admin)
            for i in range(0, 5)
        ]

        request = VideoCommentEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk)

        with self.assertNumQueries(7):
            response = self.api.get_comment(request)

        self.assertEqual(comment.text, response.text)
        self.assertEqual(comment.user_id, response.user.id)
        self.assertTrue(response.modified)
        self.assertEqual(comment.video.youtube_id, response.youtube_id)
        self.assertEqual(comment.video.youtube_video.duration, response.duration)
        self.assertEqual(comment.video.project_id, response.project_id)
        self.assertEqual(5, len(response.replies))
        self.assertEqual(
            replies[0].text, response.replies[0].text)
        self.assertTrue(response.replies[0].modified)
        self.assertEqual(
            replies[0].user_id, response.replies[0].user.id)
        self.assertEqual(
            replies[0].start_seconds, response.replies[0].start_seconds)

    def test_create_root_comment(self):
        """
            Create comment thread
        """
        self._sign_in(self.user)

        request = CreateVideoRootCommentContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            text="foo",
            start_seconds=42.0)

        with self.assertEventRecorded(
                EventKind.TIMEDVIDEOROOTCOMMENTCREATED,
                object_id=True,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(10):
            response = self.api.create_root_comment(request)

        comment = TimedVideoComment.objects.get(pk=response.id)

        self.assertEqual(self.user.pk, comment.user.pk)
        self.assertEqual(request.start_seconds, comment.start_seconds)
        self.assertEqual(request.text, comment.text)

    def test_create_reply(self):
        """
            Create reply on a commnent thread
        """
        self._sign_in(self.user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)

        request = CreateVideoCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.id,
            text="foobar")

        with self.assertEventRecorded(
                EventKind.TIMEDVIDEOREPLYCOMMENTCREATED,
                object_id=True,
                video_id=self.video.pk,
                project_id=self.project.pk,
                meta=str(comment.id)), self.assertNumQueries(11):
            response = self.api.create_comment_reply(request)

        reply = self.reload(comment).get_replies()[0]
        self.assertEqual(self.user.pk, reply.user.pk)
        self.assertEqual(request.text, reply.text)
        self.assertEqual(comment.start_seconds, reply.start_seconds)

        self.assertEqual(reply.text, response.text)
        self.assertEqual(reply.user_id, response.user.id)
        self.assertEqual(reply.project_id, self.project.pk)
        self.assertEqual(comment.pk, response.thread_id)

    def test_create_reply_to_reply(self):
        """
            Create a reply to a reply
        """
        self._sign_in(self.user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)
        reply = comment.add_reply("baz", self.admin)

        request = CreateVideoCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=reply.id,
            text="foobar")

        self.assertRaises(
            BadRequestException,
            self.api.create_comment_reply,
            request
        )

    def test_update_comment(self):
        """
            Update a root comment
        """
        self._sign_in(self.user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)

        replies = [
            comment.add_reply("baz{0}".format(i), self.admin)
            for i in range(0, 5)
        ]

        request = UpdateVideoCommentContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk,
            text="bar",
            start_seconds=42.0)

        with self.assertEventRecorded(
                EventKind.TIMEDVIDEOCOMMENTUPDATED,
                object_id=comment.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(12):
            response = self.api.update_comment(request)

        comment = self.reload(comment)

        self.assertEqual(request.text, comment.text)
        self.assertEqual(request.start_seconds, comment.start_seconds)

        replies = TimedVideoComment.objects.filter(
            pk__in=[t.pk for t in replies])

        for reply in replies:
            self.assertEqual(request.start_seconds, reply.start_seconds)

    def test_update_reply(self):
        """
            Update a comment reply
        """
        self._sign_in(self.user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.admin, text="foo", start_seconds=0)
        reply = comment.add_reply("baz", self.user)

        request = UpdateVideoCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk,
            reply_id=reply.pk,
            text="bar"
        )

        with self.assertEventRecorded(
                EventKind.TIMEDVIDEOREPLYCOMMENTUPDATED,
                object_id=reply.pk,
                video_id=self.video.pk,
                project_id=self.project.pk,
                meta=str(comment.pk)), self.assertNumQueries(9):
            response = self.api.update_reply(request)

        reply = self.reload(reply)

        self.assertEqual(request.text, reply.text)

    def test_delete_root_complete(self):
        """
            Delete a comment thread
        """
        self._sign_in(self.user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)

        replies = [
            comment.add_reply("baz{0}".format(i), self.admin)
            for i in range(0, 5)
        ]

        request = VideoCommentEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk)

        with self.assertEventRecorded(
                EventKind.TIMEDVIDEOCOMMENTDELETED,
                object_id=comment.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(17):
            response = self.api.delete_comment(request)

        self.assertFalse(TimedVideoComment.objects.filter(
            pk__in=[comment.pk] + [
                c.pk for c in replies
            ]))

    def test_delete_reply(self):
        """
            Delete a comment reply
        """
        self._sign_in(self.admin)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)

        reply1 = comment.add_reply("baz", self.admin)
        reply2 = comment.add_reply("boo", self.user)

        request = VideoCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk,
            reply_id=reply1.pk)

        with self.assertEventRecorded(
                EventKind.TIMEDVIDEOREPLYCOMMENTDELETED,
                object_id=reply1.pk,
                video_id=self.video.pk,
                project_id=self.project.pk,
                meta=str(comment.pk)), self.assertNumQueries(12):
            response = self.api.delete_reply(request)

        self.assertObjectAbsent(reply1)
        self.assertTrue(TimedVideoComment.objects.filter(pk=comment.pk))
        self.assertTrue(TimedVideoComment.objects.filter(pk=reply2.pk))

    def test_update_unauthorized(self):
        """
            Update a comment that a different user created
        """
        other_user = milkman.deliver(
            get_user_model(), email="other@example.com")

        self._sign_in(other_user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)

        request = UpdateVideoCommentContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk,
            text="bar",
            start_seconds=42.0)

        self.assertRaises(
            ForbiddenException,
            self.api.update_comment,
            request)

    def test_update_reply_unauthorized(self):
        """
            Update a comment reply that a different user created
        """
        other_user = milkman.deliver(
            get_user_model(), email="other@example.com")

        self._sign_in(other_user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)
        reply = comment.add_reply("baz", self.admin)

        request = UpdateVideoCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk,
            reply_id=reply.pk,
            text="bar")

        self.assertRaises(
            ForbiddenException,
            self.api.update_reply,
            request)

    def test_delete_unauthorized(self):
        """
            Delete a comment that another user created
        """
        other_user = milkman.deliver(
            get_user_model(), email="other@example.com")

        self._sign_in(other_user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)

        request = VideoCommentEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk)

        self.assertRaises(
            ForbiddenException,
            self.api.delete_comment,
            request)

    def test_delete_reply_unauthorized(self):
        """
            Delete a reply that another user created
        """
        other_user = milkman.deliver(
            get_user_model(), email="other@example.com")

        self._sign_in(other_user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)
        reply1 = comment.add_reply("baz", self.admin)

        request = VideoCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk,
            reply_id=reply1.pk)

        self.assertRaises(
            ForbiddenException,
            self.api.delete_reply,
            request)

    def test_patch_text(self):
        """
            Patch the text of a comment
        """
        self._sign_in(self.user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=42)

        initial_seconds = comment.start_seconds

        request = UpdateVideoCommentContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk,
            text="bar")

        with self.assertEventRecorded(
                EventKind.TIMEDVIDEOCOMMENTUPDATED,
                object_id=comment.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(8):
            response = self.api.patch_comment(request)

        comment = self.reload(comment)

        self.assertEqual(request.text, comment.text)
        self.assertEqual(initial_seconds, comment.start_seconds)

    def test_patch_time(self):
        """
            Patch the time of a comment
        """
        self._sign_in(self.user)

        comment = TimedVideoComment.add_root(
            video=self.video, user=self.user, text="foo", start_seconds=0)

        initial_text = comment.text

        replies = [
            comment.add_reply("baz{0}".format(i), self.admin)
            for i in range(0, 5)
        ]

        request = UpdateVideoCommentContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            comment_id=comment.pk,
            start_seconds=42.0)

        with self.assertEventRecorded(
                EventKind.TIMEDVIDEOCOMMENTUPDATED,
                object_id=comment.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(12):
            response = self.api.patch_comment(request)

        comment = self.reload(comment)

        self.assertEqual(initial_text, comment.text)
        self.assertEqual(request.start_seconds, comment.start_seconds)

        replies = TimedVideoComment.objects.filter(
            pk__in=[t.pk for t in replies])

        for reply in replies:
            self.assertEqual(request.start_seconds, reply.start_seconds)

"""
    Video deletion tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
from milkman.dairy import milkman
from django.utils import timezone

from greenday_core.api_exceptions import ForbiddenException
from greenday_core.constants import EventKind
from greenday_core.models import (
    Video,
    Project,
)

from ..base import ApiTestCase, TestEventBusMixin

from ...video.video_api import VideoAPI
from ...video.containers import (
    VideoEntityContainer,
    VideoBatchContainer
)

class VideoDeleteTests(TestEventBusMixin, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_delete <greenday_api.video.video_api.VideoAPI.video_delete>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap data
        """
        super(VideoDeleteTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(
            project=self.project)

    def test_only_owners_and_admins_can_delete_videos(self):
        """
            Video creation permissions
        """
        # A normal user
        self._sign_in(self.user)
        self.assertRaises(
            ForbiddenException,
            self.api.video_delete,
            VideoEntityContainer.combined_message_class(
                youtube_id=self.video.youtube_id, project_id=self.project.pk)
        )

        # The owner
        self._sign_in(self.admin)

        with self.assertEventRecorded(
                EventKind.VIDEODELETED,
                object_id=self.video.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(17):
            self.api.video_delete(
                VideoEntityContainer.combined_message_class(
                    youtube_id=self.video.youtube_id, project_id=self.project.pk)
            )
        self.assertObjectAbsent(self.video, Video.objects)

    def test_delete_archived(self):
        """
            Delete an archived video
        """
        archived_video = self.create_video(
            project=self.project, user=self.user,
            archived_at=timezone.now())

        self._sign_in(self.user)

        with self.assertEventRecorded(
                EventKind.VIDEODELETED,
                object_id=archived_video.pk,
                video_id=archived_video.pk,
                project_id=self.project.pk), self.assertNumQueries(17):
            self.api.video_delete(
                VideoEntityContainer.combined_message_class(
                    youtube_id=archived_video.youtube_id, project_id=self.project.pk)
            )

        self.assertObjectAbsent(archived_video, Video.objects)


class VideoBatchDeleteTests(TestEventBusMixin, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_batch_delete <greenday_api.video.video_api.VideoAPI.video_batch_delete>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap data
        """
        super(VideoBatchDeleteTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(
            project=self.project, user=self.user)
        self.video2 = self.create_video(
            project=self.project, user=self.user)
        self.archived_video = self.create_video(
            project=self.project, user=self.user,
            archived_at=timezone.now())

    def test_video_batch_delete(self):
        """
            Delete a list of videos
        """
        self._sign_in(self.user)

        request = VideoBatchContainer.combined_message_class(
            project_id=self.project.pk, youtube_ids=(
                self.video.youtube_id, self.video2.youtube_id, self.archived_video.youtube_id)
        )

        with self.assertNumQueries(25):
            response = self.api.video_batch_delete(request)

        for vid in (self.video, self.video2, self.archived_video,):
            item = next(i for i in response.items if i.youtube_id == vid.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertTrue(item.success)

        self.assertEqual(0, Video.objects.count())
        # self.assertEqual(3, Video.trash.count())

    def test_video_batch_delete_video_does_not_exist(self):
        """
            Delete a non-existant video
        """
        self._sign_in(self.user)

        request = VideoBatchContainer.combined_message_class(
            project_id=self.project.pk, youtube_ids=(self.video.youtube_id, "9999")
        )

        with self.assertNumQueries(17):
            response = self.api.video_batch_delete(request)

        self.assertEqual(response.items[0].youtube_id, self.video.youtube_id)
        self.assertEqual(response.items[1].youtube_id, '9999')
        self.assertEqual(response.items[0].msg, 'ok')
        self.assertEqual(
            response.items[1].msg, 'Video with youtube_id 9999 does not exist')
        self.assertTrue(response.items[0].success)
        self.assertFalse(response.items[1].success)

        self.assertEqual(1, Video.objects.count())
        # self.assertEqual(1, Video.trash.count())

    def test_video_batch_delete_video_already_trashed(self):
        """
            Delete a previously deleted video
        """
        self._sign_in(self.user)

        self.video2.delete()

        request = VideoBatchContainer.combined_message_class(
            project_id=self.project.pk, youtube_ids=(
                self.video.youtube_id, self.video2.youtube_id)
        )

        with self.assertNumQueries(17):
            response = self.api.video_batch_delete(request)

        self.assertEqual(response.items[0].youtube_id, self.video.youtube_id)
        self.assertEqual(response.items[1].youtube_id, self.video2.youtube_id)
        self.assertEqual(response.items[0].msg, 'ok')
        self.assertEqual(
            response.items[1].msg,
            'Video with youtube_id %s does not exist' % self.video2.youtube_id)
        self.assertTrue(response.items[0].success)
        self.assertFalse(response.items[1].success)

        self.assertEqual(0, Video.objects.count())
        # self.assertEqual(2, Video.trash.count())

    def test_video_batch_delete_permission_denied(self):
        """
            Delete a video which current user does not have permission to delete
        """
        self._sign_in(self.user)

        self.project.add_assigned(self.user2, pending=False)
        self.video2.user = self.user2
        self.video2.save()

        request = VideoBatchContainer.combined_message_class(
            project_id=self.project.pk, youtube_ids=(
                self.video.youtube_id, self.video2.youtube_id)
        )

        with self.assertNumQueries(17):
            response = self.api.video_batch_delete(request)

        self.assertEqual(response.items[0].youtube_id, self.video.youtube_id)
        self.assertEqual(response.items[1].youtube_id, self.video2.youtube_id)
        self.assertEqual(response.items[0].msg, 'ok')
        self.assertEqual(response.items[1].msg, 'Permission Denied!')
        self.assertTrue(response.items[0].success)
        self.assertFalse(response.items[1].success)

        self.assertEqual(1, Video.objects.count())
        # self.assertEqual(1, Video.trash.count())

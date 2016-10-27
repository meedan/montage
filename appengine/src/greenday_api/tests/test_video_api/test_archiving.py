"""
    Tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
# LIBRARIES
from milkman.dairy import milkman

# FRAMEWORK
from django.utils import timezone

# GREENDAY
from greenday_core.constants import EventKind
from greenday_core.models import (
    Video,
    Project,
)
from ..base import ApiTestCase, TestEventBusMixin

from ...video.video_api import VideoAPI
from ...video.containers import (
    VideoEntityContainer,
    ArchiveVideoBatchContainer
)


class VideoUnarchiveTests(TestEventBusMixin, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_unarchive <greenday_api.video.video_api.VideoAPI.video_unarchive>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoUnarchiveTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

    def test_video_unarchive(self):
        """
            Unarchive a video
        """
        self._sign_in(self.user)

        video = self.create_video(project=self.project, user=self.user,
            archived_at=timezone.now())

        request = VideoEntityContainer.combined_message_class(
            project_id=self.project.pk, youtube_id=video.youtube_id
        )

        with self.assertEventRecorded(
                EventKind.VIDEOUNARCHIVED,
                object_id=video.pk,
                video_id=video.pk,
                project_id=self.project.pk), self.assertNumQueries(6):
            self.api.video_unarchive(request)

        video = self.reload(video)
        self.assertFalse(video.archived_at)


class VideoBatchUnarchiveTests(TestEventBusMixin, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_batch_unarchive <greenday_api.video.video_api.VideoAPI.video_batch_unarchive>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoBatchUnarchiveTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(
            project=self.project,
            user=self.user,
            archived_at=timezone.now())
        self.video2 = self.create_video(
            project=self.project,
            user=self.user,
            archived_at=timezone.now())

    def test_video_batch_unarchive(self):
        """
            Unarchive list of videos
        """
        self._sign_in(self.user)

        request = ArchiveVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, unarchive=True, youtube_ids=(
                self.video.youtube_id, self.video2.youtube_id,)
        )

        event_recorder = self.assertEventRecorded([
            {
                'kind': EventKind.VIDEOUNARCHIVED,
                'object_id': video.pk,
                'video_id': video.pk,
                'project_id': self.project.pk
            }
            for video in (self.video, self.video2,)
        ])
        event_recorder.start()

        with self.assertNumQueries(8):
            response = self.api.video_batch_archive(request)

        for vid in (self.video, self.video2,):
            item = next(
                i for i in response.items if i.youtube_id == vid.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertTrue(item.success)

        self.assertEqual(2, len(response.videos))

        self.assertEqual(0, Video.archived_objects.count())
        self.assertEqual(2, Video.objects.count())

        event_recorder.do_assert()

class VideoBatchArchiveTests(TestEventBusMixin, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_batch_archive <greenday_api.video.video_api.VideoAPI.video_batch_archive>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoBatchArchiveTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(project=self.project, user=self.user)
        self.video2 = self.create_video(project=self.project, user=self.user)

    def test_video_batch_archive(self):
        """
            Test archiving list of videos
        """
        self._sign_in(self.user)

        request = ArchiveVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, youtube_ids=(
                self.video.youtube_id, self.video2.youtube_id,)
        )

        event_recorder = self.assertEventRecorded([
            {
                'kind': EventKind.VIDEOARCHIVED,
                'object_id': video.pk,
                'video_id': video.pk,
                'project_id': self.project.pk
            }
            for video in (self.video, self.video2,)
        ])
        event_recorder.start()

        with self.assertNumQueries(8):
            response = self.api.video_batch_archive(request)

        for vid in (self.video, self.video2,):
            item = next(
                i for i in response.items if i.youtube_id == vid.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertTrue(item.success)

        self.assertEqual(2, len(response.videos))

        self.assertEqual(0, Video.objects.count())
        self.assertEqual(2, Video.archived_objects.count())

        event_recorder.do_assert()

    def test_video_batch_archive_permission_denied(self):
        """
            Test archiving video as normal collaborator
        """
        self._sign_in(self.user)
        self.project.add_assigned(self.user2, pending=False)
        self.video2.user = self.user2
        self.video2.save()

        request = ArchiveVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, youtube_ids=(
                self.video.youtube_id, self.video2.youtube_id,)
        )

        with self.assertEventRecorded(
                EventKind.VIDEOARCHIVED,
                object_id=self.video.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(7):
            response = self.api.video_batch_archive(request)

        ok_item = next(
            i for i in response.items if i.youtube_id == self.video.youtube_id)
        self.assertEqual(ok_item.msg, 'ok')
        self.assertTrue(ok_item.success)

        bad_item = next(
            i for i in response.items if i.youtube_id == self.video2.youtube_id)
        self.assertEqual(bad_item.msg, 'Permission Denied!')
        self.assertFalse(bad_item.success)

        self.assertEqual(1, len(response.videos))

        self.assertEqual(1, Video.objects.count())
        self.assertEqual(1, Video.archived_objects.count())

    def test_video_batch_archive_video_already_archived(self):
        """
            Archive an archived video
        """
        self._sign_in(self.user)
        self.video2.archived_at = timezone.now()
        self.video2.save()

        request = ArchiveVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, youtube_ids=(
                self.video.youtube_id, self.video2.youtube_id,)
        )

        with self.assertEventRecorded(
                EventKind.VIDEOARCHIVED,
                object_id=self.video.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(7):
            response = self.api.video_batch_archive(request)

        ok_item = next(
            i for i in response.items if i.youtube_id == self.video.youtube_id)
        self.assertEqual(ok_item.msg, 'ok')
        self.assertTrue(ok_item.success)

        bad_item = next(
            i for i in response.items if i.youtube_id == self.video2.youtube_id)
        self.assertEqual(
            bad_item.msg,
            'Video with youtube_id %s does not exist' % self.video2.youtube_id)
        self.assertFalse(bad_item.success)

        self.assertEqual(1, len(response.videos))

        self.assertEqual(0, Video.objects.count())
        self.assertEqual(2, Video.archived_objects.count())

    def test_video_batch_archive_video_does_not_exist(self):
        """
            Archive a video that does not exist
        """
        self._sign_in(self.user)

        request = ArchiveVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, youtube_ids=(
                self.video.youtube_id, "9999",)
        )

        with self.assertEventRecorded(
                EventKind.VIDEOARCHIVED,
                object_id=self.video.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(7):
            response = self.api.video_batch_archive(request)

        ok_item = next(
            i for i in response.items if i.youtube_id == self.video.youtube_id)
        self.assertEqual(ok_item.msg, 'ok')
        self.assertTrue(ok_item.success)

        bad_item = next(
            i for i in response.items if i.youtube_id == "9999")
        self.assertEqual(bad_item.msg, 'Video with youtube_id 9999 does not exist')
        self.assertFalse(bad_item.success)

        self.assertEqual(1, len(response.videos))

        self.assertEqual(1, Video.objects.count())
        self.assertEqual(1, Video.archived_objects.count())

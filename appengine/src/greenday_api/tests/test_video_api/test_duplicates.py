"""
    Duplicate video tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
import itertools
from milkman.dairy import milkman
from django.utils import timezone

from greenday_core.api_exceptions import (
    ForbiddenException, NotFoundException, UnauthorizedException)
from greenday_core.models import (
    Project,
    DuplicateVideoMarker
)

from ..base import ApiTestCase
from ...video.video_api import VideoAPI

from ...video.containers import (
    VideoEntityContainer,
    VideoBatchContainer,
    VideoIDBatchContainer,
    VideoDuplicateEntityContainer,
)


class VideoAPITestDuplicatesList(ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_duplicates_list <greenday_api.video.video_api.VideoAPI.video_duplicates_list>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoAPITestDuplicatesList, self).setUp()

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.video = self.create_video(project=self.project)
        self.video_2 = self.create_video(project=self.project)

        DuplicateVideoMarker.add_marker(self.video, self.video_2)

    def test_video_duplicates_list_anon(self):
        """
            Get duplicates list - no current user
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.video_duplicates_list,
            VideoEntityContainer.combined_message_class(
                project_id=self.project.pk, youtube_id=self.video.youtube_id)
        )

    def test_video_duplicates_list_user_unassigned(self):
        """
            Get duplicates list - current user not assigned to project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.video_duplicates_list,
            VideoEntityContainer.combined_message_class(
                project_id=self.project.pk, youtube_id=self.video.youtube_id)
        )

    def test_video_duplicates_list_project_video_does_not_exist(self):
        """
            Get duplicates list - project or video does not exist
        """
        self._sign_in(self.admin)
        self.assertRaises(
            NotFoundException,
            self.api.video_duplicates_list,
            VideoEntityContainer.combined_message_class(
                project_id=9999)
        )

        self.assertRaises(
            NotFoundException,
            self.api.video_duplicates_list,
            VideoEntityContainer.combined_message_class(
                project_id=self.project.pk, youtube_id="9999")
        )

    def test_video_duplicates_list_ok(self):
        """
            Get duplicates list
        """
        self._sign_in(self.admin)

        with self.assertNumQueries(5):
            response = self.api.video_duplicates_list(
                VideoEntityContainer.combined_message_class(
                    project_id=self.project.pk, youtube_id=self.video.youtube_id)
            )
        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_2.pk, response.items[0].id)


class VideoAPITestMarkDuplicate(ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_mark_duplicate <greenday_api.video.video_api.VideoAPI.video_mark_duplicate>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoAPITestMarkDuplicate, self).setUp()

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.video = self.create_video(project=self.project)
        self.video_2 = self.create_video(project=self.project)

    def test_video_mark_duplicate_anon(self):
        """
            Mark duplicate video - no user logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.video_mark_duplicate,
            VideoDuplicateEntityContainer.combined_message_class(
                youtube_id=self.video_2.youtube_id, project_id=self.project.pk,
                duplicate_of_id=self.video.youtube_id)
        )

    def test_video_mark_duplicate_user_unassigned(self):
        """
            Mark duplicate video - current user not assigned to project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.video_mark_duplicate,
            VideoDuplicateEntityContainer.combined_message_class(
                youtube_id=self.video_2.youtube_id, project_id=self.project.pk,
                duplicate_of_id=self.video.youtube_id)
        )

    def test_video_mark_duplicate_project_does_not_exist(self):
        """
            Mark duplicate video - project does not exist
        """
        self._sign_in(self.admin)
        self.assertRaises(
            NotFoundException,
            self.api.video_mark_duplicate,
            VideoDuplicateEntityContainer.combined_message_class(
                youtube_id=self.video_2.youtube_id, project_id=9999,
                duplicate_of_id=self.video.youtube_id)
        )

    def test_video_mark_duplicate_video_does_not_exist(self):
        """
            Mark duplicate video - video does not exist
        """
        self._sign_in(self.admin)
        self.assertRaises(
            NotFoundException,
            self.api.video_mark_duplicate,
            VideoDuplicateEntityContainer.combined_message_class(
                youtube_id="9999", project_id=self.project.pk,
                duplicate_of_id=self.video.youtube_id)
        )

    def test_video_mark_duplicate_duplicate_video_does_not_exist(self):
        """
            Mark duplicate video - other video does not exist
        """
        self._sign_in(self.admin)
        self.assertRaises(
            NotFoundException,
            self.api.video_mark_duplicate,
            VideoDuplicateEntityContainer.combined_message_class(
                youtube_id=self.video_2.youtube_id, project_id=self.project.pk,
                duplicate_of_id="9999")
        )

    def test_video_mark_duplicate_mark_self(self):
        """
            Mark a video as duplicate of itself
        """
        self._sign_in(self.admin)
        self.assertRaises(
            ForbiddenException,
            self.api.video_mark_duplicate,
            VideoDuplicateEntityContainer.combined_message_class(
                youtube_id=self.video_2.youtube_id, project_id=self.project.pk,
                duplicate_of_id=self.video_2.youtube_id)
        )

    def test_video_mark_duplicate_ok(self):
        """
            Mark a video as a duplicate of another
        """
        self._sign_in(self.admin)
        with self.assertNumQueries(8):
            response = self.api.video_mark_duplicate(
                VideoDuplicateEntityContainer.combined_message_class(
                    youtube_id=self.video_2.youtube_id, project_id=self.project.pk,
                    duplicate_of_id=self.video.youtube_id)
            )
        self.assertEqual(response.id, self.video.pk)

        self.assertEqual(self.video, self.video_2.get_duplicates()[0])
        self.assertEqual(self.video_2, self.video.get_duplicates()[0])


class VideoAPIBatchMarkAsDuplicateTests(ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_batch_mark_as_duplicate <greenday_api.video.video_api.VideoAPI.video_batch_mark_as_duplicate>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoAPIBatchMarkAsDuplicateTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(project=self.project)
        self.video_2 = self.create_video(project=self.project)
        self.video_3 = self.create_video(project=self.project)
        self.archived_video = self.create_video(
            project=self.project, archived_at=timezone.now())

        self.all_live_videos = (self.video, self.video_2, self.video_3,)

    def test_batch_mark_as_duplicate_ok(self):
        """
            Mark a list of videos as duplicates of each other
        """
        self._sign_in(self.user)

        request = VideoBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_ids=[v.youtube_id for v in self.all_live_videos]
        )

        with self.assertNumQueries(6):
            response = self.api.video_batch_mark_as_duplicate(request)

        self.assertEqual(len(self.all_live_videos), len(response.videos))

        for video in self.all_live_videos:
            item = next(i for i in response.items if i.youtube_id == video.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertEqual(item.success, True)

            other_ids = set(v.pk for v in self.all_live_videos if v != video)
            self.assertEqual(
                other_ids, set(video.get_duplicates(ids_only=True)))

    def test_batch_mark_as_duplicate_not_found(self):
        """
            One video does not exist
        """
        self._sign_in(self.user)

        request = VideoBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_ids=[v.youtube_id for v in self.all_live_videos] + ["999"]
        )

        with self.assertNumQueries(6):
            response = self.api.video_batch_mark_as_duplicate(request)

        self.assertEqual(len(self.all_live_videos), len(response.videos))
        self.assertEqual(len(self.all_live_videos)+1, len(response.items))

        item = next(i for i in response.items if i.youtube_id == '999')
        self.assertEqual(item.msg, 'Video with youtube_id 999 does not exist')
        self.assertEqual(item.success, False)

    def test_batch_mark_as_duplicate_archived(self):
        """
            One video is archived
        """
        self._sign_in(self.user)

        request = VideoBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_ids=[v.youtube_id for v in self.all_live_videos] +
            [self.archived_video.youtube_id]
        )

        with self.assertNumQueries(6):
            response = self.api.video_batch_mark_as_duplicate(request)

        self.assertEqual(len(self.all_live_videos), len(response.videos))
        self.assertEqual(len(self.all_live_videos)+1, len(response.items))

        item = next(
            i for i in response.items if i.youtube_id == self.archived_video.youtube_id)
        self.assertEqual(item.msg, 'Video with youtube_id {0} does not exist'.format(
            self.archived_video.youtube_id))
        self.assertEqual(item.success, False)

    def test_batch_mark_as_duplicate_existing_markers(self):
        """
            Two videos are already marked as duplicates
        """
        self._sign_in(self.user)

        DuplicateVideoMarker.add_marker(self.video, self.video_2)
        DuplicateVideoMarker.add_marker(self.video, self.video_3)

        request = VideoBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_ids=[v.youtube_id for v in self.all_live_videos]
        )

        with self.assertNumQueries(6):
            response = self.api.video_batch_mark_as_duplicate(request)

        self.assertEqual(len(self.all_live_videos), len(response.videos))

        for video in self.all_live_videos:
            item = next(i for i in response.items if i.youtube_id == video.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertEqual(item.success, True)

            other_ids = set(v.pk for v in self.all_live_videos if v != video)
            self.assertEqual(
                other_ids, set(video.get_duplicates(ids_only=True)))


class VideoAPIBatchDeleteDuplicateMarkTests(ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_batch_delete_duplicate_marker <greenday_api.video.video_api.VideoAPI.video_batch_delete_duplicate_marker>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoAPIBatchDeleteDuplicateMarkTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(project=self.project)
        self.video_2 = self.create_video(project=self.project)
        self.video_3 = self.create_video(project=self.project)

        self.all_live_videos = (self.video, self.video_2, self.video_3,)

        for vid1, vid2 in itertools.combinations(self.all_live_videos, 2):
            DuplicateVideoMarker.add_marker(vid1, vid2)

    def test_batch_remove_duplicate_markers_ok(self):
        """
            Mark list of videos as not being duplicates of each other
        """
        self._sign_in(self.user)

        request = VideoIDBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            youtube_ids=(self.video_2.youtube_id, self.video_3.youtube_id,)
        )

        with self.assertNumQueries(7):
            response = self.api.video_batch_delete_duplicate_marker(request)

        self.assertEqual(2, len(response.videos))

        for video in (self.video_2, self.video_3,):
            item = next(i for i in response.items if i.youtube_id == video.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertTrue(item.success)

            self.assertEqual(1, len(video.get_duplicates()))

        self.assertEqual(0, len(self.video.get_duplicates()))

    def test_batch_remove_duplicate_markers_not_found(self):
        """
            One video does not exist
        """
        self._sign_in(self.user)

        request = VideoIDBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            youtube_ids=(
                self.video_2.youtube_id, self.video_3.youtube_id, "999",)
        )

        with self.assertNumQueries(7):
            response = self.api.video_batch_delete_duplicate_marker(request)

        self.assertEqual(2, len(response.videos))
        self.assertEqual(3, len(response.items))

        item = next(i for i in response.items if i.youtube_id == '999')
        self.assertEqual(item.msg, 'Video with youtube_id 999 does not exist')
        self.assertFalse(item.success)

    def test_batch_remove_duplicate_markers_missing_markers(self):
        """
            Not all videos passed are marked as duplicates
        """
        self._sign_in(self.user)

        DuplicateVideoMarker.objects.filter(
            video_1=self.video,
            video_2=self.video_2).delete()

        request = VideoIDBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            youtube_ids=(self.video_2.youtube_id, self.video_3.youtube_id,)
        )

        with self.assertNumQueries(7):
            response = self.api.video_batch_delete_duplicate_marker(request)

        self.assertEqual(2, len(response.videos))

        not_dupe_video = next(
            i for i in response.items if i.youtube_id == self.video_2.youtube_id)
        self.assertEqual(
            not_dupe_video.msg,
            'Video with youtube_id {0} is not marked as a duplicate'.format(
                self.video_2.youtube_id))
        self.assertFalse(not_dupe_video.success)
        self.assertEqual(1, len(self.video_2.get_duplicates()))

        dupe_video = next(
            i for i in response.items if i.youtube_id == self.video_3.youtube_id)
        self.assertEqual(dupe_video.msg, 'ok')
        self.assertTrue(dupe_video.success)
        self.assertEqual(1, len(self.video_3.get_duplicates()))


class VideoAPIBatchMarkVideoAsDuplicateTests(ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_batch_mark_video_as_duplicate <greenday_api.video.video_api.VideoAPI.video_batch_mark_video_as_duplicate>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoAPIBatchMarkVideoAsDuplicateTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(project=self.project)
        self.video_2 = self.create_video(project=self.project)
        self.video_3 = self.create_video(project=self.project)
        self.archived_video = self.create_video(
            project=self.project, archived_at=timezone.now())

    def test_batch_mark_as_duplicate_ok(self):
        """
            Mark a video as a duplicate of a list of other videos
        """
        self._sign_in(self.user)

        request = VideoIDBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            youtube_ids=[v.youtube_id for v in (self.video_2, self.video_3,)]
        )

        with self.assertNumQueries(7):
            response = self.api.video_batch_mark_video_as_duplicate(request)

        self.assertEqual(2, len(response.videos))

        item_2 = next(i for i in response.items if i.youtube_id == self.video_2.youtube_id)
        self.assertEqual(item_2.msg, 'ok')
        self.assertTrue(item_2.success)

        self.assertEqual(
            self.video.pk, self.video_2.get_duplicates(ids_only=True)[0])

        item_3 = next(i for i in response.items if i.youtube_id == self.video_3.youtube_id)
        self.assertEqual(item_3.msg, 'ok')
        self.assertTrue(item_3.success)

        self.assertEqual(
            self.video.pk, self.video_3.get_duplicates(ids_only=True)[0])

    def test_batch_mark_as_duplicate_not_found(self):
        """
            One video not found
        """
        self._sign_in(self.user)

        request = VideoIDBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            youtube_ids=(self.video_2.youtube_id, self.video_3.youtube_id, "999",)
        )

        with self.assertNumQueries(7):
            response = self.api.video_batch_mark_video_as_duplicate(request)

        self.assertEqual(2, len(response.videos))
        self.assertEqual(3, len(response.items))

        item = next(i for i in response.items if i.youtube_id == '999')
        self.assertEqual(item.msg, 'Video with youtube_id 999 does not exist')
        self.assertFalse(item.success)

    def test_batch_mark_as_duplicate_archived(self):
        """
            One video archived
        """
        self._sign_in(self.user)

        request = VideoIDBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            youtube_ids=(
                self.video_2.youtube_id, self.video_3.youtube_id, self.archived_video.youtube_id,)
        )

        with self.assertNumQueries(7):
            response = self.api.video_batch_mark_video_as_duplicate(request)

        self.assertEqual(2, len(response.videos))
        self.assertEqual(3, len(response.items))

        item = next(
            i for i in response.items if i.youtube_id == self.archived_video.youtube_id)
        self.assertEqual(item.msg, 'Video with youtube_id {0} does not exist'.format(
            self.archived_video.youtube_id))
        self.assertFalse(item.success)

    def test_batch_mark_as_duplicate_existing_markers(self):
        """
            Video already marked as duplicate with one of the videos
        """
        self._sign_in(self.user)

        DuplicateVideoMarker.add_marker(self.video, self.video_2)

        request = VideoIDBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            youtube_ids=(self.video_2.youtube_id, self.video_3.youtube_id,)
        )

        with self.assertNumQueries(7):
            response = self.api.video_batch_mark_video_as_duplicate(request)

        self.assertEqual(2, len(response.videos))

        item_2 = next(i for i in response.items if i.youtube_id == self.video_2.youtube_id)
        self.assertEqual(item_2.msg, 'ok')
        self.assertTrue(item_2.success)

        self.assertEqual(1, len(self.video_2.get_duplicates()))
        self.assertEqual(
            self.video.pk, self.video_2.get_duplicates(ids_only=True)[0])

        item_3 = next(i for i in response.items if i.youtube_id == self.video_3.youtube_id)
        self.assertEqual(item_3.msg, 'ok')
        self.assertTrue(item_3.success)

        self.assertEqual(1, len(self.video_2.get_duplicates()))
        self.assertEqual(
            self.video.pk, self.video_3.get_duplicates(ids_only=True)[0])

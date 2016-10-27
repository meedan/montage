"""
    Favourite video tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
from milkman.dairy import milkman

from greenday_core.api_exceptions import (
    ForbiddenException, UnauthorizedException, NotFoundException)
from greenday_core.models import Video, Project

from ..base import ApiTestCase, TestEventBusMixin

from ...video.video_api import VideoAPI
from ...video.containers import(
    VideoBooleanFlagEntityContainer,
    VideoFavouriteBatchContainer,
)


class VideoAPIFavouriteTests(TestEventBusMixin, ApiTestCase):
    """
        Tests for :class:`greenday_api.video.video_api.VideoAPI <greenday_api.video.video_api.VideoAPI>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoAPIFavouriteTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(project=self.project)
        self.video2 = self.create_video(project=self.project)

    def test_video_set_favourite_anon(self):
        """
            User not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.video_set_favourite,
            VideoBooleanFlagEntityContainer.combined_message_class(
                youtube_id=self.video.youtube_id, project_id=self.project.pk,
                value=True)
        )

    def test_video_set_favourite_user_unassigned(self):
        """
            User not assigned to project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.video_set_favourite,
            VideoBooleanFlagEntityContainer.combined_message_class(
                youtube_id=self.video.youtube_id, project_id=self.project.pk,
                value=True)
        )

    def test_video_set_favourite_project_does_not_exist(self):
        """
            Project does not exist
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.video_set_favourite,
            VideoBooleanFlagEntityContainer.combined_message_class(
                youtube_id=self.video.youtube_id, project_id=9999,
                value=True)
        )

    def test_video_set_favourite_video_does_not_exist(self):
        """
            Video does not exist
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.video_set_favourite,
            VideoBooleanFlagEntityContainer.combined_message_class(
                youtube_id="9999", project_id=self.project.pk,
                value=True)
        )

    def test_video_set_favourite_ok(self):
        """
            Mark video as a favourite for this project
        """
        self._sign_in(self.user)

        with self.assertNumQueries(5):
            response = self.api.video_set_favourite(
                VideoBooleanFlagEntityContainer.combined_message_class(
                    youtube_id=self.video.youtube_id,
                    project_id=self.project.pk,
                    value=True)
            )
        self.video = self.reload(self.video)
        self.assertTrue(self.video.favourited)
        self.assertTrue(response.favourited)

    def test_video_user_batch_mark_favourite(self):
        """
            Mark list of videos as favourites on this project
        """
        self._sign_in(self.user)

        request = VideoFavouriteBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_ids=[self.video.youtube_id, self.video2.youtube_id],
            value=True,
        )

        with self.assertNumQueries(5):
            response = self.api.video_batch_mark_favourite(request)

        for video in (self.video, self.video2,):
            item = next(
                i for i in response.items if i.youtube_id == video.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertTrue(item.success)

        self.assertEqual(2, Video.objects.filter(
            favourited=True).count())

    def test_video_user_batch_mark_unfavourite(self):
        """
            Mark list of videos as not favourites on this project
        """
        self._sign_in(self.user)

        for video in (self.video, self.video2,):
            video.favourited = True
            video.save()

        request = VideoFavouriteBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_ids=[self.video.youtube_id, self.video2.youtube_id],
            value=False,
        )

        with self.assertNumQueries(5):
            response = self.api.video_batch_mark_favourite(request)

        for video in (self.video, self.video2,):
            item = next(
                i for i in response.items if i.youtube_id == video.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertTrue(item.success)

        self.assertEqual(2, Video.objects.filter(
            favourited=False).count())

    def test_video_user_batch_mark_favourite_video_does_not_exist(self):
        """
            One video does not exist
        """
        self._sign_in(self.user)
        request = VideoFavouriteBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_ids=[self.video.youtube_id, "9999"],
            value=True
        )

        with self.assertNumQueries(5):
            response = self.api.video_batch_mark_favourite(request)

        ok_item = next(
            i for i in response.items if i.youtube_id == self.video.youtube_id)
        self.assertEqual(ok_item.msg, 'ok')
        self.assertTrue(ok_item.success)

        bad_item = next(
            i for i in response.items if i.youtube_id == '9999')
        self.assertEqual(
            bad_item.msg, 'Video with youtube_id 9999 does not exist')
        self.assertFalse(bad_item.success)

        self.assertEqual(1, Video.objects.filter(favourited=True).count())


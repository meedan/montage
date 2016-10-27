# coding: utf-8
"""
    Video tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
# LIBRARIES
from milkman.dairy import milkman

# GREENDAY
from greenday_core.api_exceptions import (
    ForbiddenException, UnauthorizedException, NotFoundException)
from greenday_core.models import (
    Project,
    UserVideoDetail,
)
from ..base import ApiTestCase

from ...video.video_api import VideoAPI
from ...video.containers import VideoBooleanFlagEntityContainer


class VideoUnarchiveTests(ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_user_mark_watched <greenday_api.video.video_api.VideoAPI.video_user_mark_watched>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap data
        """
        super(VideoUnarchiveTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

    def test_video_user_mark_watched_anon(self):
        """
            Mark video watched without being logged in
        """
        video = self.create_video(project=self.project)
        self.assertRaises(
            UnauthorizedException,
            self.api.video_user_mark_watched,
            VideoBooleanFlagEntityContainer.combined_message_class(
                youtube_id=video.youtube_id, project_id=self.project.pk,
                value=True)
        )

    def test_video_user_mark_watched_user_unassigned(self):
        """
            Mark video watched on project user is not assigned to
        """
        video = self.create_video(project=self.project)
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.video_user_mark_watched,
            VideoBooleanFlagEntityContainer.combined_message_class(
                youtube_id=video.youtube_id, project_id=self.project.pk,
                value=True)
        )

    def test_video_user_mark_watched_project_does_not_exist(self):
        """
            Mark video as watched on project that does not exist
        """
        video = self.create_video(project=self.project)
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.video_user_mark_watched,
            VideoBooleanFlagEntityContainer.combined_message_class(
                youtube_id=video.youtube_id, project_id=9999,
                value=True)
        )

    def test_video_user_mark_watched_video_does_not_exist(self):
        """
            Mark non-existant video as watched
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.video_user_mark_watched,
            VideoBooleanFlagEntityContainer.combined_message_class(
                youtube_id="9999", project_id=self.project.pk,
                value=True)
        )

    def test_video_user_mark_watched_user_video_detail_exists(self):
        """
            Mark video as watched where user already has database
            relation with the video
        """
        # if a user video detail already exists for the user on
        # the video then that should be updated
        video = self.create_video(project=self.project)
        milkman.deliver(
            UserVideoDetail, user=self.user, video=video, watched=True)
        self.assertEqual(1, len(UserVideoDetail.objects.all()))
        self._sign_in(self.user)

        with self.assertNumQueries(6):
            response = self.api.video_user_mark_watched(
                VideoBooleanFlagEntityContainer.combined_message_class(
                    youtube_id=video.youtube_id, project_id=self.project.pk,
                    value=False)
            )
        self.assertEqual(1, len(UserVideoDetail.objects.all()))
        self.assertEqual(response.watched, False)
        self.assertEqual(response.user_id, self.user.pk)

    def test_video_user_mark_watched_ok(self):
        """
            Mark video as watched
        """
        # if a user video detail does not exist for the user on
        # the video then one should be created
        video = self.create_video(project=self.project)
        self.assertEqual(0, len(UserVideoDetail.objects.all()))
        self._sign_in(self.user)

        with self.assertNumQueries(6):
            response = self.api.video_user_mark_watched(
                VideoBooleanFlagEntityContainer.combined_message_class(
                    youtube_id=video.youtube_id, project_id=self.project.pk,
                    value=True)
            )
        self.assertEqual(1, len(UserVideoDetail.objects.all()))
        self.assertEqual(response.watched, True)
        self.assertEqual(response.user_id, self.user.pk)

    def test_video_user_mark_watched_ok_archived(self):
        """
            Mark an archived video as watched
        """
        video = self.create_video(project=self.project)
        video.archive()
        self.assertEqual(0, len(UserVideoDetail.objects.all()))
        self._sign_in(self.user)

        with self.assertNumQueries(7):
            response = self.api.video_user_mark_watched(
                VideoBooleanFlagEntityContainer.combined_message_class(
                    youtube_id=video.youtube_id, project_id=self.project.pk,
                    value=True)
            )
        self.assertEqual(1, len(UserVideoDetail.objects.all()))
        self.assertEqual(response.watched, True)
        self.assertEqual(response.user_id, self.user.pk)

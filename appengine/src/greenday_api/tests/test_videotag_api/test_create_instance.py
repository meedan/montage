"""
    Tests for :mod:`greenday_api.videotag.videotag_api <greenday_api.video.videotag_api>`
"""
# import lib deps
from milkman.dairy import milkman

# import project deps
from greenday_core.api_exceptions import (
    BadRequestException,
    ForbiddenException,
    UnauthorizedException,
    NotFoundException
)
from greenday_core.models import (
    Project, GlobalTag, VideoTag, VideoTagInstance
)
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...videotag.videotag_api import VideoTagAPI
from ...videotag.containers import VideoTagInstanceInsertEntityContainer
from ...videotag.messages import VideoTagInstanceResponseMessage


class VideoTagCreateInstanceTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.create_instance <greenday_api.videotag.videotag_api.VideoTagAPI.create_instance>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagCreateInstanceTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)
        self.video = self.create_video(project=self.project)
        self.video_2 = self.create_video(project=self.project)

        self.tag, self.project_tag, self.video_tag, self.video_tag_instance = \
            self.create_video_instance_tag(
                project=self.project,
                video=self.video,
                start_seconds=3,
                end_seconds=5,
                name='A')

    def test_create_instance_endpoint_anon(self):
        """
            Create tag instance - not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.create_instance,
            VideoTagInstanceInsertEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                start_seconds=1.23,
                end_seconds=2.36)
        )

    def test_create_instance_endpoint_loggedin_unassigned(self):
        """
            Create tag instance - not assigned to project
        """
        # user is logged in but not assigned to the project
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.create_instance,
            VideoTagInstanceInsertEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                start_seconds=1.23,
                end_seconds=2.36)
        )

    def test_create_instance_endpoint_logged_in_project_does_not_exist(self):
        """
            Create tag instance - project does not exist
        """
        # user is logged in and project does not exist should raise 404
        self._sign_in(self.user2)
        self.assertRaises(
            NotFoundException,
            self.api.create_instance,
            VideoTagInstanceInsertEntityContainer.
            combined_message_class(
                project_id=9999,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                start_seconds=1.23,
                end_seconds=2.36)
        )

    def test_create_instance_endpoint_logged_in_video_does_not_exist(self):
        """
            Create tag instance - video does not exist
        """
        # user is logged in and video does not exist should raise 404
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.create_instance,
            VideoTagInstanceInsertEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id="9999",
                video_tag_id=self.video_tag.pk,
                start_seconds=1.23,
                end_seconds=2.36)
        )

    def test_create_instance_endpoint_logged_in_videotag_does_not_exist(self):
        """
            Create tag instance - tag definition not associated with video
        """
        # user is logged in and video tag does not exist should raise 404
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.create_instance,
            VideoTagInstanceInsertEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=9999,
                start_seconds=1.23,
                end_seconds=2.36)
        )

    def test_create_instance_endpoint_ok(self):
        """
            Create tag instance
        """
        # user is logged in and assigned to project
        self.assertEqual(1, len(VideoTag.objects.all()))
        self.assertEqual(1, len(VideoTagInstance.objects.all()))
        self.assertEqual(1, len(GlobalTag.objects.all()))
        self._sign_in(self.user)
        response = self.api.create_instance(
            VideoTagInstanceInsertEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                start_seconds=1.23,
                end_seconds=2.36))
        self.assertEqual(2, len(VideoTagInstance.objects.all()))
        self.assertEqual(1, len(VideoTag.objects.all()))
        self.assertEqual(1, len(GlobalTag.objects.all()))
        instance = VideoTagInstance.objects.get(
            video_tag=self.video_tag,
            start_seconds=1.23, end_seconds=2.36)
        self.assertEqual(instance.pk, response.id)
        self.assertEqual(instance.start_seconds, response.start_seconds)
        self.assertEqual(instance.end_seconds, response.end_seconds)
        self.assertEqual(instance.video_tag.pk, response.video_tag_id)
        self.assertIsInstance(response, VideoTagInstanceResponseMessage)

    def test_create_instance_overlap(self):
        """
            Create tag instance overlapping another tag instance
        """
        video = self.create_video(project=self.project)
        _, _, videotag, _ = self.create_video_instance_tag(
            project_tag=self.project_tag,
            video=video,
            start_seconds=0.0,
            end_seconds=42.0)

        self._sign_in(self.user)

        request = VideoTagInstanceInsertEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=video.youtube_id,
            video_tag_id=videotag.pk,
            start_seconds=10.0,
            end_seconds=50.0)
        self.assertRaises(
            BadRequestException,
            self.api.create_instance,
            request
        )

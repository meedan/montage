"""
    Tests for :mod:`greenday_api.videotag.videotag_api <greenday_api.video.videotag_api>`
"""
# import lib deps
from milkman.dairy import milkman

# import project deps
from greenday_core.api_exceptions import (
    BadRequestException, UnauthorizedException)
from greenday_core.models import Project
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...videotag.videotag_api import VideoTagAPI
from ...videotag.containers import VideoTagInstanceUpdateEntityContainer


class VideoTagPatchInstanceTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.patch_instance <greenday_api.videotag.videotag_api.VideoTagAPI.patch_instance>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagPatchInstanceTestCase, self).setUp()
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

    def test_patch_instance_endpoint_ok(self):
        """
            Patch a tag instance
        """
        self._sign_in(self.user)

        initial_end_seconds = self.video_tag_instance.end_seconds
        self.api.patch_instance(
            VideoTagInstanceUpdateEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk,
                start_seconds=4.0))

        self.video_tag_instance = self.reload(self.video_tag_instance)
        self.assertEqual(4, self.video_tag_instance.start_seconds)
        self.assertEqual(
            initial_end_seconds, self.video_tag_instance.end_seconds)

    def test_patch_instance_endpoint_anon(self):
        """
            Patch a tag instance - user not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.patch_instance,
            VideoTagInstanceUpdateEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk)
        )

    def test_overlap_invalid(self):
        """
            Patch a tag instance - overlaps another tag
        """
        # another instance of the tag to overlap with
        self.create_video_instance_tag(
            video_tag=self.video_tag,
            start_seconds=6,
            end_seconds=9)

        self._sign_in(self.user)

        request = VideoTagInstanceUpdateEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            video_tag_id=self.video_tag.pk,
            instance_id=self.video_tag_instance.pk,
            start_seconds=3.0,
            end_seconds=9.0)

        self.assertRaises(
            BadRequestException,
            self.api.patch_instance,
            request
        )

    def test_invalid_start_end(self):
        """
            Patch a tag instance - end is before start
        """
        self._sign_in(self.user)

        request = VideoTagInstanceUpdateEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            video_tag_id=self.video_tag.pk,
            instance_id=self.video_tag_instance.pk,
            start_seconds=9.0,
            end_seconds=1.0)

        self.assertRaises(
            BadRequestException,
            self.api.patch_instance,
            request
        )

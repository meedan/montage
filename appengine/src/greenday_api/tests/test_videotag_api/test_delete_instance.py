"""
    Tests for :mod:`greenday_api.videotag.videotag_api <greenday_api.video.videotag_api>`
"""
# import lib deps
from milkman.dairy import milkman

# import project deps
from greenday_core.api_exceptions import (
    ForbiddenException, UnauthorizedException, NotFoundException)
from greenday_core.models import Project
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...videotag.videotag_api import VideoTagAPI
from ...videotag.containers import VideoTagInstanceEntityContainer


class VideoTagDeleteInstanceTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.delete_instance <greenday_api.videotag.videotag_api.VideoTagAPI.delete_instance>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagDeleteInstanceTestCase, self).setUp()
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

    def test_delete_instance_endpoint_anon(self):
        """
            Delete a tag instance - not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.delete_instance,
            VideoTagInstanceEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk)
        )

    def test_delete_instance_endpoint_loggedin_unassigned(self):
        """
            Delete a tag instance - user is logged in but not assigned to the project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.delete_instance,
            VideoTagInstanceEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk)
        )

    def test_delete_instance_endpoint_logged_in_instance_does_not_exist(self):
        """
            Delete a tag instance -  user is logged in and instance does not
            exist should raise 404
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.delete_instance,
            VideoTagInstanceEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=9999)
        )

    def test_delete_instance_endpoint_logged_in_project_does_not_exist(self):
        """
            Delete a tag instance - user is logged in and project does not
            exist should raise 404
        """
        self._sign_in(self.user2)
        self.assertRaises(
            NotFoundException,
            self.api.delete_instance,
            VideoTagInstanceEntityContainer.
            combined_message_class(
                project_id=9999,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk)
        )

    def test_delete_instance_endpoint_logged_in_video_does_not_exist(self):
        """
            Delete a tag instance -  user is logged in and video does not exist
            should raise 404
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.delete_instance,
            VideoTagInstanceEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id="9999",
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk)
        )

    def test_delete_instance_endpoint_ok(self):
        """
            Delete a tag instance
        """
        _, _, _, instance_tag = self.create_video_instance_tag(
            video_tag=self.video_tag)

        self._sign_in(self.user)
        self.api.delete_instance(
            VideoTagInstanceEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=instance_tag.pk))
        self.assertObjectAbsent(instance_tag)

        self.assertTrue(self.reload(self.video_tag))

    def test_delete_instance_endpoint_delete_orphan_videotag(self):
        """
            Delete last instance of a tag on a video
        """
        self._sign_in(self.user)
        self.api.delete_instance(
            VideoTagInstanceEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk))

        self.assertObjectAbsent(self.video_tag)

"""
    Tests for :mod:`greenday_api.videotag.videotag_api <greenday_api.video.videotag_api>`
"""
# import lib deps
from milkman.dairy import milkman

# import project deps
from greenday_core.api_exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException
)
from greenday_core.models import (
    Project, VideoTagInstance
)
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...videotag.videotag_api import VideoTagAPI
from ...videotag.containers import VideoTagInstanceUpdateEntityContainer


class VideoTagUpdateInstanceTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.update_instance <greenday_api.videotag.videotag_api.VideoTagAPI.update_instance>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagUpdateInstanceTestCase, self).setUp()
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

    def test_update_instance_endpoint_anon(self):
        """
            Update video tag instance - user not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.update_instance,
            VideoTagInstanceUpdateEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk)
        )

    def test_update_instance_endpoint_loggedin_unassigned(self):
        """
            Update video tag instance - user is logged in but not assigned
            to the project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.update_instance,
            VideoTagInstanceUpdateEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk)
        )

    def test_update_instance_endpoint_logged_in_instance_does_not_exist(self):
        """
            Update video tag instance - user is logged in and instance does not
            exist should raise 404
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.update_instance,
            VideoTagInstanceUpdateEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=9999)
        )

    def test_update_instance_endpoint_logged_in_project_does_not_exist(self):
        """
            Update video tag instance - user is logged in and project does not
            exist should raise 404
        """
        self._sign_in(self.user2)
        self.assertRaises(
            NotFoundException,
            self.api.update_instance,
            VideoTagInstanceUpdateEntityContainer.
            combined_message_class(
                project_id=9999,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk)
        )

    def test_update_instance_endpoint_logged_in_video_does_not_exist(self):
        """
            Update video tag instance - user is logged in and video does not
            exist should raise 404
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.update_instance,
            VideoTagInstanceUpdateEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id="9999",
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk)
        )

    def test_update_instance_endpoint_ok(self):
        """
            Update video tag instance - user is logged in and assigned
            to project
        """
        self.assertEqual(1, len(VideoTagInstance.objects.all()))
        self._sign_in(self.user)
        self.api.update_instance(
            VideoTagInstanceUpdateEntityContainer.
            combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                instance_id=self.video_tag_instance.pk,
                start_seconds=4.0,
                end_seconds=9.0))
        self.assertEqual(1, len(VideoTagInstance.objects.all()))
        instance = VideoTagInstance.objects.get(pk=self.video_tag_instance.pk)
        self.assertEqual(4, instance.start_seconds)
        self.assertEqual(9, instance.end_seconds)

    def test_overlap_invalid(self):
        """
            Update video tag instance - another instance of the tag to overlap
            with
        """
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
            self.api.update_instance,
            request
        )

    def test_invalid_start_end(self):
        """
            Update video tag instance - end is before start
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
            self.api.update_instance,
            request
        )

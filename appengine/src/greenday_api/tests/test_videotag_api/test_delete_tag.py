"""
    Tests for :mod:`greenday_api.videotag.videotag_api <greenday_api.video.videotag_api>`
"""
# import lib deps
from milkman.dairy import milkman

# import project deps
from greenday_core.api_exceptions import (
    ForbiddenException, UnauthorizedException, NotFoundException)
from greenday_core.models import (
    Project, VideoTag, VideoTagInstance
)
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...videotag.videotag_api import VideoTagAPI
from ...videotag.containers import VideoTagEntityContainer


# test video tag api
class VideoTagDeleteTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.delete_tag <greenday_api.videotag.videotag_api.VideoTagAPI.delete_tag>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagDeleteTestCase, self).setUp()
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

    def test_delete_tag_endpoint_anon(self):
        """
            Delete video tag - not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.delete_tag,
            VideoTagEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk)
        )

    def test_delete_tag_endpoint_loggedin_unassigned(self):
        """
            Delete video tag - user is logged in but not
            assigned to the project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.delete_tag,
            VideoTagEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk)
        )

    def test_delete_tag_endpoint_logged_in_project_does_not_exist(self):
        """
            Delete video tag - user is logged in and project does not exist
            should raise 404
        """
        self._sign_in(self.user2)
        self.assertRaises(
            NotFoundException,
            self.api.delete_tag,
            VideoTagEntityContainer.combined_message_class(
                project_id=999999,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk)
        )

    def test_delete_tag_endpoint_ok(self):
        """
            Delete video tag
        """
        # user is logged in and assigned to project
        self.assertEqual(1, len(VideoTag.objects.all()))
        self.assertEqual(1, len(VideoTagInstance.objects.all()))
        self._sign_in(self.user)
        self.api.delete_tag(
            VideoTagEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk))
        self.assertEqual(0, len(VideoTag.objects.all()))
        self.assertEqual(0, len(VideoTagInstance.objects.all()))

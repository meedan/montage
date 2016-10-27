"""
    Tests for :mod:`greenday_api.videotag.videotag_api <greenday_api.video.videotag_api>`
"""
# import lib deps
from milkman.dairy import milkman

# import project deps
from greenday_core.api_exceptions import UnauthorizedException
from greenday_core.models import Project
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...videotag.videotag_api import VideoTagAPI
from ...videotag.containers import VideoTagUpdateEntityContainer


class VideoTagPatchTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.patch_tag <greenday_api.videotag.videotag_api.VideoTagAPI.patch_tag>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagPatchTestCase, self).setUp()
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

    def test_patch_tag_endpoint_ok(self):
        """
            Patch video tag
        """
        self._sign_in(self.user)

        initial_name = self.tag.name
        initial_image_url = self.tag.image_url
        response = self.api.patch_tag(
            VideoTagUpdateEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                description='It was grebo'))

        self.tag = self.reload(self.tag)
        self.assertEqual(initial_name, self.tag.name)
        self.assertEqual(initial_image_url, self.tag.image_url)
        self.assertEqual('It was grebo', self.tag.description)
        self.assertEqual(self.video_tag.pk, response.id)

    def test_patch_tag_endpoint_anon(self):
        """
            Patch video tag - user not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.patch_tag,
            VideoTagUpdateEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk)
        )

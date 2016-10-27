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
from ...videotag.containers import VideoTagEntityContainer


class VideoTagGetTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.get_tag <greenday_api.videotag.videotag_api.VideoTagAPI.get_tag>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagGetTestCase, self).setUp()
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

        # another video tag to assert that queries are constrained correctly
        self.create_video_instance_tag(
            project_tag=self.project_tag,
            video=self.create_video(project=self.project))

    def test_get_tag_endpoint_anon(self):
        """
            Get tag - user not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.get_tag,
            VideoTagEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk)
        )

    def test_get_tag_endpoint_loggedin_unassigned(self):
        """
            Get tag - user is logged in but not assigned to the project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.get_tag,
            VideoTagEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk)
        )

    def test_get_tag_endpoint_logged_in_project_does_not_exist(self):
        """
            Get tag - user is logged in and project does not exist should
            raise 404
        """
        self._sign_in(self.user2)
        self.assertRaises(
            NotFoundException,
            self.api.get_tag,
            VideoTagEntityContainer.combined_message_class(
                project_id=999999,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk)
        )

    def test_get_tag_endpoint_ok(self):
        """
            Get tag - user is logged in and assigned to project
        """
        self._sign_in(self.user)
        response = self.api.get_tag(
            VideoTagEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk))

        self.assertEqual(self.video_tag.pk, response.id)
        self.assertEqual(self.project_tag.pk, response.project_tag_id)
        self.assertEqual(self.tag.pk, response.project_tag.global_tag_id)
        self.assertEqual(self.tag.name, response.project_tag.name)
        self.assertEqual(self.tag.description, response.project_tag.description)
        self.assertEqual(self.tag.image_url, response.project_tag.image_url)
        self.assertEqual(self.video.youtube_id, response.youtube_id)
        self.assertEqual(self.project.pk, response.project_tag.project_id)

        self.assertEqual(1, len(response.instances))
        self.assertEqual(self.video_tag_instance.pk, response.instances[0].id)
        self.assertEqual(
            self.video.youtube_id, response.instances[0].youtube_id)
        self.assertEqual(self.project.pk, response.instances[0].project_id)
        self.assertEqual(self.tag.pk, response.instances[0].global_tag_id)
        self.assertEqual(self.video_tag.pk, response.instances[0].video_tag_id)
        self.assertEqual(
            self.project_tag.pk, response.instances[0].project_tag_id)

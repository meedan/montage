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
from ...videotag.containers import VideoEntityContainer


class VideoTagListTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.list_tags <greenday_api.videotag.videotag_api.VideoTagAPI.list_tags>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagListTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)
        self.video = self.create_video(project=self.project)

        self.tag, self.project_tag, self.video_tag, self.video_tag_instance = \
            self.create_video_instance_tag(
                project=self.project,
                video=self.video,
                start_seconds=3,
                end_seconds=5,
                name='A')

        self.tag2, self.project_tag2, self.video_tag2 = \
            self.create_video_tag(
                project=self.project,
                video=self.video,
                name='C')

        self.tag3, self.project_tag3, self.video_tag3 = \
            self.create_video_tag(
                project=self.project,
                video=self.video,
                name='B')

    def test_list_tags_endpoint_anon(self):
        """
            List tags - user not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.list_tags, VideoEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id)
        )

    def test_list_tags_endpoint_loggedin_unassigned(self):
        """
            List tags - user is logged in but not assigned to the project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.list_tags, VideoEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id)
        )

    def test_list_tags_endpoint_logged_in_project_does_not_exist(self):
        """
            List tags - user is logged in and project does not exist should
            raise 404
        """
        self._sign_in(self.user2)
        self.assertRaises(
            NotFoundException,
            self.api.list_tags, VideoEntityContainer.combined_message_class(
                project_id=99999,
                youtube_id=self.video.youtube_id)
        )

    def test_list_tags_endpoint_ok(self):
        """
            List tags
        """
        self._sign_in(self.user)
        with self.assertNumQueries(5):
            response = self.api.list_tags(
                VideoEntityContainer.combined_message_class(
                    project_id=self.project.pk,
                    youtube_id=self.video.youtube_id))

        self.assertEqual(3, len(response.items))

        self.assertEqual(self.video_tag.pk, response.items[0].id)
        self.assertEqual(self.video_tag3.pk, response.items[1].id)
        self.assertEqual(self.video_tag2.pk, response.items[2].id)

        self.assertEqual(self.project_tag.pk, response.items[0].project_tag_id)
        self.assertEqual(self.project_tag3.pk, response.items[1].project_tag_id)
        self.assertEqual(self.project_tag2.pk, response.items[2].project_tag_id)

        self.assertEqual(
            self.tag.pk, response.items[0].project_tag.global_tag_id)
        self.assertEqual(
            self.tag3.pk, response.items[1].project_tag.global_tag_id)
        self.assertEqual(
            self.tag2.pk, response.items[2].project_tag.global_tag_id)

        self.assertEqual(self.video.pk, response.items[0].video_id)
        self.assertEqual(self.video.youtube_id, response.items[0].youtube_id)
        self.assertEqual(
            self.project.pk, response.items[0].project_tag.project_id)

        self.assertEqual(1, len(response.items[0].instances))
        resp_instance = response.items[0].instances[0]
        self.assertEqual(self.video_tag_instance.pk, resp_instance.id)
        self.assertEqual(self.video.pk, resp_instance.video_id)
        self.assertEqual(self.video.youtube_id, resp_instance.youtube_id)
        self.assertEqual(self.project.pk, resp_instance.project_id)
        self.assertEqual(
            self.video_tag_instance.start_seconds, resp_instance.start_seconds)
        self.assertEqual(
            self.video_tag_instance.end_seconds, resp_instance.end_seconds)

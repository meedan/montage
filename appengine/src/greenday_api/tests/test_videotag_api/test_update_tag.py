"""
    Tests for :mod:`greenday_api.videotag.videotag_api <greenday_api.video.videotag_api>`
"""
# import lib deps
from milkman.dairy import milkman

# import project deps
from greenday_core.api_exceptions import (
    ForbiddenException, UnauthorizedException, NotFoundException)
from greenday_core.models import (
    Project, GlobalTag, ProjectTag, VideoTag
)
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...videotag.messages import VideoTagResponseMessage
from ...videotag.videotag_api import VideoTagAPI

from ...videotag.containers import (
    VideoTagUpdateEntityContainer,
)


class VideoTagUpdateTagTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.test_update_tag_endpoint_logged_in_videotag_does_not_exist <greenday_api.videotag.videotag_api.VideoTagAPI.test_update_tag_endpoint_logged_in_videotag_does_not_exist>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagUpdateTagTestCase, self).setUp()
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

    def test_update_tag_endpoint_anon(self):
        """
            Update video tag - user not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.update_tag,
            VideoTagUpdateEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                name='Han Solo & Chewwie',
                description='Han shot first. Where is Chewwies medal?',
                image_url='http://han.shotfirst.com/han_and_chew.jpg')
        )

    def test_update_tag_endpoint_loggedin_unassigned(self):
        """
            Update video tag - user is logged in but not assigned
            to the project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.update_tag,
            VideoTagUpdateEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                name='Han Solo & Chewwie',
                description='Han shot first. Where is Chewwies medal?',
                image_url='http://han.shotfirst.com/han_and_chew.jpg')
        )

    def test_update_tag_endpoint_logged_in_project_does_not_exist(self):
        """
            Update video tag - user is logged in and project does not exist
            should raise 404
        """
        self._sign_in(self.user2)
        self.assertRaises(
            NotFoundException,
            self.api.update_tag,
            VideoTagUpdateEntityContainer.combined_message_class(
                project_id=9999,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                name='Han Solo & Chewwie',
                description='Han shot first. Where is Chewwies medal?',
                image_url='http://han.shotfirst.com/han_and_chew.jpg')
        )

    def test_update_tag_endpoint_logged_in_video_does_not_exist(self):
        """
            Update video tag - user is logged in and video does not exist
            should raise 404
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.update_tag,
            VideoTagUpdateEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id="9999",
                video_tag_id=self.video_tag.pk,
                name='Han Solo & Chewwie',
                description='Han shot first. Where is Chewwies medal?',
                image_url='http://han.shotfirst.com/han_and_chew.jpg')
        )

    def test_update_tag_endpoint_logged_in_videotag_does_not_exist(self):
        """
            Update video tag - user is logged in and video tag does not exist
            should raise 404
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.update_tag,
            VideoTagUpdateEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=9999,
                name='Han Solo & Chewwie',
                description='Han shot first. Where is Chewwies medal?',
                image_url='http://han.shotfirst.com/han_and_chew.jpg')
        )

    def test_update_tag_endpoint_ok(self):
        """
            Update video tag - user is logged in and assigned to
            project
        """
        self.assertEqual(1, len(GlobalTag.objects.all()))
        self.assertEqual(1, len(ProjectTag.objects.all()))
        self.assertEqual(1, len(VideoTag.objects.all()))
        self._sign_in(self.user)

        response = self.api.update_tag(
            VideoTagUpdateEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                video_tag_id=self.video_tag.pk,
                name='Han Solo & Chewwie',
                description='Han shot first. Where is Chewwies medal?',
                image_url='http://han.shotfirst.com/han_and_chew.jpg'))
        self.assertEqual(1, len(GlobalTag.objects.all()))
        self.assertEqual(1, len(ProjectTag.objects.all()))
        self.assertEqual(1, len(VideoTag.objects.all()))
        tag = GlobalTag.objects.get(pk=self.tag.pk)
        project_tag = tag.projecttags.get(project=self.project)
        video_tag = project_tag.videotags.get(video=self.video)
        self.assertEqual('Han Solo & Chewwie', tag.name)
        self.assertEqual(
            'Han shot first. Where is Chewwies medal?', tag.description)
        self.assertEqual(
            'http://han.shotfirst.com/han_and_chew.jpg', tag.image_url)
        self.assertEqual(video_tag.pk, response.id)
        self.assertIsInstance(response, VideoTagResponseMessage)

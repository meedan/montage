"""
    Tests for :mod:`greenday_api.videotag.videotag_api <greenday_api.video.videotag_api>`
"""
# import lib deps
from milkman.dairy import milkman

# import project deps
from greenday_core.api_exceptions import (
    ForbiddenException, NotFoundException, UnauthorizedException)
from greenday_core.models import (
    Project, GlobalTag, ProjectTag, VideoTag
)
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...videotag.messages import VideoTagResponseMessage
from ...videotag.videotag_api import VideoTagAPI
from ...videotag.containers import VideoTagInsertEntityContainer


class VideoTagCreateTestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.videotag.videotag_api.VideoTagAPI.create_tag <greenday_api.videotag.videotag_api.VideoTagAPI.create_tag>`
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagCreateTestCase, self).setUp()
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

    def test_create_tag_endpoint_anon(self):
        """
            Add tag to video - not logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.create_tag,
            VideoTagInsertEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                name='Han Solo',
                description='Han shot first',
                image_url='http://han.shotfirst.com/foo.jpg')
        )

    def test_create_tag_endpoint_loggedin_unassigned(self):
        """ user is logged in but not assigned to the project """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.create_tag,
            VideoTagInsertEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                name='Han Solo',
                description='Han shot first',
                image_url='http://han.shotfirst.com/foo.jpg')
        )

    def test_create_tag_endpoint_logged_in_project_does_not_exist(self):
        """ user is logged in and project does not exist should raise 404 """
        self._sign_in(self.user2)
        self.assertRaises(
            NotFoundException,
            self.api.create_tag,
            VideoTagInsertEntityContainer.combined_message_class(
                project_id=9999,
                youtube_id=self.video.youtube_id,
                name='Han Solo',
                description='Han shot first',
                image_url='http://han.shotfirst.com/foo.jpg')
        )

    def test_create_tag_endpoint_logged_in_video_does_not_exist(self):
        """ user is logged in and project does not exist should raise 404 """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.create_tag,
            VideoTagInsertEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id="9999",
                name='Han Solo',
                description='Han shot first',
                image_url='http://han.shotfirst.com/foo.jpg')
        )

    def test_create_tag_endpoint_ok(self):
        """ user is logged in and assigned to project """
        self._sign_in(self.user)
        response = self.api.create_tag(
            VideoTagInsertEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video.youtube_id,
                name='Han Solo',
                description='Han shot first',
                image_url='http://han.shotfirst.com/foo.jpg'))
        self.assertEqual(2, GlobalTag.objects.count())
        self.assertEqual(2, ProjectTag.objects.count())
        self.assertEqual(2, VideoTag.objects.count())

        videotag = VideoTag.objects.get(
            project_tag__global_tag__name='Han Solo',
            project=self.project,
            video=self.video)
        self.assertEqual(videotag.pk, response.id)
        self.assertEqual(videotag.project_tag_id, response.project_tag_id)
        self.assertEqual(
            videotag.project_tag.global_tag_id,
            response.project_tag.global_tag_id)
        self.assertIsInstance(response, VideoTagResponseMessage)

    def test_create_tag_project_tag_exists(self):
        """
            if a project tag and global tag are passed to the endpoint
            and the relevant records already exist then they are re-used
            and not created
        """
        self._sign_in(self.user)

        # valid request
        response = self.api.create_tag(
            VideoTagInsertEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video_2.youtube_id,
                global_tag_id=self.tag.pk))
        self.assertEqual(1, GlobalTag.objects.count())
        self.assertEqual(1, ProjectTag.objects.count())
        self.assertEqual(2, VideoTag.objects.count())

        videotag = VideoTag.objects.get(
            project_tag__global_tag=self.tag,
            project=self.project,
            video=self.video_2)

        self.assertEqual(videotag.pk, response.id)
        self.assertIsInstance(response, VideoTagResponseMessage)

    def test_create_tag_global_tag_duplicate_name(self):
        """
            If a tag already exists with the given name then we should
            use that.
        """
        tag = milkman.deliver(GlobalTag, name="Bazooka")
        self._sign_in(self.user)

        response = self.api.create_tag(
            VideoTagInsertEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video_2.youtube_id,
                name="  " + tag.name.lower() + "    "))

        self.assertEqual(2, GlobalTag.objects.count())
        self.assertEqual(2, ProjectTag.objects.count())
        self.assertEqual(2, VideoTag.objects.count())

        videotag = VideoTag.objects.get(
            project_tag__global_tag=tag,
            project=self.project,
            video=self.video_2)

        self.assertEqual(videotag.pk, response.id)
        self.assertIsInstance(response, VideoTagResponseMessage)

    def test_create_tag_global_tag_exists(self):
        """
            if a global tag is passed to the endpoint
            and the relevant record already exists then it is re-used
            and not created
        """
        tag = milkman.deliver(GlobalTag)

        self._sign_in(self.user)
        response = self.api.create_tag(
            VideoTagInsertEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video_2.youtube_id,
                global_tag_id=tag.pk))

        videotag = VideoTag.objects.get(
            project_tag__global_tag=tag,
            project=self.project,
            video=self.video_2)

        self.assertEqual(videotag.pk, response.id)
        self.assertEqual(videotag.project_tag_id, response.project_tag_id)
        self.assertEqual(
            videotag.project_tag.global_tag_id,
            response.project_tag.global_tag_id)
        self.assertIsInstance(response, VideoTagResponseMessage)

    def test_create_tag_global_tag_exists_edited(self):
        """
            if a global tag is passed to the endpoint
            and the relevant record already exists then it is re-used
            and not created. If updated description and images
            are provided, they should be ignore. Tag updates should
            be made from the update_tag endpoint and not done here.
            This change makes the endpoint more restful
        """
        tag = milkman.deliver(
            GlobalTag, name='Han Solo', description='Han shot first',
            image_url='http://han.shotfirst.com/foo.jpg')

        self._sign_in(self.user)
        response = self.api.create_tag(
            VideoTagInsertEntityContainer.combined_message_class(
                project_id=self.project.pk,
                youtube_id=self.video_2.youtube_id,
                global_tag_id=tag.pk))
        self.assertEqual(2, GlobalTag.objects.count())
        self.assertEqual(2, ProjectTag.objects.count())
        self.assertEqual(2, VideoTag.objects.count())

        videotag = VideoTag.objects.get(
            project_tag__global_tag=tag,
            project=self.project,
            video=self.video_2)
        self.assertEqual(videotag.pk, response.id)
        self.assertEqual(videotag.project_tag_id, response.project_tag_id)
        self.assertEqual(
            videotag.project_tag.global_tag_id,
            response.project_tag.global_tag_id)

        self.assertEqual('Han shot first', response.project_tag.description)
        self.assertEqual(
            'http://han.shotfirst.com/foo.jpg', response.project_tag.image_url)
        self.assertIsInstance(response, VideoTagResponseMessage)

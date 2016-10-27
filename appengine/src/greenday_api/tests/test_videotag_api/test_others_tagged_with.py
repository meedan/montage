"""
    Tests for :mod:`greenday_api.videotag.videotag_api <greenday_api.video.videotag_api>`
"""
# import lib deps
from milkman.dairy import milkman

# import project deps
from greenday_core.api_exceptions import (
    ForbiddenException, NotFoundException, UnauthorizedException)
from greenday_core.models import (
    Project, Video, GlobalTag, ProjectTag, VideoTag
)

from ..base import ApiTestCase

from ...videotag.videotag_api import VideoTagAPI
from ...videotag.containers import VideoEntityContainer


class OthersTaggedWithTestCase(ApiTestCase):
    """
        Seperate test case for `Others tagged with` functionality.
        Kept Seperate for test data and logical simplicity.
        Slightly complex data setup here and so I cant use the
        ``TestCaseTagHelpers`` with ease.

        Data structure

            Global Tags:
            ------------
                self.tag_1 - self.tag_8

            Project 1:
            ----------
                Project Tags: self.tag_1 - self.tag_4
                Videos:
                    self.video_1
                        Tagged with: self.tag_1 and self.tag_3

            Project 2:
            ----------
                Project Tags: self.tag_5 - self.tag_7
                Videos:
                    self.video_2
                        Tagged with: self.tag_5, self.tag_6 and self.tag_7

            Project 3:
            ----------
                Project Tags: self.tag_8
                Videos:
                    self.video_3
                        Tagged with: self.tag_8
    """
    api_type = VideoTagAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(OthersTaggedWithTestCase, self).setUp()

        # projects
        self.project_1 = milkman.deliver(
            Project, name='Project 1', privacy_project=2)
        self.project_2 = milkman.deliver(
            Project, name='Project 2', privacy_project=2)
        self.project_3 = milkman.deliver(
            Project, name='Project 3 Private Tags',
            privacy_project=1, privacy_tags=1)
        self.project_1.set_owner(self.admin)
        self.project_1.add_assigned(self.user, pending=False)
        self.project_2.set_owner(self.admin)
        self.project_2.add_assigned(self.user2, pending=False)
        self.project_3.set_owner(self.user)

        # videos
        self.video_1 = self.create_video(
            project=self.project_1, name='Foo', youtube_id='rob')
        self.video_2 = self.create_video(
            project=self.project_2,
            name='Foo',
            youtube_video=self.video_1.youtube_video)
        self.video_3 = self.create_video(
            project=self.project_3,
            name='Foo',
            youtube_video=self.video_1.youtube_video)

        # tags
        self.tag_1 = milkman.deliver(
            GlobalTag, name='Han Solo',
            description='Scruffy looking nerf-hurder',
            created_from_project=self.project_1)
        self.tag_2 = milkman.deliver(
            GlobalTag, name='Luke Skywalker',
            description='Used to balls-eye wamp rats',
            created_from_project=self.project_1)
        self.tag_3 = milkman.deliver(
            GlobalTag, name='Chewbacca',
            description='Walking carpet',
            created_from_project=self.project_1)
        self.tag_4 = milkman.deliver(
            GlobalTag, name='Sci-Fi',
            description='Science Fiction Genre',
            created_from_project=self.project_1)
        self.tag_5 = milkman.deliver(
            GlobalTag, name='Egon Spengler',
            description='PHD',
            created_from_project=self.project_2)
        self.tag_6 = milkman.deliver(
            GlobalTag, name='Ray Stantz',
            description='Get her!',
            created_from_project=self.project_2)
        self.tag_7 = milkman.deliver(
            GlobalTag, name='Peter Venkman',
            description='The witty one',
            created_from_project=self.project_2)
        self.tag_8 = milkman.deliver(
            GlobalTag, name='Marty McFly',
            description='Kid from the 80s',
            created_from_project=self.project_3)
        tags = [
            self.tag_1, self.tag_2, self.tag_3, self.tag_4,
            self.tag_5, self.tag_6, self.tag_7, self.tag_8
        ]

        # create project tags
        for index, tag in enumerate(tags):
            setattr(self, 'project_tag_%i' % (index + 1), ProjectTag.add_root(
                global_tag=tag, project=tag.created_from_project))

        # video tags
        self.video_tag_1 = milkman.deliver(
            VideoTag, video=self.video_1, project=self.project_1,
            project_tag=self.project_tag_1)
        self.video_tag_2 = milkman.deliver(
            VideoTag, video=self.video_1, project=self.project_1,
            project_tag=self.project_tag_3)
        self.video_tag_3 = milkman.deliver(
            VideoTag, video=self.video_2, project=self.project_2,
            project_tag=self.project_tag_5)
        self.video_tag_4 = milkman.deliver(
            VideoTag, video=self.video_2, project=self.project_2,
            project_tag=self.project_tag_6)
        self.video_tag_5 = milkman.deliver(
            VideoTag, video=self.video_2, project=self.project_2,
            project_tag=self.project_tag_7)
        self.video_tag_6 = milkman.deliver(
            VideoTag, video=self.video_3, project=self.project_3,
            project_tag=self.project_tag_8)

    def test_list_others_tagged_with_anon(self):
        """
            List others tagged with - user not logged in
        """
        # user must be logged in
        self.assertRaises(
            UnauthorizedException,
            self.api.list_others_tagged_with,
            VideoEntityContainer.combined_message_class(
                project_id=self.project_1.pk,
                youtube_id=self.video_1.youtube_id)
        )

    def test_list_others_tagged_with_loggedin_unassigned(self):
        """
            List others tagged with -
            user is logged in but not assigned to the project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.list_others_tagged_with,
            VideoEntityContainer.combined_message_class(
                project_id=self.project_1.pk,
                youtube_id=self.video_1.youtube_id)
        )

    def test_list_others_tagged_with_endpoint_logged_in_project_does_not_exist(
            self):
        """
            List others tagged with -
            user is logged in and project does not exist should raise 404
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.list_others_tagged_with,
            VideoEntityContainer.combined_message_class(
                project_id=99999,
                youtube_id=self.video_1.youtube_id)
        )

    def test_list_others_tagged_with_endpoint_logged_in_video_does_not_exist(
            self):
        """
            List others tagged with - user is logged in and video does not exist
            should raise 404
        """
        self._sign_in(self.user)
        self.assertRaises(
            NotFoundException,
            self.api.list_others_tagged_with,
            VideoEntityContainer.combined_message_class(
                project_id=self.project_1.pk,
                youtube_id='9999')
        )

    def test_list_others_tagged_with_project_1(self):
        # test with first project
        """
            Endpoint should return un-used tag 2 and 4 from the
            current project and tags 5, 6 and 7 from project_2 since
            the project is public the video youtube_ids match and the tags
            have all been applied to that video. Nothing should be returned
            from project_3 since its marked as private.
        """
        self._sign_in(self.user)
        with self.assertNumQueries(8):
            response = self.api.list_others_tagged_with(
                VideoEntityContainer.combined_message_class(
                    project_id=self.project_1.pk,
                    youtube_id=self.video_1.youtube_id))
        result_ids = [result.id for result in response.items]
        self.assertTrue(self.tag_2.pk in result_ids)
        self.assertTrue(self.tag_4.pk in result_ids)
        self.assertTrue(self.tag_5.pk in result_ids)
        self.assertTrue(self.tag_6.pk in result_ids)
        self.assertTrue(self.tag_7.pk in result_ids)

    def test_list_others_tagged_with_project_2(self):
        # test with second project
        """
            Endpoint should return nothing from the current project as all
            project_2 tags have already been applied. And it should
            return tags 1 and 3 from project_1 since the project is public
            and the video youtube_ids match and the relevant tags have been
            applied to that video. Nothing should be returned
            from project_3 since its marked as private.
        """
        self._sign_in(self.user2)
        with self.assertNumQueries(8):
            response = self.api.list_others_tagged_with(
                VideoEntityContainer.combined_message_class(
                    project_id=self.project_2.pk,
                    youtube_id=self.video_2.youtube_id))
        result_ids = [result.id for result in response.items]
        self.assertTrue(self.tag_1.pk in result_ids)
        self.assertTrue(self.tag_3.pk in result_ids)

    def test_list_others_tagged_with_project_3(self):
        # test with third project
        """
            Endpoint should return nothing from the current project as all
            project_3 tags have already been applied. And it should
            return tags 1 and 3 from project_1 and tags 5, 6 and 7 from
            project_2 since both these projects are public, the video
            youtube_ids match and the relevant tags have been
            applied to those videos.
        """
        self._sign_in(self.user)
        with self.assertNumQueries(8):
            response = self.api.list_others_tagged_with(
                VideoEntityContainer.combined_message_class(
                    project_id=self.project_3.pk,
                    youtube_id=self.video_3.youtube_id))
        result_ids = [result.id for result in response.items]
        self.assertTrue(self.tag_1.pk in result_ids)
        self.assertTrue(self.tag_3.pk in result_ids)
        self.assertTrue(self.tag_5.pk in result_ids)
        self.assertTrue(self.tag_6.pk in result_ids)
        self.assertTrue(self.tag_7.pk in result_ids)

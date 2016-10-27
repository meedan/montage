"""
    Tests for :mod:`greenday_api.onesearch.onesearch_api <greenday_api.onesearch.onesearch_api>`
"""
# import lib deps
import datetime
from milkman.dairy import milkman
from django.utils import timezone

# import project deps
from greenday_core.api_exceptions import (
    UnauthorizedException, NotFoundException)
from greenday_core.models import (
    Project, VideoCollection, UserVideoDetail)
from greenday_core.tests.base import TestCaseTagHelpers

from .base import ApiTestCase
from ..onesearch.onesearch_api import (
    OneSearchAPI,
)
from ..onesearch.containers import (
    OneSearchEntityContainer,
    OneSearchProjectContextEntityContainer,
    OneSearchAdvancedVideoEntityContainer
)


# test onesearch API.
class OneSearchAPITests(ApiTestCase):
    """
        Test case for
        :class:`greenday_api.onesearch.onesearch_api.OneSearchAPI <greenday_api.onesearch.onesearch_api.OneSearchAPI>`
    """
    api_type = OneSearchAPI

    # Test search projects API end point
    def test_search_projects(self):
        """
            Numerous assertions for project searching
        """
        project1 = milkman.deliver(Project, name='Rob Charlwood can code')
        project1.set_owner(self.admin)
        project1.add_assigned(self.user, pending=False)
        project2 = milkman.deliver(Project, name='Can Yilmaz code')
        project2.set_owner(self.admin)
        project2.add_admin(self.user, pending=False)

        project3 = milkman.deliver(
            Project, name='David Neale yilmaz the codebase')
        project3.set_owner(self.user)

        # finally create a project that self.user is not assigned to.
        # this is so we can test that the search only search assigned
        # projects.
        project4 = milkman.deliver(
            Project, name='Someone elses awesome project')
        project4.set_owner(self.admin)

        # unauthenticated users should be booted
        self.assertRaises(
            UnauthorizedException,
            self.api.search_projects,
            OneSearchEntityContainer.combined_message_class(
                q='rob')
        )

        # sign someone in - boom!
        self._sign_in(self.user)

        # empty search terms should be allowed
        response = self.api.search_projects(
            OneSearchEntityContainer.combined_message_class()
        )
        self.assertEqual(3, len(response.items))

        # now lets run some actual tests
        # these are the droids you are looking for...
        response = self.api.search_projects(
            OneSearchEntityContainer.combined_message_class(
                q='rob'))
        self.assertEqual(1, len(response.items))
        self.assertEqual(project1.pk, response.items[0].id)

        response = self.api.search_projects(
            OneSearchEntityContainer.combined_message_class(
                q='can'))
        self.assertEqual(2, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertTrue(project2.pk in result_ids)
        self.assertTrue(project1.pk in result_ids)

        response = self.api.search_projects(
            OneSearchEntityContainer.combined_message_class(
                q='yilmaz'))
        self.assertEqual(2, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertTrue(project2.pk in result_ids)
        self.assertTrue(project3.pk in result_ids)

        response = self.api.search_projects(
            OneSearchEntityContainer.combined_message_class(
                q='code'))
        self.assertEqual(3, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertTrue(project2.pk in result_ids)
        self.assertTrue(project3.pk in result_ids)
        self.assertTrue(project1.pk in result_ids)

        # finally check that we are only searching self.users
        # assigned projects
        response = self.api.search_projects(
            OneSearchEntityContainer.combined_message_class(
                q='someone'))
        self.assertEqual(0, len(response.items))


class OneSearchVideoAPITests(ApiTestCase):
    """
        Test case for
        :func:`greenday_api.onesearch.onesearch_api.OneSearchAPI.search_videos <greenday_api.onesearch.onesearch_api.OneSearchAPI.search_videos>`
    """
    api_type = OneSearchAPI

    def setUp(self):
        """
            Bootstrap videos to search
        """
        super(OneSearchVideoAPITests, self).setUp()

        self.project = milkman.deliver(Project, privacy_project=2)
        self.project.set_owner(self.admin)
        self.project.add_admin(self.user, pending=False)
        self.project_2 = milkman.deliver(Project, privacy_project=2)
        self.project_2.set_owner(self.admin)

        # create some videos for projects.
        self.video_1 = self.create_video(
            project=self.project,
            channel_id=u"UCDASmtEzVZS5PZxjiRjcHKA",
            publish_date=datetime.datetime(2014, 1, 1, tzinfo=timezone.utc),
            name=u"Bazooka")

        self.video_2 = self.create_video(
            channel_id=u"UCmA0uNMDy4wx9NHu1OfBK7R",
            publish_date=datetime.datetime(2014, 2, 1, tzinfo=timezone.utc),
            project=self.project,
            name='Rob Charlwood Video',
            duration=42)

        self.video_3 = self.create_video(
            channel_id=u"UCHX5-wIWTaClDu6uTKXKItg",
            publish_date=datetime.datetime(2014, 3, 1, tzinfo=timezone.utc),
            project=self.project,
            name='Video')

        self.video_4 = self.create_video(
            project=self.project_2,
            channel_id=u"purestawesomeness",
            publish_date=datetime.datetime(2014, 1, 1, tzinfo=timezone.utc),
            name=u"Bazooka 2")

    def test_not_logged_in(self):
        """
            No user logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.search_videos,
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='rob')
        )

    def test_no_search_term(self):
        """
            No search term specified
        """
        self._sign_in(self.user)

        response = self.api.search_videos(
            OneSearchProjectContextEntityContainer.combined_message_class()
        )
        self.assertEqual(4, len(response.items))

    def test_search_response(self):
        """
            Test response message format
        """
        self._sign_in(self.user)
        # search for bazooka as self.user should yield two results
        response = self.api.search_videos(
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='Rob Charlwood Video'))
        self.assertEqual(1, len(response.items))

        item = response.items[0]
        self.assertEqual(self.video_2.pk, item.id)
        self.assertEqual(self.video_2.project_id, item.project_id)
        self.assertEqual(self.video_2.youtube_video.name, item.name)
        self.assertEqual(
            self.video_2.youtube_video.youtube_id, item.youtube_id)
        self.assertEqual(
            self.video_2.youtube_video.channel_id, item.channel_id)
        self.assertEqual(
            self.video_2.youtube_video.channel_name, item.channel_name)
        self.assertEqual(
            self.video_2.youtube_video.publish_date.replace(tzinfo=None),
            item.publish_date)
        self.assertEqual(self.video_2.youtube_video.duration, item.duration)

    def test_search_videos(self):
        """
            Test video searches matching terms
        """
        self._sign_in(self.user)
        # search for bazooka as self.user should yield two results
        response = self.api.search_videos(
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='Bazooka'))
        self.assertEqual(2, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertIn(self.video_1.pk, result_ids)
        self.assertIn(self.video_4.pk, result_ids)

        # search for video should yield 2 results both from the user's
        # assigned project
        response = self.api.search_videos(
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='video'))
        self.assertEqual(2, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertIn(self.video_3.pk, result_ids)
        self.assertIn(self.video_2.pk, result_ids)

    def test_search_videos_with_project_not_assigned(self):
        """
            Searching for videos belonging to a project the
            signed in user is not assigned to
        """
        self._sign_in(self.user)
        # search for bazooka when passing in project_2's pk should
        # not yield any results since self.user is not assigned to
        # project 2
        self.assertRaises(
            NotFoundException,
            self.api.search_videos,
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='Bazooka', project_id=self.project_2.pk)
        )

        # any search when passing in a project pk that does
        # not exist should not yield any results
        self.assertRaises(
            NotFoundException,
            self.api.search_videos,
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='Bazooka', project_id=9999)
        )

    def test_search_videos_with_project(self):
        """
            Searching for videos in a given project
        """
        self._sign_in(self.admin)

        # search for bazooka when passing in project_2's pk should
        # only yield the result for project 2 since we are constraining
        # on project context
        response = self.api.search_videos(
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='Bazooka', project_id=self.project_2.pk))
        self.assertEqual(1, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertIn(self.video_4.pk, result_ids)

        # search for video should yield 2 results both from the user's
        # assigned project (this time as admin)
        response = self.api.search_videos(
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='video'))
        self.assertEqual(2, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertIn(self.video_3.pk, result_ids)
        self.assertIn(self.video_2.pk, result_ids)

    def test_search_videos_no_projects_assigned(self):
        """
            Searching for videos where signed in user is not assigned to
            any projects
        """
        self._sign_in(self.user2)

        # a search for bazooka as user2 should still yield 2 results since
        # both projects are public.
        response = self.api.search_videos(
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='Bazooka'))
        self.assertEqual(2, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertIn(self.video_4.pk, result_ids)
        self.assertIn(self.video_1.pk, result_ids)

        # any search as this user constraining on project should not yield
        # any results since the user is not assigned to either project
        self.assertRaises(
            NotFoundException,
            self.api.search_videos,
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='Bazooka', project_id=self.project.pk)
        )

        self.assertRaises(
            NotFoundException,
            self.api.search_videos,
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='Bazooka', project_id=self.project_2.pk)
        )

    def test_search_videos_negate_video_ids(self):
        """
            Searching for videos specifically excluding some videos
        """
        self._sign_in(self.user)

        response = self.api.search_videos(
            OneSearchProjectContextEntityContainer.combined_message_class(
                q='Bazooka', exclude_ids=str(self.video_4.pk)))
        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_1.pk, response.items[0].id)


class OneSearchAdvancedVideoAPITests(TestCaseTagHelpers, ApiTestCase):
    """
        Test case for
        :func:`greenday_api.onesearch.onesearch_api.OneSearchAPI.advanced_search_videos <greenday_api.onesearch.onesearch_api.OneSearchAPI.advanced_search_videos>`
    """
    api_type = OneSearchAPI

    def setUp(self):
        """
            Bootstrap with videos to search
        """
        super(OneSearchAdvancedVideoAPITests, self).setUp()

        # make both projects public
        self.project = milkman.deliver(Project, privacy_project=2)
        self.project.set_owner(self.admin)
        self.project.add_admin(self.user, pending=False)
        self.private_project = milkman.deliver(Project, privacy_project=1)
        self.private_project.set_owner(self.admin)

        # create some videos for projects.
        self.video_1 = self.create_video(
            project=self.project,
            channel_id=u"UCDASmtEzVZS5PZxjiRjcHKA",
            publish_date=datetime.datetime(2014, 1, 1, tzinfo=timezone.utc),
            name=u"Bazooka",
            youtube_id="yyyzzz123")

        self.video_2 = self.create_video(
            channel_id=u"UCmA0uNMDy4wx9NHu1OfBK7R",
            publish_date=datetime.datetime(2014, 2, 1, tzinfo=timezone.utc),
            project=self.project,
            name='Rob Charlwood Video')

        self.video_3 = self.create_video(
            channel_id=u"UCHX5-wIWTaClDu6uTKXKItg",
            publish_date=datetime.datetime(2014, 3, 1, tzinfo=timezone.utc),
            project=self.project,
            name='Video')

        self.video_4 = self.create_video(
            project=self.private_project,
            youtube_video=self.video_1.youtube_video)

    def test_unauthenticated(self):
        """
            No user logged in
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.advanced_search_videos,
            OneSearchAdvancedVideoEntityContainer.combined_message_class()
        )

    def test_response_data(self):
        """
            Test returned data
        """
        # add some extra meta around video_2
        UserVideoDetail.objects.create(
            user=self.user, video=self.video_2, watched=True)
        UserVideoDetail.objects.create(
            user=self.admin, video=self.video_2, watched=False)

        self.create_video_instance_tag(
            project=self.project, video=self.video_2)

        collection = milkman.deliver(
            VideoCollection, project=self.project)
        collection.add_video(self.video_2)

        self._sign_in(self.admin)

        response = self.api.advanced_search_videos(
            OneSearchAdvancedVideoEntityContainer.combined_message_class(
                q=self.video_2.youtube_video.name)
        )

        self.assertEqual(1, len(response.items))

        self.assertEqual(self.video_2.pk, response.items[0].id)
        self.assertEqual(
            self.video_2.videotags.count(), response.items[0].tag_count)
        self.assertEqual(
            self.video_2.related_users.filter(watched=True).count(),
            response.items[0].watch_count)
        self.assertEqual(
            [collection.pk],
            response.items[0].in_collections)

    def test_empty_search(self):
        """
            No search term specified
        """
        self._sign_in(self.user)

        response = self.api.advanced_search_videos(
            OneSearchAdvancedVideoEntityContainer.combined_message_class()
        )

        self.assertEqual(3, len(response.items))

    def test_search_with_project(self):
        """
            Search videos within a specific project
        """
        self._sign_in(self.user)

        response = self.api.advanced_search_videos(
            OneSearchAdvancedVideoEntityContainer.combined_message_class(
                q='Bazooka', project_id=self.project.pk))
        self.assertEqual(1, len(response.items))

    def test_search_project_doesnt_exist(self):
        """
            Search videos within a project ID that doesn't exist
        """
        self._sign_in(self.user)

        self.assertRaises(
            NotFoundException,
            self.api.advanced_search_videos,
            OneSearchAdvancedVideoEntityContainer.combined_message_class(
                q='a', project_id=9999)
        )

    def test_search_private(self):
        """
            Search videos which are private to a project
        """
        self._sign_in(self.admin)

        response = self.api.advanced_search_videos(
            OneSearchAdvancedVideoEntityContainer.combined_message_class(
                q='Bazooka'))
        self.assertEqual(2, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertIn(self.video_1.pk, result_ids)
        self.assertIn(self.video_4.pk, result_ids)

        # search for video should yield 2 results both from the user's
        # assigned project
        response = self.api.advanced_search_videos(
            OneSearchAdvancedVideoEntityContainer.combined_message_class(
                q='video'))
        self.assertEqual(2, len(response.items))
        result_ids = [result.id for result in response.items]
        self.assertIn(self.video_3.pk, result_ids)
        self.assertIn(self.video_2.pk, result_ids)

    def test_search_with_project_unassigned(self):
        """
            Search videos within a project that the signed in user is
            not assigned to
        """
        self._sign_in(self.user2)

        self.assertRaises(
            NotFoundException,
            self.api.advanced_search_videos,
            OneSearchAdvancedVideoEntityContainer.combined_message_class(
                q='a', project_id=self.project.pk)
        )

    def test_search_public(self):
        """
            Search videos belonging to public project
        """
        self._sign_in(self.user2)

        # a search for bazooka as user2 should yield 2 results since
        # both projects are public.
        response = self.api.advanced_search_videos(
            OneSearchAdvancedVideoEntityContainer.combined_message_class(
                q='Bazooka'))
        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_1.pk, response.items[0].id)

    def test_filter_youtube_id(self):
        """
            Search videos by YouTube ID
        """
        self._sign_in(self.admin)

        response = self.api.advanced_search_videos(
            OneSearchAdvancedVideoEntityContainer.combined_message_class(
                youtube_id='yyyzzz123'))
        self.assertEqual(2, len(response.items))
        result_ids = [v.id for v in response.items]
        self.assertIn(self.video_1.pk, result_ids)
        self.assertIn(self.video_4.pk, result_ids)

    def test_search_videos_negate_video_ids(self):
        """
            Search videos and exclude videos with a given video ID
        """
        self._sign_in(self.user)

        response = self.api.advanced_search_videos(
            OneSearchAdvancedVideoEntityContainer.combined_message_class(
                q='Bazooka', exclude_ids=str(self.video_4.pk)))
        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_1.pk, response.items[0].id)

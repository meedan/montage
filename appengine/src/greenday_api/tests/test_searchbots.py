"""
    Tests for :mod:`greenday_api.searchbot <greenday_api.searchbot>`
"""
# import pyton deps
import datetime
import mock

# import lib deps
from milkman.dairy import milkman
from django.utils import timezone
from google.appengine.api.search import Index

# import project deps
from greenday_core.tests.base import AppengineTestBed
from greenday_core.models import (
    Project,
    ProjectTag,
    VideoTag,
    VideoTagInstance,
    GlobalTag,
    VideoCollection,
    TimedVideoComment
)
from greenday_core.documents.video import VideoDocument
from ..searchbot import VideoSearch


# test searchbots
class SearchVideoTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_api.searchbot.VideoSearch <greenday_api.searchbot.VideoSearch>`
    """
    def setUp(self):
        """
            Bootstrap test data

            Video 1: Millennium Falcon
            Video 2: Millennium Falcon, Death Star
            Video 3: X-Wing, Death Star
        """
        super(SearchVideoTestCase, self).setUp()
        self.video_search = VideoSearch.create(
            'videos', VideoDocument, ids_only=False)

        self.project = milkman.deliver(Project, name='Project')
        self.project_2 = milkman.deliver(Project, name='Project 2')
        self.video_1 = self.create_video(
            project=self.project,
            channel_id=u"UCDASmtEzVZS5PZxjiRjcHKA",
            publish_date=datetime.datetime(2014, 1, 1, tzinfo=timezone.utc),
            latitude=3.14,
            longitude=4.5,
            name=u"Bazooka",
            youtube_id="yyyzzz123")

        self.video_2 = self.create_video(
            channel_id=u"UCmA0uNMDy4wx9NHu1OfAw9g",
            publish_date=datetime.datetime(2014, 2, 1, tzinfo=timezone.utc),
            recorded_date=datetime.datetime(2014, 1, 15, tzinfo=timezone.utc),
            project=self.project_2,
            name='Bazooka 2',
            youtube_id="ttthhh333")

        self.video_3 = self.create_video(
            channel_id=u"UCHX5-wIWTaClDu6uTKXKItg",
            publish_date=datetime.datetime(2014, 3, 1, tzinfo=timezone.utc),
            project=self.project,
            name='Video',
            youtube_id="321bbbaaa")

        self.video_4 = self.create_video(
            youtube_video=self.video_1.youtube_video,
            publish_date=datetime.datetime(2000, 1, 1, tzinfo=timezone.utc),
            recorded_date_overridden=True,
            recorded_date=datetime.datetime(2000, 1, 1, tzinfo=timezone.utc),
        )

        # setup some collection
        self.collection_1 = milkman.deliver(
            VideoCollection, project=self.project, name='Collection 1')
        self.collection_2 = milkman.deliver(
            VideoCollection, project=self.project, name='Collection 2')
        self.collection_1.add_video(self.video_3)
        self.collection_2.add_video(self.video_1)
        self.collection_2.add_video(self.video_3)

        # setup some tags and stuff.
        self.tag_1 = milkman.deliver(
            GlobalTag, name='Millennium Falcon',
            description='Fastest hunka junk in the galaxy')
        self.tag_2 = milkman.deliver(
            GlobalTag, name='X-Wing',
            description='Red Leader, Red 1, Red 2, Red 3, Red 4 and Red 5')
        self.tag_3 = milkman.deliver(
            GlobalTag, name='Death Star',
            description='The ultimate power in the galaxy')
        self.project_tag_1 = milkman.deliver(
            ProjectTag, project=self.project, global_tag=self.tag_1)
        self.project_tag_2 = milkman.deliver(
            ProjectTag, project=self.project, global_tag=self.tag_2)
        self.project_tag_3 = milkman.deliver(
            ProjectTag, project=self.project, global_tag=self.tag_3)

        self.video_tag_1 = milkman.deliver(
            VideoTag, project=self.project, project_tag=self.project_tag_1,
            video=self.video_1)
        self.video_tag_2 = milkman.deliver(
            VideoTag, project=self.project, project_tag=self.project_tag_1,
            video=self.video_2)
        self.video_tag_3 = milkman.deliver(
            VideoTag, project=self.project, project_tag=self.project_tag_2,
            video=self.video_3)
        self.video_tag_4 = milkman.deliver(
            VideoTag, project=self.project, project_tag=self.project_tag_3,
            video=self.video_2)
        self.video_tag_5 = milkman.deliver(
            VideoTag, project=self.project, project_tag=self.project_tag_3,
            video=self.video_3)
        self.video_tag_instance_1 = VideoTagInstance.objects.create(
            video_tag=self.video_tag_1)
        self.video_tag_instance_2 = VideoTagInstance.objects.create(
            video_tag=self.video_tag_2)
        self.video_tag_instance_3 = VideoTagInstance.objects.create(
            video_tag=self.video_tag_3)
        self.video_tag_instance_4 = VideoTagInstance.objects.create(
            video_tag=self.video_tag_4)
        self.video_tag_instance_5 = VideoTagInstance.objects.create(
            video_tag=self.video_tag_5)

        self.root_comment = TimedVideoComment.add_root(
            video=self.video_1,
            text='foo',
            start_seconds=0
        )

    def test_keyword_search(self):
        """
            Search by keyword
        """
        self.video_search = self.video_search.keywords('bazooka')
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(3, len(results))
        self.assertIn(str(self.video_2.pk), result_ids)
        self.assertIn(str(self.video_1.pk), result_ids)
        self.assertIn(str(self.video_4.pk), result_ids)

    def test_keyword_search_comment(self):
        """
            Search by keyword contained in comments
        """
        self.video_search = self.video_search.keywords(self.root_comment.text)
        results = self.video_search
        self.assertEqual(1, len(results))
        self.assertEqual(str(self.video_1.pk), results[0].id)

    def test_filter_projects(self):
        """
            Filter videos by project
        """
        self.video_search = self.video_search.filter_projects(
            self.project_2.pk)
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(1, len(results))
        self.assertIn(str(self.video_2.pk), result_ids)

    def test_filter_projects_list(self):
        """
            Filter videos by numerous projects
        """
        self.video_search = self.video_search.filter_projects(
            [self.project.pk, self.project_2.pk])
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(3, len(results))
        self.assertIn(str(self.video_3.pk), result_ids)
        self.assertIn(str(self.video_2.pk), result_ids)
        self.assertIn(str(self.video_1.pk), result_ids)

    def test_filter_collections(self):
        """
            Filter videos by collection
        """
        self.video_search = self.video_search.filter_collections(self.collection_1.pk)
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(1, len(results))
        self.assertIn(str(self.video_3.pk), result_ids)

    def test_filter_collections_list(self):
        """
            Filter videos by numerous collections
        """
        self.video_search = self.video_search.filter_collections(
            [self.collection_1.pk, self.collection_2.pk])
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(2, len(results))
        self.assertIn(str(self.video_3.pk), result_ids)
        self.assertIn(str(self.video_1.pk), result_ids)

    def test_filter_projects_csv_string(self):
        """
            Filter videos by a CSV string of project IDs
        """
        self.video_search = self.video_search.filter_projects('%s,%s' % (
            self.project.pk, self.project_2.pk))
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(3, len(results))
        self.assertIn(str(self.video_3.pk), result_ids)
        self.assertIn(str(self.video_2.pk), result_ids)
        self.assertIn(str(self.video_1.pk), result_ids)

    def test_keyword_search_chained_with_project_filter(self):
        """
            Search by keyword and project ID
        """
        self.video_search = self.video_search.keywords('bazooka')
        self.video_search = self.video_search.filter_projects(self.project_2.pk)
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(1, len(results))
        self.assertIn(str(self.video_2.pk), result_ids)

    def test_filter_tags_single(self):
        """
            Filter by a single tag
        """
        self.video_search = self.video_search.filter_tags('%s' % self.project_tag_2.pk)
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(1, len(results))
        self.assertIn(str(self.video_3.pk), result_ids)

    def test_filter_tags_single_negation(self):
        """
            Filter by a single negated tag
        """
        self.video_search = self.video_search.filter_tags('-%s' % self.project_tag_2.pk)
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(3, len(results))
        self.assertIn(str(self.video_1.pk), result_ids)
        self.assertIn(str(self.video_2.pk), result_ids)
        self.assertIn(str(self.video_4.pk), result_ids)

    def test_filter_tags_two(self):
        """
            Filter by two tags
        """
        self.video_search = self.video_search.filter_tags(
            '%s,%s' % (self.project_tag_2.pk, self.project_tag_3.pk))
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(2, len(results))
        self.assertIn(str(self.video_3.pk), result_ids)
        self.assertIn(str(self.video_2.pk), result_ids)

    def test_filter_tags_two_negation(self):
        """
            Filter by one negated tag and one non-negated tag
        """
        self.video_search = self.video_search.filter_tags('-%s,%s' % (
            self.project_tag_2.pk, self.project_tag_3.pk))
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(1, len(results))
        self.assertIn(str(self.video_2.pk), result_ids)

    def test_filter_tags_multiple(self):
        """
            Filter by multiple tags
        """
        self.video_search = self.video_search.filter_tags('%s,%s,%s' % (
            self.project_tag_1.pk, self.project_tag_2.pk, self.project_tag_3.pk))
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(3, len(results))
        self.assertIn(str(self.video_3.pk), result_ids)
        self.assertIn(str(self.video_2.pk), result_ids)
        self.assertIn(str(self.video_1.pk), result_ids)

    def test_filter_tags_multiple_negation(self):
        """
            Filter by a combination of negated and non-negated tags
        """
        self.video_search = self.video_search.filter_tags('%s,-%s,%s' % (
            self.project_tag_1.pk, self.project_tag_2.pk, self.project_tag_3.pk))
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(2, len(results))
        self.assertIn(str(self.video_2.pk), result_ids)
        self.assertIn(str(self.video_1.pk), result_ids)

    def test_filter_date_between(self):
        """
            Filter by published date between two dates
        """
        self.video_search = self.video_search.filter_date(
            "publish_date__between__2014-1-20__2014-2-20")
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(1, len(results))
        self.assertIn(str(self.video_2.pk), result_ids)

    def test_filter_date_not_between(self):
        """
            Filter by published date not between two dates
        """
        self.video_search = self.video_search.filter_date(
            "publish_date__notbetween__2014-1-20__2014-2-20")
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(3, len(results))
        self.assertIn(str(self.video_3.pk), result_ids)
        self.assertIn(str(self.video_1.pk), result_ids)

    def test_filter_date_after(self):
        """
            Filter by published date after a date
        """
        self.video_search = self.video_search.filter_date("publish_date__after__2014-1-2")
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(2, len(results))
        self.assertIn(str(self.video_3.pk), result_ids)
        self.assertIn(str(self.video_2.pk), result_ids)

    def test_filter_date_before(self):
        """
            Filter by published date before a date
        """
        self.video_search = self.video_search.filter_date("publish_date__before__2014-2-2")
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(3, len(results))
        self.assertIn(str(self.video_1.pk), result_ids)
        self.assertIn(str(self.video_2.pk), result_ids)

    def test_filter_date_exact(self):
        """
            Filter by an exact published date
        """
        self.video_search = self.video_search.filter_date("publish_date__exact__2014-1-1")
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(2, len(results))
        self.assertIn(str(self.video_1.pk), result_ids)
        self.assertIn(str(self.video_4.pk), result_ids)

    def test_filter_recorded_date_exact(self):
        """
            Filter by an exact recorded date
        """
        self.video_search = self.video_search.filter_date("recorded_date__exact__2014-1-15")
        results = self.video_search
        self.assertEqual(str(self.video_2.pk), results[0].doc_id)

    def test_filter_has_no_recorded_date(self):
        """
            Filter videos with no recorded date
        """
        self.video_search = self.video_search.filter_date("recorded_date__false")
        results = self.video_search
        self.assertEqual(2, len(results))
        self.assertNotIn(str(self.video_2.pk), [doc.id for doc in results])

    def test_filter_has_recorded_date(self):
        """
            Filter videos with any recorded date
        """
        self.video_search = self.video_search.filter_date("recorded_date__true")
        results = self.video_search[:1000]
        self.assertEqual(2, len(results))
        result_ids = [doc.id for doc in results]
        self.assertIn(str(self.video_2.pk), result_ids)
        self.assertIn(str(self.video_4.pk), result_ids)

    def test_filter_channels(self):
        """
            Filter videos by channel
        """
        self.video_search = self.video_search.filter_channels(self.video_1.youtube_video.channel_id)
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(2, len(results))
        self.assertIn(str(self.video_1.pk), result_ids)

    def test_filter_channels_list(self):
        """
            Filter videos by list of channels
        """
        self.video_search = self.video_search.filter_channels(
            [self.video_1.youtube_video.channel_id,
            self.video_2.youtube_video.channel_id])
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(3, len(results))
        self.assertIn(str(self.video_2.pk), result_ids)
        self.assertIn(str(self.video_1.pk), result_ids)

    def test_filter_channels_csv_string(self):
        """
            Filter videos by CSV string of channel IDs
        """
        self.video_search = self.video_search.filter_channels('%s,%s' % (
            self.video_1.youtube_video.channel_id,
            self.video_2.youtube_video.channel_id))
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(3, len(results))
        self.assertIn(str(self.video_2.pk), result_ids)
        self.assertIn(str(self.video_1.pk), result_ids)

    def test_filter_has_location(self):
        """
            Filter videos that have a location
        """
        self.video_search = self.video_search.geo_search('true')

        result_ids = [doc.id for doc in self.video_search]
        self.assertEqual(2, len(result_ids))
        self.assertIn(str(self.video_1.pk), result_ids)
        self.assertIn(str(self.video_4.pk), result_ids)

    def test_filter_has_no_location(self):
        """
            Filter videos that do not have a location
        """
        self.video_search = self.video_search.geo_search('false')
        results = self.video_search
        result_ids = [int(doc.id) for doc in results]
        self.assertEqual(2, len(results))
        self.assertNotIn(self.video_1.pk, result_ids)

    @mock.patch.object(Index, "search")
    def test_filter_location(self, mock_search):
        """
            Filter videos by location
        """
        self.video_search = self.video_search.geo_search("3.14__4.28__5__some-location-name")

        results = [r.id for r in self.video_search[:1000]]
        self.assertEqual(0, len(results))

        # We cant retrieve results here as the search stub
        # in the SDK does not support geo-filtering locally.
        # However, we can check that the correct query is run
        # by checking the mocked search
        self.assertEqual(
            '(distance(location, '
            'geopoint(3.140000, 4.280000)) < 8046 AND '
            'has_location:"1")',
            mock_search.mock_calls[0][1][0].query_string)

    def test_youtube_id(self):
        """
            Filter videos by YouTube ID
        """
        self.video_search = self.video_search.filter_youtube_id("yyyzzz123")
        results = self.video_search
        result_ids = [doc.id for doc in results]
        self.assertEqual(2, len(results))
        self.assertIn(str(self.video_1.pk), result_ids)
        self.assertIn(str(self.video_4.pk), result_ids)

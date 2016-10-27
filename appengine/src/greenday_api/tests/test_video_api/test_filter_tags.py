"""
    Video tag filter tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
# LIBRARIES
import datetime
from milkman.dairy import milkman
import mock
from google.appengine.api.search import Index

# FRAMEWORK
from django.utils import timezone

# GREENDAY
from greenday_core.models import (
    Project,
    VideoCollection,
)
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...video.video_api import VideoAPI
from ...video.containers import VideoFilterContainer


# pylint: disable=R0902
class VideoTagFilterAPITests(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_tag_filter <greenday_api.video.video_api.VideoAPI.video_tag_filter>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoTagFilterAPITests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

        self.video_1 = self.create_video(
            project=self.project,
            channel_id=u"UCDASmtEzVZS5PZxjiRjcHKA",
            publish_date=datetime.datetime(2014, 1, 1, tzinfo=timezone.utc),
            name=u"Bazooka")

        self.video_2 = self.create_video(
            channel_id=u"UCmA0uNMDy4wx9NHu1OfAw9g",
            publish_date=datetime.datetime(2014, 2, 1, tzinfo=timezone.utc),
            recorded_date=datetime.datetime(2014, 1, 15, tzinfo=timezone.utc),
            project=self.project)

        self.video_3 = self.create_video(
            channel_id=u"UCHX5-wIWTaClDu6uTKXKItg",
            publish_date=datetime.datetime(2014, 3, 1, tzinfo=timezone.utc),
            project=self.project)

        # Video 1: Alpha
        self.tag_1, self.project_tag_1, _, self.video_1_tag_instance = \
            self.create_video_instance_tag(
                name='Alpha',
                project=self.project,
                video=self.video_1,
                user=self.admin,
                start_seconds=5,
                end_seconds=42)

        # Video 2: Alpha
        self.create_video_instance_tag(
            video=self.video_2,
            user=self.admin,
            project_tag=self.project_tag_1)

        # Video 3: Bravo
        self.tag_2, self.project_tag_2, _, _ = self.create_video_instance_tag(
            name='Bravo',
            project=self.project,
            video=self.video_3,
            user=self.admin)

        # Video 2: Charlie
        self.tag_3, self.project_tag_3, _, _ = self.create_video_instance_tag(
            name='Charlie',
            project=self.project,
            video=self.video_2,
            user=self.admin)

        # Video 3: Charlie
        _, _, _, _ = self.create_video_instance_tag(
            project=self.project,
            project_tag=self.project_tag_3,
            video=self.video_3,
            user=self.admin)

        # create some collections
        self.collection_1 = milkman.deliver(
            VideoCollection, project=self.project, name='Collection 1')
        self.collection_2 = milkman.deliver(
            VideoCollection, project=self.project, name='Collection 2')
        self.collection_1.add_video(self.video_2)
        self.collection_2.add_video(self.video_1)

        # add a video outside of this project to make sure we filter on project
        self.other_project = milkman.deliver(Project)
        self.other_project.set_owner(self.admin)

        self.other_video = self.create_video(youtube_video=self.video_1.youtube_video)

    def test_filter_response_data(self):
        """
            Check API response data
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(3, len(response.items))

        first_item = response.items[0]
        self.assertEqual(self.tag_1.pk, first_item.global_tag_id)
        self.assertEqual(self.tag_1.name, first_item.name)
        self.assertEqual(self.tag_1.description, first_item.description)
        self.assertEqual(self.tag_1.image_url, first_item.image_url)
        self.assertEqual(2, len(first_item.instances))

        first_instance = first_item.instances[0]
        self.assertEqual(
            self.video_1_tag_instance.start_seconds,
            first_instance.start_seconds)
        self.assertEqual(
            self.video_1_tag_instance.end_seconds,
            first_instance.end_seconds)
        self.assertEqual(
            self.video_1.pk,
            first_instance.video_id)
        self.assertEqual(
            self.video_1.youtube_video.name,
            first_instance.video_name)
        self.assertEqual(
            self.video_1.youtube_video.youtube_id,
            first_instance.youtube_id)
        self.assertEqual(
            self.video_1_tag_instance.user_id,
            first_instance.user_id)

    def test_filter_keyword(self):
        """
            Filter by keyword
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id, q=u"Bazooka")

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(1, len(response.items))
        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(
            self.video_1.pk, response.items[0].instances[0].video_id)
        self.assertEqual(
            self.video_1_tag_instance.start_seconds,
            response.items[0].instances[0].start_seconds)

    def test_filter_tags_single(self):
        """
            Filter by tag
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids="%s" % self.project_tag_2.pk
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(2, len(response.items))

        global_tag_ids = [t.global_tag_id for t in response.items]
        self.assertIn(self.tag_2.pk, global_tag_ids)
        self.assertIn(self.tag_3.pk, global_tag_ids)

        self.assertEqual(
            self.video_3.pk, response.items[0].instances[0].video_id)
        self.assertEqual(1, len(response.items[0].instances))

    def test_filter_tags_single_negation(self):
        """
            Filter by negated tag
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids="-%s" % self.project_tag_2.pk
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(2, len(response.items))

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(2, len(response.items[0].instances))
        self.assertEqual(
            self.video_1.pk, response.items[0].instances[0].video_id)
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[1].video_id)

        self.assertEqual(self.tag_3.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_2.pk, response.items[1].instances[0].video_id)

    def test_filter_tags_two(self):
        """
            Filter by two tags
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids=",".join(
                map(str, (self.project_tag_2.pk, self.project_tag_3.pk))
            )
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        global_tag_ids = [t.global_tag_id for t in response.items]
        self.assertIn(self.tag_3.pk, global_tag_ids)
        self.assertIn(self.tag_2.pk, global_tag_ids)

        tag_2_item = next(
            t for t in response.items if t.global_tag_id == self.tag_2.pk)

        self.assertEqual(self.tag_2.pk, tag_2_item.global_tag_id)
        self.assertEqual(1, len(tag_2_item.instances))
        self.assertEqual(
            self.video_3.pk, tag_2_item.instances[0].video_id)

        tag_3_item = next(
            t for t in response.items if t.global_tag_id == self.tag_3.pk)

        self.assertEqual(self.tag_3.pk, tag_3_item.global_tag_id)
        self.assertEqual(2, len(tag_3_item.instances))
        self.assertEqual(
            self.video_2.pk, tag_3_item.instances[0].video_id)
        self.assertEqual(
            self.video_3.pk, tag_3_item.instances[1].video_id)

    def test_filter_tags_two_negation(self):
        """
            Filter by negated and non-negated tag
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids=",".join(
                (str(self.project_tag_3.pk), '-%s' % self.project_tag_2.pk)
            )
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        global_tag_ids = [t.global_tag_id for t in response.items]
        self.assertIn(self.tag_3.pk, global_tag_ids)
        self.assertIn(self.tag_1.pk, global_tag_ids)

        self.assertEqual(1, len(response.items[0].instances))
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[0].video_id)

    def test_filter_tags_multiple(self):
        """
            Filter by list of tags
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids=",".join(
                map(str, (
                    self.project_tag_1.pk,
                    self.project_tag_2.pk,
                    self.project_tag_3.pk))
            )
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(2, len(response.items[0].instances))
        self.assertEqual(
            self.video_1.pk, response.items[0].instances[0].video_id)
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[1].video_id)

        self.assertEqual(self.tag_2.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_3.pk, response.items[1].instances[0].video_id)

        self.assertEqual(self.tag_3.pk, response.items[2].global_tag_id)
        self.assertEqual(2, len(response.items[2].instances))
        self.assertEqual(
            self.video_2.pk, response.items[2].instances[0].video_id)
        self.assertEqual(
            self.video_3.pk, response.items[2].instances[1].video_id)

    def test_filter_tags_multiple_with_negation(self):
        """
            Filter by combination of negated and non-negated tags
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids=",".join(
                (
                    str(self.project_tag_1.pk),
                    str(self.project_tag_3.pk),
                    '-%s' % self.project_tag_2.pk
                )
            )
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(2, len(response.items[0].instances))
        self.assertEqual(
            self.video_1.pk, response.items[0].instances[0].video_id)
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[1].video_id)

        self.assertEqual(self.tag_3.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_2.pk, response.items[1].instances[0].video_id)

    def test_filter_date_between(self):
        """
            Filter published date between two dates
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__between__2014-1-20__2014-2-20"
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(1, len(response.items[0].instances))
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[0].video_id)

        self.assertEqual(self.tag_3.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_2.pk, response.items[1].instances[0].video_id)

    def test_filter_date_notbetween(self):
        """
            Filter published date not between two dates
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__notbetween__2014-1-20__2014-2-20"
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(1, len(response.items[0].instances))
        self.assertEqual(
            self.video_1.pk, response.items[0].instances[0].video_id)

        self.assertEqual(self.tag_2.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_3.pk, response.items[1].instances[0].video_id)

    def test_filter_date_after(self):
        """
            Filter published date after a date
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__after__2014-1-2"
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(1, len(response.items[0].instances))
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[0].video_id)

        self.assertEqual(self.tag_2.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_3.pk, response.items[1].instances[0].video_id)

        self.assertEqual(self.tag_3.pk, response.items[2].global_tag_id)
        self.assertEqual(2, len(response.items[2].instances))
        self.assertEqual(
            self.video_2.pk, response.items[2].instances[0].video_id)
        self.assertEqual(
            self.video_3.pk, response.items[2].instances[1].video_id)

    def test_filter_date_before(self):
        """
            Filter published date before a date
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__before__2014-2-2"
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(2, len(response.items[0].instances))
        self.assertEqual(
            self.video_1.pk, response.items[0].instances[0].video_id)
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[1].video_id)

        self.assertEqual(self.tag_3.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_2.pk, response.items[1].instances[0].video_id)

    def test_filter_date_exact(self):
        """
            Filter published date exactly matches a date
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__exact__2014-1-1"
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(1, len(response.items[0].instances))
        self.assertEqual(
            self.video_1.pk, response.items[0].instances[0].video_id)

    def test_filter_recorded_date_exact(self):
        """
            Filter recorded date after a date
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="recorded_date__exact__2014-1-15"
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(1, len(response.items[0].instances))
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[0].video_id)

        self.assertEqual(self.tag_3.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_2.pk, response.items[1].instances[0].video_id)

    def test_filter_channel_id(self):
        """
            Filter by channel ID
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            channel_ids=",".join(
                (self.video_1.youtube_video.channel_id, self.video_2.youtube_video.channel_id,)
            )
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(2, len(response.items[0].instances))
        self.assertEqual(
            self.video_1.pk, response.items[0].instances[0].video_id)
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[1].video_id)
        self.assertEqual(2, len(response.items[0].instances))

        self.assertEqual(self.tag_3.pk, response.items[1].global_tag_id)
        self.assertEqual(
            self.video_2.pk, response.items[1].instances[0].video_id)
        self.assertEqual(1, len(response.items[1].instances))

    def test_filter_collection_id(self):
        """
            Filter by collection ID
        """
        self._sign_in(self.admin)

        # single collection id
        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            collection_id="%s" % self.collection_1.pk
        )

        with self.assertNumQueries(7):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(1, len(response.items[0].instances))

        self.assertEqual(
            self.video_2.pk, response.items[0].instances[0].video_id)

        self.assertEqual(self.tag_3.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_2.pk, response.items[1].instances[0].video_id)

        # multiple collection id
        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            collection_id=",".join(
                (str(self.collection_1.pk), str(self.collection_2.pk))
            )
        )

        with self.assertNumQueries(6):
            response = self.api.video_tag_filter(request)

        self.assertEqual(self.tag_1.pk, response.items[0].global_tag_id)
        self.assertEqual(2, len(response.items[0].instances))
        self.assertEqual(
            self.video_1.pk, response.items[0].instances[0].video_id)
        self.assertEqual(
            self.video_2.pk, response.items[0].instances[1].video_id)

        self.assertEqual(self.tag_3.pk, response.items[1].global_tag_id)
        self.assertEqual(1, len(response.items[1].instances))
        self.assertEqual(
            self.video_2.pk, response.items[1].instances[0].video_id)

    @mock.patch.object(Index, "search")
    def test_filter_location(self, mock_search):
        """
            Filter by location
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            location="3.14__4.28__5"
        )

        response = self.api.video_tag_filter(request)

        # not expecting results because the local search stub in the SDK
        # does not support geo-filtering
        self.assertEqual(0, len(response.items))
        self.assertEqual(
            '((project_id:"{project_id}") AND '
            '(distance(location, geopoint(3.140000, 4.280000)) < 8046 AND '
            'has_location:"1"))'.format(
                project_id=self.project.pk),
            mock_search.mock_calls[0][1][0].query_string
        )

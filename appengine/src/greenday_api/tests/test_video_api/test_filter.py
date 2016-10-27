# coding: utf-8
"""
    Filtering video tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
# LIBRARIES
import datetime
from milkman.dairy import milkman
import mock
import unittest
from google.appengine.api.search import Index

# FRAMEWORK
from django.utils import timezone

# GREENDAY
from greenday_core.api_exceptions import ForbiddenException
from greenday_core.models import (
    Project,
    VideoCollection,
    UserVideoDetail
)
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase

from ...video.video_api import VideoAPI
from ...video.containers import (
    VideoFilterContainer,
)


# pylint: disable=R0902
class VideoFilterAPITests(TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_list <greenday_api.video.video_api.VideoAPI.video_list>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoFilterAPITests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

        self.video_1 = self.create_video(
            project=self.project,
            channel_id=u"UCDASmtEzVZS5PZxjiRjcHKA",
            publish_date=datetime.datetime(2014, 1, 1, tzinfo=timezone.utc),
            name=u"Bazooka",
            duration=42)

        self.video_2 = self.create_video(
            channel_id=u"UCmA0uNMDy4wx9NHu1OfAw9g",
            publish_date=datetime.datetime(2014, 2, 1, tzinfo=timezone.utc),
            recorded_date=datetime.datetime(2014, 1, 15, tzinfo=timezone.utc),
            project=self.project)

        self.video_3 = self.create_video(
            channel_id=u"UCHX5-wIWTaClDu6uTKXKItg",
            publish_date=datetime.datetime(2014, 3, 1, tzinfo=timezone.utc),
            project=self.project)

        # Video 1: Millenium Falcon
        self.tag_1, self.project_tag_1, _, _ = self.create_video_instance_tag(
            name='Millennium Falcon',
            project=self.project,
            video=self.video_1,
            user=self.admin)

        # Video 2: Millenium Falcon
        self.create_video_instance_tag(
            video=self.video_2,
            user=self.admin,
            project_tag=self.project_tag_1)

        # Video 3: X-Wing
        self.tag_2, self.project_tag_2, _, _ = self.create_video_instance_tag(
            name='X-Wing',
            project=self.project,
            video=self.video_3,
            user=self.admin)

        # Video 2: Death Star
        self.tag_3, self.project_tag_3, _, _ = self.create_video_instance_tag(
            name='Death Star',
            project=self.project,
            video=self.video_2,
            user=self.admin)

        # Video 3: Death Star
        _, _, _, _ = self.create_video_instance_tag(
            project=self.project,
            video=self.video_3,
            user=self.admin)

        UserVideoDetail.objects.create(
            user=self.user, video=self.video_1, watched=True)
        UserVideoDetail.objects.create(
            user=self.admin, video=self.video_1, watched=False)

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

        self.other_video = self.create_video(
            youtube_video=self.video_1.youtube_video)

    def test_list(self):
        """
            List all videos
        """
        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.pk,
        )

        self._sign_in(self.admin)

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(3, len(response.items))
        self.assertEqual(0, response.items[0].order)
        self.assertEqual(self.video_1.pk, response.items[2].id)
        self.assertEqual(self.project.pk, response.items[2].project_id)
        self.assertEqual(
            self.video_1.videotags.count(), response.items[2].tag_count)
        self.assertEqual(
            self.video_1.related_users.filter(watched=True).count(),
            response.items[2].watch_count)
        self.assertEqual(
            [self.collection_2.pk],
            response.items[2].in_collections)
        self.assertEqual(0, response.items[0].duplicate_count)

    def test_list_not_assigned(self):
        """
            Current user not assigned to project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.video_list,
            VideoFilterContainer.combined_message_class(
                project_id=self.project.pk,
            )
        )

    def test_video_list_archived(self):
        """
            List all archived videos in project
        """
        archived_at = timezone.now().replace(microsecond=0)
        archived_video = self.create_video(
            project=self.project, archived_at=archived_at)

        self._sign_in(self.admin)

        video_list_container = VideoFilterContainer.combined_message_class(
            project_id=self.project.pk, archived=True
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(video_list_container)

        self.assertEqual(1, len(response.items))
        self.assertEqual(archived_video.pk, response.items[0].id)
        self.assertEqual(archived_at, response.items[0].archived_at)

    def test_filter_response_data(self):
        """
            Check API response data
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(3, len(response.items))

        for i, item in enumerate(response.items):
            self.assertEqual(i, getattr(item, 'order'))

        first_item = next(r for r in response.items if r.id == self.video_1.pk)
        self.assertEqual(self.video_1.pk, first_item.id)
        self.assertEqual(self.video_1.project_id, first_item.project_id)
        self.assertEqual(
            self.video_1.youtube_video.name, first_item.name)
        self.assertEqual(
            self.video_1.youtube_video.youtube_id, first_item.youtube_id)
        self.assertEqual(
            self.video_1.youtube_video.latitude, first_item.latitude)
        self.assertEqual(
            self.video_1.youtube_video.longitude, first_item.longitude)
        self.assertEqual(
            self.video_1.youtube_video.notes, first_item.notes)
        self.assertEqual(
            self.video_1.youtube_video.publish_date, first_item.publish_date)
        self.assertEqual(
            self.video_1.youtube_video.recorded_date, first_item.recorded_date)
        self.assertEqual(
            self.video_1.youtube_video.channel_id, first_item.channel_id)
        self.assertEqual(
            self.video_1.youtube_video.channel_name, first_item.channel_name)
        self.assertEqual(
            self.video_1.youtube_video.playlist_id, first_item.playlist_id)
        self.assertEqual(
            self.video_1.youtube_video.playlist_name, first_item.playlist_name)
        self.assertEqual(
            self.video_1.youtube_video.duration, first_item.duration)
        self.assertEqual(self.video_1.favourited, first_item.favourited)
        self.assertEqual(
            self.video_1.recorded_date_overridden,
            first_item.recorded_date_overridden)
        self.assertEqual(
            self.video_1.location_overridden,
            first_item.location_overridden)

    def test_filter_keyword(self):
        """
            Filter by keyword
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id, q=u"Bazooka")

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_1.pk, response.items[0].id)

    def test_filter_tags_single(self):
        """
            Filter by tag
        """
        self._sign_in(self.admin)

        # test single tag - video_3 is the only video tagged with
        # the X-Wing tag.
        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids="%s" % self.project_tag_2.pk
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_3.pk, response.items[0].id)

    def test_filter_tags_single_negation(self):
        """
            Filter by single negated tag
        """
        self._sign_in(self.admin)

        # test single tag - video_3 is the only video tagged with
        # the X-Wing tag. So video 3 should not be returned because
        # we are negating it in the filter
        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids="-%s" % self.project_tag_2.pk
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(2, len(response.items))
        self.assertEqual(self.video_1.pk, response.items[1].id)
        self.assertEqual(self.video_2.pk, response.items[0].id)

    def test_filter_tags_two(self):
        """
            Filter by two tags
        """
        self._sign_in(self.admin)

        # test two tags - videos 2 and 3 are tagged with X-Wing
        # and Death Star
        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids=",".join(
                (str(self.project_tag_2.pk), str(self.project_tag_3.pk))
            )
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(2, len(response.items))
        self.assertEqual(self.video_2.pk, response.items[1].id)
        self.assertEqual(self.video_3.pk, response.items[0].id)

    def test_filter_tags_two_negation(self):
        """
            Filter by two negated tags
        """
        self._sign_in(self.admin)

        # test two tags - videos 2 and 3 are tagged with X-Wing
        # and Death Star but we are going to negate the X-Wing tag
        # again so video 3 should not be returned
        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids=",".join(
                (str(self.project_tag_3.pk), '-%s' % self.project_tag_2.pk)
            )
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_2.pk, response.items[0].id)

    def test_filter_tags_multiple(self):
        """
            Filter by list of tags
        """
        self._sign_in(self.admin)

        # test multiple tags - videos 1, 2 and 3 are tagged with X-Wing,
        # Death Star and Millennium Falcon
        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            tag_ids=",".join(
                (
                    str(self.project_tag_1.pk),
                    str(self.project_tag_2.pk),
                    str(self.project_tag_3.pk)
                )
            )
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(3, len(response.items))
        result_ids = [r.id for r in response.items]
        self.assertIn(self.video_1.pk, result_ids)
        self.assertIn(self.video_2.pk, result_ids)
        self.assertIn(self.video_3.pk, result_ids)

    def test_filter_tags_multiple_with_negation(self):
        """
            Filter by combination of non-negated and negated tags
        """
        self._sign_in(self.admin)

        # test multiple tags - videos 1, 2 and 3 are tagged with X-Wing,
        # Death Star and Millennium Falcon. However, we are negating the
        # X-Wing tag and so video 3 should not be returned with the results
        # even though it has also been tagged with Death Star
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

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(2, len(response.items))
        result_ids = [r.id for r in response.items]
        self.assertIn(self.video_1.pk, result_ids)
        self.assertIn(self.video_2.pk, result_ids)

    def test_filter_date_between(self):
        """
            Filter published date between two dates
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__between__2014-1-20__2014-2-20"
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_2.pk, response.items[0].id)

    def test_filter_date_notbetween(self):
        """
            Filter published date not between two dates
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__notbetween__2014-1-20__2014-2-20"
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(2, len(response.items))
        result_ids = [r.id for r in response.items]
        self.assertIn(self.video_3.pk, result_ids)
        self.assertIn(self.video_1.pk, result_ids)

    def test_filter_date_after(self):
        """
            Filter published date after a date
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__after__2014-1-2"
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(2, len(response.items))
        # TODO: Need to add sorting to this test
        self.assertEqual(self.video_2.pk, response.items[1].id)
        self.assertEqual(self.video_3.pk, response.items[0].id)

    def test_filter_date_before(self):
        """
            Filter published date before a date
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__before__2014-2-2"
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(2, len(response.items))
        self.assertEqual(self.video_1.pk, response.items[1].id)
        self.assertEqual(self.video_2.pk, response.items[0].id)

    def test_filter_date_exact(self):
        """
            Filter published date exactly matches a date
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="publish_date__exact__2014-1-1"
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(1, len(response.items))

    def test_filter_recorded_date_exact(self):
        """
            Filter recorded date after a date
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            date="recorded_date__exact__2014-1-15"
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_2.pk, response.items[0].id)

    def test_filter_channel_id(self):
        """
            Filter by channel ID
        """
        self._sign_in(self.admin)

        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            channel_ids=",".join(
                (self.video_1.youtube_video.channel_id,
                    self.video_2.youtube_video.channel_id,)
            )
        )

        with self.assertNumQueries(5):
            response = self.api.video_list(request)

        # TODO: Add sorting
        self.assertEqual(2, len(response.items))
        self.assertEqual(self.video_1.pk, response.items[1].id)
        self.assertEqual(self.video_2.pk, response.items[0].id)

    @unittest.skip("Not supported by the API")
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
            response = self.api.video_list(request)

        self.assertEqual(1, len(response.items))
        self.assertEqual(self.video_2.pk, response.items[0].id)

        # multiple collection id
        request = VideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            collection_id=",".join(
                (str(self.collection_1.pk), str(self.collection_2.pk))
            )
        )

        with self.assertNumQueries(3):
            response = self.api.video_list(request)

        self.assertEqual(2, len(response.items))
        self.assertEqual(self.video_1.pk, response.items[0].id)
        self.assertEqual(self.video_2.pk, response.items[1].id)

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

        response = self.api.video_list(request)

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

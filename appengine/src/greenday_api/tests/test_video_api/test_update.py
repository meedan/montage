"""
    Update video tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
import mock
import datetime
from milkman.dairy import milkman
from django.utils import timezone

from greenday_core.constants import EventKind
from greenday_core.tests.base import TestCaseTagHelpers
from greenday_core.models import (
    Video,
    Project,
)


from ..base import ApiTestCase, TestEventBusMixin

from ...video.video_api import VideoAPI, YouTubeClient
from ...video.containers import VideoUpdateEntityContainer
from ...video.messages import VideoResponseMessage


a_date = timezone.now().replace(microsecond=0)

yt_vid_data = {
    'foo_45': dict(
            recorded_date=a_date,
            channel_name="channel",
            channel_id="channel_id",
            notes="notes",
            latitude=3.1,
            longitude=4.0,
            publish_date=a_date,
            duration=42,
            name='foo'
     )
}

def _mock_get_video_data(*args):
    return yt_vid_data


class VideoUpdateTests(TestEventBusMixin, TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_update <greenday_api.video.video_api.VideoAPI.video_update>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data

            Patch mocks
        """
        super(VideoUpdateTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(
            project=self.project,
            youtube_id="foo_45",
            latitude=9.4,
            longitude=10.5)

        self.yt_client_patcher = mock.patch.object(
            YouTubeClient,
            'get_video_data',
            new=_mock_get_video_data)
        self.m_get_video_data = self.yt_client_patcher.start()
        self.yt_discover_patcher = mock.patch.object(
            YouTubeClient, 'get_discovery_client')
        self.yt_discover_patcher.start()

    def tearDown(self):
        """
            Unpatch mocks
        """
        self.yt_client_patcher.stop()
        self.yt_discover_patcher.stop()
        super(VideoUpdateTests, self).tearDown()

    def test_video_update(self):
        """
            Update a video
        """
        self._sign_in(self.admin)

        # now update the object
        request = VideoUpdateEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=self.video.youtube_id,
            latitude=5.1,
            longitude=0.3,
            location_overridden=True,
            recorded_date=datetime.datetime(
                2010, 8, 1, tzinfo=timezone.utc),
            recorded_date_overridden=True,
            precise_location=True,
        )
        with self.assertEventRecorded(
                EventKind.VIDEOUPDATED,
                object_id=self.video.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(7):
            response = self.api.video_update(request)

        self.assertIsInstance(response, VideoResponseMessage)
        self.assertEqual(1, Video.objects.count())
        self.video = self.reload(self.video)
        self.assertEqual(self.video.project, self.project)
        self.assertEqual(
            self.video.youtube_video.youtube_id, request.youtube_id)

        self.assertEqual(self.video.latitude, 5.1)
        self.assertEqual(self.video.longitude, 0.3)
        self.assertEqual(
            self.video.location_overridden, request.location_overridden)

        self.assertEqual(self.video.recorded_date, datetime.datetime(
                2010, 8, 1, tzinfo=timezone.utc))
        self.assertTrue(self.video.recorded_date_overridden)

        for attr, val in yt_vid_data['foo_45'].items():
            self.assertEqual(val, getattr(self.video.youtube_video, attr))


class VideoPatchTests(TestEventBusMixin, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_patch <greenday_api.video.video_api.VideoAPI.video_patch>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoPatchTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(
            project=self.project,
            location_overridden=True,
            latitude=5.1,
            longitude=0.3
        )

    def test_patch_video_ok(self):
        """
            Patch a video
        """
        self._sign_in(self.user)

        request = VideoUpdateEntityContainer.combined_message_class(
            youtube_id=self.video.youtube_id,
            project_id=self.project.pk,
            recorded_date=datetime.datetime(
                2010, 8, 1, tzinfo=timezone.utc),
            recorded_date_overridden=True,
        )

        with self.assertEventRecorded(
                EventKind.VIDEOUPDATED,
                object_id=self.video.pk,
                video_id=self.video.pk,
                project_id=self.project.pk), self.assertNumQueries(6):
            self.api.video_patch(request)

        self.video = self.reload(self.video)
        self.assertEqual(self.video.latitude, 5.1)
        self.assertEqual(self.video.longitude, 0.3)
        self.assertTrue(self.video.location_overridden)

        self.assertEqual(self.video.recorded_date, datetime.datetime(
                2010, 8, 1, tzinfo=timezone.utc))
        self.assertTrue(self.video.recorded_date_overridden)


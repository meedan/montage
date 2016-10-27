"""
    Video creation tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
import mock
from milkman.dairy import milkman
from django.utils import timezone

from greenday_core.api_exceptions import BadRequestException, ForbiddenException
from greenday_core.constants import EventKind
from greenday_core.tests.base import TestCaseTagHelpers
from greenday_core.models import (
    Video,
    Project,
    Event
)

from ..base import ApiTestCase, TestEventBusMixin

from ...video.video_api import VideoAPI, YouTubeClient
from ...video.containers import (
    VideoInsertEntityContainer,
    CreateVideoBatchContainer
)
from ...video.messages import VideoResponseMessage


a_date = timezone.now().replace(microsecond=0)

core_vid_data = dict(
    recorded_date=a_date,
    channel_name="channel",
    channel_id="channel_id",
    notes="notes",
    latitude=3.1,
    longitude=4.0,
    publish_date=a_date,
    duration=42
)

vid_names = {
    'foo_45': 'foo',
    'bar_59': 'bar'
}

def _mock_get_video_data(_, youtube_ids):
    ret = {}
    for yt_id in youtube_ids:
        ret[yt_id] = core_vid_data.copy()
        ret[yt_id]['name'] = vid_names[yt_id]

    return ret


class VideoCreateTests(TestEventBusMixin, TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_insert <greenday_api.video.video_api.VideoAPI.video_insert>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap data

            Patch mocks
        """
        super(VideoCreateTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

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
        super(VideoCreateTests, self).tearDown()

    def test_create_videos(self):
        """
            Add videos
        """
        video_container = VideoInsertEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id="foo_45",
        )
        # Check that users who are not assigned to the project can't create
        # corpus objects
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.video_insert,
            video_container)

        # But admins can
        self._sign_in(self.admin)
        with self.assertEventRecorded(
                EventKind.VIDEOCREATED,
                object_id=True,
                video_id=True,
                project_id=self.project.pk), self.assertNumQueries(10):
            response = self.api.video_insert(video_container)
        self.assertIsInstance(response, VideoResponseMessage)
        self.assertEqual(1, Video.objects.count())
        video = Video.objects.get(pk=response.id)

        self.assertEqual(video.project, self.project)
        self.assertEqual(video.youtube_video.youtube_id, response.youtube_id)
        self.assertEqual(video.user, self.admin)

        for attr, val in core_vid_data.items():
            self.assertEqual(val, getattr(video.youtube_video, attr))
            self.assertEqual(val, getattr(response, attr))

        self.assertEqual(vid_names['foo_45'], video.youtube_video.name)

    def test_add_video_already_exists_on_project(self):
        """
            Add video which already exists on the project
        """
        existing_video = self.create_video(
            project=self.project, youtube_id="foo_45")
        video_container = VideoInsertEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=existing_video.youtube_video.youtube_id)

        self._sign_in(self.admin)

        self.assertRaises(
            BadRequestException,
            self.api.video_insert,
            video_container)

    def test_add_video_youtube_video_exists(self):
        """
            Add video which exists on another project
        """
        yt_video = self.create_video(youtube_id="foo_45").youtube_video

        video_container = VideoInsertEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=yt_video.youtube_id
        )

        # But admins can
        self._sign_in(self.admin)
        with self.assertEventRecorded(
                EventKind.VIDEOCREATED,
                object_id=True,
                video_id=True,
                project_id=self.project.pk), self.assertNumQueries(8):
            response = self.api.video_insert(video_container)
        self.assertIsInstance(response, VideoResponseMessage)
        self.assertEqual(1, self.project.videos.count())
        video = Video.objects.get(pk=response.id)

        self.assertEqual(video.project, self.project)
        self.assertEqual(video.youtube_video, yt_video)
        self.assertEqual(yt_video.youtube_id, response.youtube_id)
        self.assertEqual(video.user, self.admin)

    def test_readd_deleted_video(self):
        """
            Add video previously trashed video
        """
        video = self.create_video(project=self.project, youtube_id="foo_45")
        video.delete()

        self.assertEqual(0, Video.objects.count())
        self.assertEqual(1, Video.trash.count())

        self._sign_in(self.admin)

        request = VideoInsertEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=video.youtube_video.youtube_id
        )

        with self.assertEventRecorded(
                EventKind.VIDEOCREATED,
                object_id=True,
                video_id=True,
                project_id=self.project.pk), self.assertNumQueries(8):
            response = self.api.video_insert(request)

        self.assertIsInstance(response, VideoResponseMessage)
        self.assertEqual(1, Video.objects.count())
        self.assertEqual(0, Video.trash.count())
        video = self.reload(video)
        self.assertEqual(video.project, self.project)
        self.assertEqual(video.youtube_video.youtube_id, response.youtube_id)

    def test_readd_archived_video(self):
        """
            Add video previously archived
        """
        self._sign_in(self.admin)

        yt_id = "foo_45"
        archived_video = self.create_video(
            project=self.project,
            archived_at=timezone.now(),
            youtube_id=yt_id)

        request = VideoInsertEntityContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_id=yt_id
        )
        with self.assertEventRecorded(
                EventKind.VIDEOCREATED,
                object_id=True,
                video_id=True,
                project_id=self.project.pk), self.assertNumQueries(8):
            response = self.api.video_insert(request)

        self.assertIsInstance(response, VideoResponseMessage)
        self.assertEqual(1, Video.objects.count())
        self.assertEqual(0, Video.trash.count())
        self.assertEqual(0, Video.archived_objects.count())

        video = self.reload(archived_video)
        self.assertFalse(video.archived_at)
        self.assertEqual("foo", video.youtube_video.name)
        self.assertEqual(yt_id, video.youtube_video.youtube_id)


class VideoBatchCreateTests(ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_batch_create <greenday_api.video.video_api.VideoAPI.video_batch_create>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap test data

            Patch mocks
        """
        super(VideoBatchCreateTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

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
        super(VideoBatchCreateTests, self).tearDown()

    def test_video_batch_create(self):
        """
            Add list of videos
        """
        self._sign_in(self.user)

        request = CreateVideoBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_ids=["foo_45", "bar_59"]
        )

        with self.assertNumQueries(18):
            response = self.api.video_batch_create(request)
        self.assertEqual(2, len(response.items))
        self.assertEqual(2, len(response.videos))
        self.assertEqual(2, Video.objects.all().count())

        self.assertTrue(response.items[0].success)
        self.assertTrue(response.items[1].success)

        video_1 = Video.objects.get(youtube_id=response.items[0].youtube_id)
        for attr, val in core_vid_data.items():
            self.assertEqual(val, getattr(video_1.youtube_video, attr))
            self.assertEqual(val, getattr(response.videos[0], attr))

        self.assertEqual(vid_names['foo_45'], video_1.youtube_video.name)

        self.assertEqual(
            2,
            Event.objects.filter(
                kind=EventKind.VIDEOCREATED,
                object_id__isnull=False,
                project_id=self.project.pk,
                user=self.user
            ).count()
        )

    def test_video_batch_create_already_exists(self):
        """
            Add video already added
        """
        self._sign_in(self.user)

        existing_video = self.create_video(
            project=self.project,
            name="foo",
            youtube_id="foo_45"
        )

        # video being added on another project should be allowed
        other_project_video = self.create_video(
            name="bar",
            youtube_id="bar_59"
        )

        request = CreateVideoBatchContainer.combined_message_class(
            project_id=self.project.pk,
            youtube_ids=["foo_45", "bar_59"]
        )

        response = self.api.video_batch_create(request)
        self.assertEqual(2, len(response.items))

        self.assertTrue(response.items[0].success)
        self.assertFalse(response.items[1].success)
        self.assertTrue(response.items[1].msg)
        self.assertEqual(existing_video.youtube_id, response.items[1].youtube_id)

        self.assertEqual(2, len(response.videos))

"""
    Video tests for :mod:`greenday_api.video.video_api <greenday_api.video.video_api>`
"""
# LIBRARIES
from milkman.dairy import milkman

# FRAMEWORK
from django.utils import timezone

# GREENDAY
from greenday_core.api_exceptions import ForbiddenException, NotFoundException
from greenday_core.models import (
    Project,
    UserVideoDetail,
    VideoCollection
)
from greenday_core.tests.base import TestCaseTagHelpers

from ..base import ApiTestCase, TestEventBusMixin

from ...video.messages import VideoResponseMessage
from ...video.video_api import VideoAPI
from ...video.containers import (
    VideoEntityContainer,
    VideoFilterContainer,
)


class VideoAPITests(TestEventBusMixin, TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_api.VideoAPI.video_get <greenday_api.video.video_api.VideoAPI.video_get>`
    """
    api_type = VideoAPI

    def setUp(self):
        """
            Bootstrap data
        """
        super(VideoAPITests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.video = self.create_video(project=self.project)

        UserVideoDetail.objects.create(
            user=self.user, video=self.video, watched=True)
        UserVideoDetail.objects.create(
            user=self.admin, video=self.video, watched=False)

        self.create_video_instance_tag(project=self.project, video=self.video)

        self.collection = milkman.deliver(
            VideoCollection, project=self.project)
        self.collection.add_video(self.video)

    def test_get_ok(self):
        """
            Get a video
        """
        request = VideoEntityContainer.combined_message_class(
            youtube_id=self.video.youtube_id,
            project_id=self.project.pk,
        )

        self._sign_in(self.user)

        with self.assertNumQueries(6):
            response = self.api.video_get(request)
        self.assertIsInstance(response, VideoResponseMessage)
        self.assertEqual(self.video.pk, response.id)
        self.assertEqual(self.project.pk, response.project_id)
        self.assertEqual(self.video.videotags.count(), response.tag_count)
        self.assertEqual(
            self.video.related_users.filter(watched=True).count(),
            response.watch_count)
        self.assertTrue(response.watched)
        self.assertEqual(0, response.duplicate_count)
        self.assertEqual(
            [self.collection.pk],
            response.in_collections)

    def test_get_not_assigned(self):
        """
            Get a video - user not assigned to project
        """
        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException,
            self.api.video_get,
            VideoEntityContainer.combined_message_class(
                youtube_id=self.video.youtube_id,
                project_id=self.project.pk,
            )
        )

    def test_video_get_archived(self):
        """
            Get an archived video
        """
        archived_at = timezone.now().replace(microsecond=0)
        archived_video = self.create_video(
            project=self.project, archived_at=archived_at)

        self._sign_in(self.user)

        request = VideoEntityContainer.combined_message_class(
            youtube_id=archived_video.youtube_id,
            project_id=self.project.pk,
        )
        with self.assertNumQueries(6):
            response = self.api.video_get(request)

        self.assertEqual(archived_at, response.archived_at)

    def test_404_is_raised(self):
        """
            Get a non-existant video
        """
        self._sign_in(self.user)
        # Test it with a non-existant corpus object
        self.assertRaises(
            NotFoundException,
            self.api.video_get,
            VideoEntityContainer.combined_message_class(
                youtube_id="9999", project_id=self.project.pk)
        )

        # Test it with a non-existant project
        self.assertRaises(
            NotFoundException,
            self.api.video_get,
            VideoEntityContainer.combined_message_class(
                youtube_id=self.video.youtube_id, project_id=9999)
        )

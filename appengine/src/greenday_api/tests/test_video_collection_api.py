"""
    Tests for :mod:`greenday_api.video.video_collection_api <greenday_api.video.video_collection_api>`
"""
import datetime
# LIBRARIES
from milkman.dairy import milkman

# FRAMEWORK
from django.utils import timezone

# GREENDAY
from greenday_core.api_exceptions import NotFoundException
from greenday_core.models import VideoCollection, Video, Project
from greenday_core.constants import EventKind
from greenday_core.tests.base import TestCaseTagHelpers

from .base import ApiTestCase, TestEventBusMixin

from ..video.messages import CollectionResponseMessageSkinny

from ..video.video_collection_api import VideoCollectionAPI
from ..video.containers import (
    CollectionEntityContainer,
    CollectionInsertEntityContainer,
    CollectionUpdateEntityContainer,
    CollectionListContainer,
    CollectionVideoContainer,
    CollectionDeleteVideoContainer,
    CollectionVideoBatchContainer,
    MoveCollectionVideoContainer,
    CollectionVideoFilterContainer
)


class VideoCollectionAPITests(
        TestEventBusMixin, TestCaseTagHelpers, ApiTestCase):
    """
        Tests for :class:`greenday_api.video.video_collection_api.VideoCollectionAPI <greenday_api.video.video_collection_api.VideoCollectionAPI>`
    """
    api_type = VideoCollectionAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoCollectionAPITests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_admin(self.user, pending=False)

    def test_video_collection_insert(self):
        """
            Create new collection
        """
        self._sign_in(self.user)
        request = CollectionInsertEntityContainer.combined_message_class(
            project_id=self.project.pk, name="foo")

        with self.assertEventRecorded(
                EventKind.VIDEOCOLLECTIONCREATED,
                object_id=True,
                project_id=self.project.pk), self.assertNumQueries(6):
            response = self.api.video_collection_insert(request)

        self.assertEqual(response.project_id, self.project.pk)
        self.assertEqual(response.name, request.name)

        collection = VideoCollection.objects.get()

        self.assertEqual(collection.project_id, self.project.pk)
        self.assertEqual(collection.name, request.name)

    def test_video_collection_get(self):
        """
            Get a collection
        """
        self._sign_in(self.user)
        collection = milkman.deliver(
            VideoCollection, project=self.project)
        video = self.create_video(project=self.project, duration=42)
        video_2 = self.create_video(project=self.project, duration=2)

        self.create_video_instance_tag(
            name='Foo', project=self.project, video=video)

        # intentionally add video_2 first to check ordering
        collection.add_video(video_2)
        collection.add_video(video)

        with self.assertNumQueries(5):
            response = self.api.video_collection_get(
                CollectionEntityContainer.combined_message_class(
                    project_id=self.project.pk,
                    id=collection.pk))

        self.assertEqual(response.name, collection.name)

        self.assertEqual(len(response.videos), 2)
        self.assertEqual(response.videos[0].id, video_2.pk)
        self.assertEqual(response.videos[0].order, 0)
        self.assertEqual(response.videos[1].id, video.pk)
        self.assertEqual(response.videos[1].order, 1)

    def test_video_collection_list(self):
        """
            List all collections for project
        """
        self._sign_in(self.user)
        collection_1 = milkman.deliver(VideoCollection, project=self.project)
        milkman.deliver(VideoCollection, project=self.project)

        video = self.create_video(project=self.project)
        collection_1.add_video(video)

        with self.assertNumQueries(4):
            response = self.api.video_collection_list(
                CollectionListContainer.combined_message_class(
                    project_id=self.project.pk)
            )

        self.assertEqual(len(response.items), 2)
        self.assertIsInstance(
            response.items[0], CollectionResponseMessageSkinny)

    def test_video_collection_update(self):
        """
            Update a collection
        """
        self._sign_in(self.user)
        collection = milkman.deliver(VideoCollection, project=self.project)

        request = CollectionUpdateEntityContainer.combined_message_class(
            name="bar", project_id=self.project.pk, id=collection.pk
        )

        with self.assertEventRecorded(
                EventKind.VIDEOCOLLECTIONUPDATED,
                object_id=collection.pk,
                project_id=self.project.pk), self.assertNumQueries(7):
            self.api.video_collection_update(request)

        collection = VideoCollection.objects.get(pk=collection.pk)

        self.assertEqual(request.name, collection.name)

    def test_video_collection_delete(self):
        """
            Delete a collection
        """
        self._sign_in(self.user)
        collection = milkman.deliver(VideoCollection, project=self.project)

        with self.assertEventRecorded(
                EventKind.VIDEOCOLLECTIONDELETED,
                object_id=collection.pk,
                project_id=self.project.pk), self.assertNumQueries(7):
            self.api.video_collection_delete(
                CollectionEntityContainer.combined_message_class(
                    project_id=self.project.pk,
                    id=collection.pk))

        self.assertEqual(0, len(VideoCollection.objects.all()))

    def test_add_video_to_collection(self):
        """
            Add a vide to a collection
        """
        self._sign_in(self.user)
        collection = milkman.deliver(
            VideoCollection, project=self.project)

        video = self.create_video(project=self.project)

        request = CollectionVideoContainer.combined_message_class(
            project_id=self.project.pk,
            id=collection.pk,
            youtube_id=video.youtube_id
        )

        with self.assertEventRecorded(
                EventKind.VIDEOADDEDTOCOLLECTION,
                object_id=video.pk,
                video_id=video.pk,
                project_id=self.project.pk,
                meta=str(collection.pk)), self.assertNumQueries(10):
            self.api.add_video_to_collection(request)

        self.assertEqual(video.collections.get(), collection)
        self.assertEqual(collection.videos.get(), video)

    def test_add_video_batch_to_collection(self):
        """
            Add a list of videos to a collection
        """
        self._sign_in(self.user)
        collection = milkman.deliver(
            VideoCollection, project=self.project)

        video = self.create_video(project=self.project)
        video2 = self.create_video(project=self.project)

        request = CollectionVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, id=collection.pk,
            youtube_ids=[video.youtube_id, video2.youtube_id]
        )

        with self.assertNumQueries(14):
            response = self.api.add_video_batch_to_collection(request)

        for vid in (video, video2,):
            item = next(i for i in response.items if i.youtube_id == vid.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertTrue(response.items[0].success)

            self.assertTrue(v for v in response.videos if v.youtube_id == vid.youtube_id)

        self.assertEqual(video.collections.get(), collection)
        self.assertEqual(2, len(collection.videos.all()))

    def test_remove_video_batch_from_collection(self):
        """
            Remove a list of videos from a collection
        """
        self._sign_in(self.user)
        collection = milkman.deliver(
            VideoCollection, project=self.project)

        video = self.create_video(project=self.project)
        video2 = self.create_video(project=self.project)
        video3 = self.create_video(project=self.project)

        request = CollectionVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, id=collection.pk,
            youtube_ids=[video.youtube_id, video2.youtube_id, video3.youtube_id]
        )

        with self.assertNumQueries(18):
            response = self.api.add_video_batch_to_collection(request)

        for vid in (video, video2, video3):
            item = next(i for i in response.items if i.youtube_id == vid.youtube_id)
            self.assertEqual(item.msg, 'ok')
            self.assertTrue(response.items[0].success)

            self.assertTrue(v for v in response.videos if v.youtube_id == vid.youtube_id)

        self.assertEqual(video.collections.get(), collection)
        self.assertEqual(3, len(collection.videos.all()))

        # now lets remove video and video 3 from the collection
        request = CollectionVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, id=collection.pk,
            youtube_ids=[video.youtube_id, video3.youtube_id]
        )

        with self.assertNumQueries(11):
            response = self.api.remove_video_batch_from_collection(request)
        self.assertEqual(1, len(collection.videos.all()))
        self.assertEqual(video2, collection.videos.get())

    def test_add_video_batch_to_collection_video_does_not_exist(self):
        """
            Add a list of videos to a collection where a vide does exist
        """
        self._sign_in(self.user)
        collection = milkman.deliver(
            VideoCollection, project=self.project)

        video = self.create_video(project=self.project)

        request = CollectionVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, id=collection.pk,
            youtube_ids=[video.youtube_id, "9999"]
        )

        with self.assertNumQueries(10):
            response = self.api.add_video_batch_to_collection(request)

        self.assertEqual(response.items[0].youtube_id, video.youtube_id)
        self.assertEqual(response.items[1].youtube_id, '9999')
        self.assertEqual(response.items[0].msg, 'ok')
        self.assertEqual(
            response.items[1].msg, 'Video with youtube_id 9999 does not exist')
        self.assertEqual(response.items[0].success, True)
        self.assertEqual(response.items[1].success, False)

        self.assertEqual(video.collections.get(), collection)
        self.assertEqual(1, len(collection.videos.all()))

    def test_add_video_batch_to_collection_video_already_in_collection(self):
        """
            Add a list of videos to a collection where a video is already
            in the collection
        """
        self._sign_in(self.user)
        collection = milkman.deliver(
            VideoCollection, project=self.project)

        video = self.create_video(project=self.project)
        video2 = self.create_video(project=self.project)
        collection.add_video(video2)

        request = CollectionVideoBatchContainer.combined_message_class(
            project_id=self.project.pk, id=collection.pk,
            youtube_ids=[video.youtube_id, video2.youtube_id]
        )

        with self.assertNumQueries(10):
            response = self.api.add_video_batch_to_collection(request)

        self.assertEqual(2, len(response.videos))

        self.assertEqual(response.items[0].youtube_id, video.youtube_id)
        self.assertEqual(response.items[1].youtube_id, video2.youtube_id)
        self.assertEqual(response.items[0].msg, 'ok')
        self.assertEqual(
            response.items[1].msg, 'Video is already in collection')
        self.assertEqual(response.items[0].success, True)
        self.assertEqual(response.items[1].success, False)

        self.assertEqual(video.collections.get(), collection)
        self.assertEqual(2, len(collection.videos.all()))

    def test_remove_video_from_collection(self):
        """
            Remove a video from a collection
        """
        self._sign_in(self.user)
        collection = milkman.deliver(
            VideoCollection, project=self.project)

        video = self.create_video(project=self.project)
        collection.add_video(video)

        request = CollectionDeleteVideoContainer.combined_message_class(
            project_id=self.project.pk,
            id=collection.pk,
            youtube_id=video.youtube_id
        )

        with self.assertEventRecorded(
                EventKind.VIDEOREMOVEDFROMCOLLECTION,
                object_id=video.pk,
                video_id=video.pk,
                project_id=self.project.pk,
                meta=str(collection.pk)), self.assertNumQueries(11):
            self.api.remove_video_from_collection(request)

        video = Video.objects.get(pk=video.pk)
        self.assertEqual(0, video.collections.count())
        self.assertEqual(0, collection.videos.count())

    def test_add_video_to_collection_different_project(self):
        """
            Add a video to a collection in a different project
        """
        self._sign_in(self.user)
        another_project = milkman.deliver(Project)
        another_project.set_owner(self.admin)
        another_project.add_assigned(self.user, pending=False)

        video = self.create_video(project=another_project)

        collection = milkman.deliver(VideoCollection, project=self.project)

        request = CollectionVideoContainer.combined_message_class(
            project_id=self.project.pk,
            id=collection.pk,
            youtube_id=video.youtube_id
        )

        self.assertRaises(
            NotFoundException,
            self.api.add_video_to_collection,
            request)

    def test_list_collection_videos(self):
        """
            List all videos in a collection
        """
        self._sign_in(self.user)

        collection = milkman.deliver(
            VideoCollection, project=self.project)

        video = self.create_video(project=self.project, duration=42)
        video_2 = self.create_video(project=self.project, duration=2)

        self.create_video_instance_tag(
            name='Foo', project=self.project, video=video)

        # intentionally add video_2 first to check ordering
        collection.add_video(video_2)
        collection.add_video(video)

        with self.assertNumQueries(6):
            response = self.api.video_collection_video_list(
                CollectionVideoFilterContainer.combined_message_class(
                    project_id=self.project.pk,
                    id=collection.pk))

        self.assertEqual(len(response.items), 2)
        self.assertEqual(response.items[0].id, video_2.pk)
        self.assertEqual(response.items[1].id, video.pk)


class VideoCollectionAPIMoveVideoTests(ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_collection_api.VideoCollectionAPI.move_video_in_collection <greenday_api.video.video_collection_api.VideoCollectionAPI.move_video_in_collection>`
    """
    api_type = VideoCollectionAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoCollectionAPIMoveVideoTests, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_admin(self.user, pending=False)

        self.collection = milkman.deliver(
            VideoCollection, project=self.project)

        self.video = self.create_video(project=self.project)
        self.video2 = self.create_video(project=self.project)
        self.video3 = self.create_video(project=self.project)

        self.collection.add_video(self.video)
        self.collection.add_video(self.video2)
        self.collection.add_video(self.video3)

        self._sign_in(self.user)

    def test_move_video_to_end(self):
        """
            Move video to end of collection
        """
        request = MoveCollectionVideoContainer.combined_message_class(
            project_id=self.project.pk,
            id=self.collection.pk,
            youtube_id=self.video.youtube_id,
            sibling_youtube_id=self.video3.youtube_id
        )
        with self.assertNumQueries(10):
            response = self.api.move_video_in_collection(request)

        self.assertEqual(
            [self.video2.pk, self.video3.pk, self.video.pk],
            [v.pk for v in self.collection.ordered_videos])

    def test_move_video_to_middle(self):
        """
            Move video to middle to end of collection
        """
        request = MoveCollectionVideoContainer.combined_message_class(
            project_id=self.project.pk,
            id=self.collection.pk,
            youtube_id=self.video.youtube_id,
            sibling_youtube_id=self.video2.youtube_id
        )
        with self.assertNumQueries(10):
            response = self.api.move_video_in_collection(request)

        self.assertEqual(
            [self.video2.pk, self.video.pk, self.video3.pk],
            [v.pk for v in self.collection.ordered_videos])

    def test_move_video_to_start(self):
        """
            Move video to start of collection
        """
        request = MoveCollectionVideoContainer.combined_message_class(
            project_id=self.project.pk,
            id=self.collection.pk,
            youtube_id=self.video.youtube_id,
            sibling_youtube_id=self.video2.youtube_id,
            before=True
        )
        with self.assertNumQueries(10):
            response = self.api.move_video_in_collection(request)

        self.assertEqual(
            [self.video.pk, self.video2.pk, self.video3.pk],
            [v.pk for v in self.collection.ordered_videos])


class VideoCollectionFilterAPITests(ApiTestCase):
    """
        Tests for :func:`greenday_api.video.video_collection_api.VideoCollectionAPI.video_collection_video_list <greenday_api.video.video_collection_api.VideoCollectionAPI.video_collection_video_list>`
    """
    api_type = VideoCollectionAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoCollectionFilterAPITests, self).setUp()
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
            project=self.project,
            name=u"Bazooka 2")

        self.collection_1 = milkman.deliver(
            VideoCollection, project=self.project, name='Collection 1')
        self.collection_1.add_video(self.video_2)
        self.collection_1.add_video(self.video_1)

        self.other_video = self.create_video(youtube_video=self.video_1.youtube_video)

    def test_filter_response_data(self):
        """
            Test response data from endpoint
        """
        self._sign_in(self.admin)

        request = CollectionVideoFilterContainer.combined_message_class(
            project_id=self.project.id,
            id=self.collection_1.pk,
            q="Bazooka"
        )

        with self.assertNumQueries(6):
            response = self.api.video_collection_video_list(request)

        self.assertEqual(2, len(response.items))

        first_item = response.items[0]
        self.assertEqual(self.video_2.pk, first_item.id)
        self.assertEqual(0, first_item.order)
        self.assertEqual(self.video_2.project_id, first_item.project_id)
        self.assertEqual(self.video_2.youtube_video.name, first_item.name)
        self.assertEqual(
            self.video_2.youtube_video.youtube_id, first_item.youtube_id)
        self.assertEqual(
            self.video_2.youtube_video.latitude, first_item.latitude)
        self.assertEqual(
            self.video_2.youtube_video.longitude, first_item.longitude)
        self.assertEqual(self.video_2.youtube_video.notes, first_item.notes)
        self.assertEqual(
            self.video_2.youtube_video.publish_date, first_item.publish_date)
        self.assertEqual(
            self.video_2.youtube_video.recorded_date, first_item.recorded_date)
        self.assertEqual(
            self.video_2.youtube_video.channel_id, first_item.channel_id)
        self.assertEqual(
            self.video_2.youtube_video.channel_name, first_item.channel_name)
        self.assertEqual(
            self.video_2.youtube_video.playlist_id, first_item.playlist_id)
        self.assertEqual(
            self.video_2.youtube_video.playlist_name, first_item.playlist_name)
        self.assertEqual(
            self.video_2.youtube_video.duration, first_item.duration)
        self.assertEqual(self.video_2.favourited, first_item.favourited)
        self.assertEqual(
            self.video_2.recorded_date_overridden,
            first_item.recorded_date_overridden)
        self.assertEqual(
            self.video_2.location_overridden,
            first_item.location_overridden)

        response.items[1].order = 1

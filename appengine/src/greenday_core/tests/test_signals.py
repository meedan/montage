"""
    Tests for :mod:`greenday_core.signals <greenday_core.signals>`
"""
import mock
from milkman.dairy import milkman

# import django deps
from django.contrib.auth import get_user_model

# import project deps
from ..models import (
    Project,
    GlobalTag,
    ProjectTag,
    VideoTag,
    VideoTagInstance,
    PendingUser,
    VideoCollection,
    VideoCollectionVideo,
    TimedVideoComment
)
from .base import AppengineTestBed


class BaseSignalsTestCase(AppengineTestBed):
    """
        Base test case for signal tests
    """
    def setUp(self):
        super(BaseSignalsTestCase, self).setUp()
        self.admin = milkman.deliver(
            get_user_model(),
            email="admin@example.com")


# test project signals
class ProjectSignalsTestCase(BaseSignalsTestCase):
    """
        Tests for :class:`greenday_core.models.project.Project <greenday_core.models.project.Project>` signals
    """
    @mock.patch('greenday_core.signals.index_project_document')
    def test_process_project_search_document_handler_create(
            self, mock_index_project_document):
        """
            Project created
        """
        project = Project.objects.create(name='foo')
        mock_index_project_document.assert_called_once_with(project.pk)

    @mock.patch('greenday_core.signals.index_project_document')
    def test_process_project_search_document_handler_update(
            self, mock_index_project_document):
        """
            Project updated
        """
        project = Project.objects.create(name='foo')
        mock_index_project_document.reset_mock()

        project.save()
        mock_index_project_document.assert_called_once_with(project.pk)

    @mock.patch('greenday_core.signals.index_project_document')
    def test_delete_project_search_document_handler(
            self, mock_index_project_document):
        """
            Project deleted
        """
        project = Project.objects.create(name='foo')
        project_id = project.pk
        mock_index_project_document.reset_mock()

        project.delete()
        mock_index_project_document.assert_called_once_with(project_id)


# test tag signals
class TagSignalsTestCase(BaseSignalsTestCase):
    """
        Tests for :class:`greenday_core.models.tag.GlobalTag <greenday_core.models.tag.GlobalTag>` signals
    """
    @mock.patch('greenday_core.signals.index_global_tag_document')
    def test_process_global_tag_search_document_create(
            self, mock_index_global_tag_document):
        """
            Tag created
        """
        project = Project.objects.create(name='foo')
        tag = GlobalTag.objects.create(
            name='foo', created_from_project=project)
        mock_index_global_tag_document.assert_called_once_with(tag.pk)

    @mock.patch('greenday_core.signals.index_global_tag_document')
    def test_process_global_tag_search_document_update(
            self, mock_index_global_tag_document):
        """
            Tag updated
        """
        project = Project.objects.create(name='foo')
        tag = GlobalTag.objects.create(
            name='foo', created_from_project=project)
        mock_index_global_tag_document.reset_mock()

        tag.save()
        mock_index_global_tag_document.assert_called_once_with(tag.pk)

    @mock.patch('greenday_core.signals.index_global_tag_document')
    def test_delete_global_tag_search_document(
            self, mock_index_global_tag_document):
        """
            Tag deleted
        """
        project = Project.objects.create(name='foo')
        tag = GlobalTag.objects.create(
            name='foo', created_from_project=project)
        tag_id = tag.pk
        mock_index_global_tag_document.reset_mock()

        tag.delete()
        mock_index_global_tag_document.assert_called_once_with(tag_id)


class ProjectTagSignalsTestCase(BaseSignalsTestCase):
    """
        Tests for :class:`greenday_core.models.tag.ProjectTag <greenday_core.models.tag.ProjectTag>` signals
    """
    @mock.patch('greenday_core.signals.index_global_tag_document')
    def test_save_project_tag_search_document(
            self, mock_index_global_tag_document):
        """
            Project tag created
        """
        tag = milkman.deliver(GlobalTag)
        mock_index_global_tag_document.reset_mock()

        ProjectTag.add_root(project=milkman.deliver(Project), global_tag=tag)
        mock_index_global_tag_document.assert_called_once_with(tag.pk)

    @mock.patch('greenday_core.signals.index_global_tag_document')
    def test_delete_project_tag_search_document(
            self, mock_index_global_tag_document):
        """
            Project tag deleted
        """
        tag = milkman.deliver(GlobalTag)
        project_tag = ProjectTag.add_root(
            project=milkman.deliver(Project), global_tag=tag)
        mock_index_global_tag_document.reset_mock()

        project_tag.delete()
        mock_index_global_tag_document.assert_called_once_with(tag.pk)


# test user signals
class UserSignalsTestCase(BaseSignalsTestCase):
    """
        Tests for :class:`greenday_core.models.user.User <greenday_core.models.user.User>` signals
    """
    @mock.patch('greenday_core.signals.index_auto_complete_user')
    def test_process_user_search_document_create(
            self, mock_index_auto_complete_user):
        """
            User created
        """
        user = get_user_model().objects.create(
            email='user@example.com')
        mock_index_auto_complete_user.assert_called_once_with(user.email)

    @mock.patch('greenday_core.signals.index_auto_complete_user')
    def test_process_user_search_document_update(
            self, mock_index_auto_complete_user):
        """
            User updated
        """
        user = get_user_model().objects.create(
            email='user@example.com')
        mock_index_auto_complete_user.reset_mock()

        user.save()
        mock_index_auto_complete_user.assert_called_once_with(user.email)

    @mock.patch('greenday_core.signals.index_auto_complete_user')
    def test_delete_user_search_document(
            self, mock_index_auto_complete_user):
        """
            User deleted
        """
        user = get_user_model().objects.create(
            email='user@example.com')
        email = user.email
        mock_index_auto_complete_user.reset_mock()

        user.delete()
        mock_index_auto_complete_user.assert_called_once_with(email)


# test pending user signals
class PendingUserSignalsTestCase(BaseSignalsTestCase):
    """
        Tests for :class:`greenday_core.models.user.PendingUser <greenday_core.models.user.PendingUser>` signals
    """
    @mock.patch('greenday_core.signals.index_auto_complete_user')
    def test_process_pending_user_search_document_create(
            self, mock_index_auto_complete_user):
        """
            Pending user created
        """
        user = PendingUser.objects.create(email='user@example.com')
        mock_index_auto_complete_user.assert_called_once_with(user.email)

    @mock.patch('greenday_core.signals.index_auto_complete_user')
    def test_process_pending_user_search_document_update(
            self, mock_index_auto_complete_user):
        """
            Pending user updated
        """
        user = PendingUser.objects.create(email='user@example.com')
        mock_index_auto_complete_user.reset_mock()

        user.save()
        mock_index_auto_complete_user.assert_called_once_with(user.email)

    @mock.patch('greenday_core.signals.index_auto_complete_user')
    def test_delete_pending_user_search_document(
            self, mock_index_auto_complete_user):
        """
            Pending user deleted
        """
        user = PendingUser.objects.create(email='user@example.com')
        email = user.email
        mock_index_auto_complete_user.reset_mock()

        user.delete()
        mock_index_auto_complete_user.assert_called_once_with(email)


# test VideoCollectionVideo signals
class VideoCollectionVideoSignalsTestCase(BaseSignalsTestCase):
    """
        Tests for :class:`greenday_core.models.video.VideoCollection <greenday_core.models.video.VideoCollection>` signals
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoCollectionVideoSignalsTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.video = self.create_video()
        self.collection = milkman.deliver(
            VideoCollection, project=self.project)

    @mock.patch('greenday_core.signals.index_video_document')
    def test_video_collection_video_reprocess_video_search_document_add(
            self, mock_reprocess_index_video_document):
        """
            Video added to collection
        """
        # tests the video document is updated when a video is added to
        # a collection
        self.collection.add_video(self.video)
        added = VideoCollectionVideo.objects.get(
            collection=self.collection, video=self.video)
        mock_reprocess_index_video_document.assert_called_once_with(
            added.video.pk)

    def test_video_collection_video_reprocess_video_search_document_remove(
            self):
        """
            Video removed from collection
        """
        # tests the video document is updated when a video is removed from
        # a collection
        self.collection.add_video(self.video)
        with mock.patch(
                'greenday_core.signals.index_video_document') as \
                mock_reprocess_index_video_document:
            self.collection.remove_video(self.video)
            mock_reprocess_index_video_document.assert_called_once_with(
                self.video.pk)


class VideoSignalsTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.video.Video <greenday_core.models.video.Video>` signals
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoSignalsTestCase, self).setUp()
        self.project = milkman.deliver(Project)

    @mock.patch('greenday_core.signals.index_video_document')
    def test_process_video_search_document_handler_create(
            self, mock_index_video_document):
        """
            Video created
        """
        video = self.create_video(project=self.project)
        mock_index_video_document.assert_called_once_with(video.pk)

    @mock.patch('greenday_core.signals.index_video_document')
    def test_process_video_search_document_handler_update(
            self, mock_index_video_document):
        """
            Video updated
        """
        video = self.create_video(project=self.project)
        mock_index_video_document.reset_mock()

        video.save()
        mock_index_video_document.assert_called_once_with(video.pk)

    @mock.patch('greenday_core.signals.index_video_document')
    def test_delete_video_search_document(
            self, mock_index_video_document):
        """
            Video soft deleted
        """
        video = self.create_video(project=self.project)
        video_id = video.pk
        mock_index_video_document.reset_mock()

        video.delete()
        mock_index_video_document.assert_called_once_with(video_id)

    @mock.patch('greenday_core.signals.index_video_document')
    def test_delete_video_hard(
            self, mock_index_video_document):
        """
            Video hard deleted
        """
        video = self.create_video(project=self.project)
        video_id = video.pk
        mock_index_video_document.reset_mock()

        video.delete(trash=False)
        mock_index_video_document.assert_called_once_with(video_id)

        self.assertObjectAbsent(video)

        # the youtubevideo is not related to any other videos so should
        # be deleted
        self.assertObjectAbsent(video.youtube_video)

class VideoInstanceTagSignalsTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.models.tag.VideoTagInstance <greenday_core.models.tag.VideoTagInstance>` signals
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoInstanceTagSignalsTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.video = self.create_video(project=self.project)
        self.global_tag = milkman.deliver(GlobalTag)
        self.project_tag = ProjectTag.add_root(
            project=self.project, global_tag=self.global_tag
        )
        self.video_tag = VideoTag.objects.create(
            video=self.video,
            project_tag=self.project_tag,
            project=self.project
        )

    @mock.patch('greenday_core.signals.index_global_tag_document')
    @mock.patch('greenday_core.signals.index_video_document')
    def test_create_video_tag_instance_search_document(
            self, mock_index_video_document, mock_index_global_tag_document):
        """
            Create instance
        """
        VideoTagInstance.objects.create(
            video_tag=self.video_tag
        )
        mock_index_video_document.assert_called_once_with(self.video.pk)
        mock_index_global_tag_document.assert_called_once_with(
            self.global_tag.pk)

    @mock.patch('greenday_core.signals.index_global_tag_document')
    @mock.patch('greenday_core.signals.index_video_document')
    def test_delete_video_tag_instance_search_document(
            self, mock_index_video_document, mock_index_global_tag_document):
        """
            Update instance
        """
        video_tag_instance = VideoTagInstance.objects.create(
            video_tag=self.video_tag
        )
        mock_index_video_document.reset_mock()
        mock_index_global_tag_document.reset_mock()

        video_tag_instance.delete()
        mock_index_video_document.assert_called_once_with(self.video.pk)
        mock_index_global_tag_document.assert_called_once_with(
            self.global_tag.pk)


class TimedVideoCommentSignalsTestCase(BaseSignalsTestCase):
    """
        Tests for :class:`greenday_core.models.comment.TimedVideoComment <greenday_core.models.comment.TimedVideoComment>` signals
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(TimedVideoCommentSignalsTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.video = self.create_video(project=self.project)

    @mock.patch('greenday_core.signals.index_video_document')
    def test_create_root_comment_search_document(
            self, mock_index_video_document):
        """
            Create instance
        """
        root_comment = TimedVideoComment.add_root(
            video=self.video,
            user=self.admin,
            text='foo',
            start_seconds=0
        )
        mock_index_video_document.assert_called_once_with(self.video.pk)

    @mock.patch('greenday_core.signals.index_video_document')
    def test_delete_root_comment_search_document(
            self, mock_index_video_document):
        """
            Create instance
        """
        root_comment = TimedVideoComment.add_root(
            video=self.video,
            user=self.admin,
            text='foo',
            start_seconds=0
        )
        mock_index_video_document.reset_mock()

        root_comment.delete()
        mock_index_video_document.assert_called_once_with(self.video.pk)


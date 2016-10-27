"""
    Tests for :mod:`greenday_core.indexers <greenday_core.indexers>`
"""
import mock
from milkman.dairy import milkman
from search.indexes import Index

from django.contrib.auth import get_user_model

from .base import AppengineTestBed
from ..documents.project import ProjectDocument
from ..documents.tag import AutoCompleteTagDocument
from ..documents.user import AutoCompleteUserDocument
from ..documents.video import VideoDocument

from ..models import Project, GlobalTag, PendingUser
from ..indexers import (
    index_project_document,
    index_global_tag_document,
    index_auto_complete_user,
    index_video_document,

    index_all
)
from ..signal_utils import inhibit_signals


class BaseIndexerTestCase(AppengineTestBed):
    """
        Base test case for indexers
    """
    def setUp(self):
        """
            Disconnects all Django signals and sets up a test user
        """
        super(BaseIndexerTestCase, self).setUp()
        self.inhibit_signals_ctx = inhibit_signals(None)
        self.inhibit_signals_ctx.disconnect_signals()

        self.admin = milkman.deliver(
            get_user_model(),
            email="admin@example.com",
            is_superuser=True,
            is_googler=True)

    def tearDown(self):
        """
            Reconnects Django signals
        """
        self.inhibit_signals_ctx.reconnect_signals()


class ProjectIndexerTestCase(BaseIndexerTestCase):
    """
        Tests for :func:`greenday_core.indexers.index_project_document <greenday_core.indexers.index_project_document>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectIndexerTestCase, self).setUp()

        self.project = milkman.deliver(Project, name='foo')
        self.project.set_owner(self.admin)

    def test_index_project(self):
        """
            Index a project
        """
        index_project_document(self.project.pk)

        docs = Index(name='projects').search(
            ProjectDocument, ids_only=False).keywords(self.project.name)
        self.assertEqual(1, len(docs))
        self.assertEqual(docs[0].id, unicode(self.project.pk))

    def test_index_deleted_project(self):
        """
            Index a project that doesn't exist
        """
        # get project into index
        index_project_document(self.project.pk)

        self.project.delete()
        index_project_document(self.project.pk)

        # make sure project is removed from index
        docs = Index(name='projects').search(
            ProjectDocument, ids_only=False).keywords(self.project.name)
        self.assertEqual(0, len(docs))


class GlobalTagIndexerTestCase(BaseIndexerTestCase):
    """
        Tests for :func:`greenday_core.indexers.index_global_tag_document <greenday_core.indexers.index_global_tag_document>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(GlobalTagIndexerTestCase, self).setUp()

        self.global_tag = milkman.deliver(GlobalTag, name='foo')

    def test_index_global_tag(self):
        """
            Index a tag
        """
        index_global_tag_document(self.global_tag.pk)

        docs = (
            Index(name='tags')
            .search(AutoCompleteTagDocument, ids_only=False)
            .keywords(self.global_tag.name)
        )
        self.assertEqual(1, len(docs))
        self.assertEqual(docs[0].id, unicode(self.global_tag.pk))

    def test_deleted_global_tag(self):
        """
            Index a tag that doesn't exist
        """
        index_global_tag_document(self.global_tag.pk)

        self.global_tag.delete()
        index_global_tag_document(self.global_tag.pk)

        # make sure project is removed from index
        docs = (
            Index(name='tags')
            .search(AutoCompleteTagDocument, ids_only=False)
            .keywords(self.global_tag.name)
        )
        self.assertEqual(0, len(docs))


class AutoCompleteUserIndexer(BaseIndexerTestCase):
    """
        Tests for :func:`greenday_core.indexers.index_auto_complete_user <greenday_core.indexers.index_auto_complete_user>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(AutoCompleteUserIndexer, self).setUp()

        self.admin_user_kw = 'admin'
        self.pendinguser_kw = 'foo'
        self.pendinguser = PendingUser.objects.create(
            email="{0}@example.com".format(self.pendinguser_kw))

    def test_index_user(self):
        """
            Index a user
        """
        index_auto_complete_user(self.admin.email)

        docs = (
            Index(name='autocomplete_users')
            .search(AutoCompleteUserDocument, ids_only=False)
            .keywords(self.admin_user_kw)
        )
        self.assertEqual(1, len(docs))
        self.assertEqual(docs[0].user_id, str(self.admin.pk))

    def test_index_pending_user(self):
        """
            Index a pending user
        """
        index_auto_complete_user(self.pendinguser.email)

        docs = (
            Index(name='autocomplete_users')
            .search(AutoCompleteUserDocument, ids_only=False)
            .keywords(self.pendinguser_kw)
        )
        self.assertEqual(1, len(docs))
        self.assertEqual(docs[0].pending_user_id, str(self.pendinguser.pk))

    def test_index_user_with_pending_user(self):
        """
            Index a user where a pending user has already been indexed for this
            email
        """
        # index the pending user first
        index_auto_complete_user(self.pendinguser.email)

        proper_user = get_user_model().objects.create(
            email=self.pendinguser.email)
        # index the proper user - it should replace the document
        index_auto_complete_user(proper_user.email)

        docs = (
            Index(name='autocomplete_users')
            .search(AutoCompleteUserDocument, ids_only=False)
            .keywords(self.pendinguser_kw)
        )
        self.assertEqual(1, len(docs))
        self.assertEqual(docs[0].user_id, str(proper_user.pk))
        self.assertFalse(docs[0].pending_user_id)

    def test_index_pending_user_with_user(self):
        """
            Index a pending user where a user has already been indexed for
            this email
        """
        # index the proper user first
        index_auto_complete_user(self.admin.email)

        new_pending_user = PendingUser.objects.create(
            email=self.admin.email)

        # index the new pending user - it should not replace the existing index
        index_auto_complete_user(new_pending_user.email)

        docs = (
            Index(name='autocomplete_users')
            .search(AutoCompleteUserDocument, ids_only=False)
            .keywords(self.admin_user_kw)
        )
        self.assertEqual(1, len(docs))
        self.assertEqual(docs[0].user_id, str(self.admin.pk))
        self.assertFalse(docs[0].pending_user_id)

    def test_delete_user(self):
        """
            Index a deleted user
        """
        index_auto_complete_user(self.admin.email)

        self.admin.delete()
        index_auto_complete_user(self.admin.email)

        docs = (
            Index(name='autocomplete_users')
            .search(AutoCompleteUserDocument, ids_only=False)
            .keywords(self.admin_user_kw)
        )
        self.assertEqual(0, len(docs))

    def test_delete_pending_user(self):
        """
            Index a deleted pending user
        """
        index_auto_complete_user(self.pendinguser.email)

        self.pendinguser.delete()
        index_auto_complete_user(self.pendinguser.email)

        docs = (
            Index(name='autocomplete_users')
            .search(AutoCompleteUserDocument, ids_only=False)
            .keywords(self.pendinguser_kw)
        )
        self.assertEqual(0, len(docs))

    def test_delete_pending_user_with_user(self):
        """
            Index a deleted pending user where a user object still
            exists
        """
        new_pending_user = PendingUser.objects.create(
            email=self.admin.email)

        index_auto_complete_user(self.admin.email)

        new_pending_user.delete()

        docs = (
            Index(name='autocomplete_users')
            .search(AutoCompleteUserDocument, ids_only=False)
            .keywords(self.admin_user_kw)
        )
        self.assertEqual(1, len(docs))
        self.assertEqual(docs[0].user_id, str(self.admin.pk))
        self.assertFalse(docs[0].pending_user_id)


class VideoIndexerTestCase(BaseIndexerTestCase):
    """
        Tests for :func:`greenday_core.indexers.index_video_document <greenday_core.indexers.index_video_document>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoIndexerTestCase, self).setUp()

        self.project = milkman.deliver(Project, name='foo')
        self.project.set_owner(self.admin)

        self.video = self.create_video(
            name='bar', latitude="3.14", longitude="6.28")

    def test_index_video(self):
        """
            Index a video
        """
        index_video_document(self.video.pk)

        docs = Index(name='videos').search(
            VideoDocument).keywords(self.video.youtube_video.name)
        self.assertEqual(1, len(docs))
        self.assertEqual(docs[0].id, unicode(self.video.pk))

    def test_index_deleted_video(self):
        """
            Index a deleted video
        """
        index_video_document(self.video.pk)

        self.video.delete()

        index_video_document(self.video.pk)
        docs = Index(name='videos').search(
            VideoDocument).keywords(self.video.youtube_video.name)
        self.assertEqual(0, len(docs))


class IndexAllTestCase(BaseIndexerTestCase):
    """
        Tests for :func:`greenday_core.indexers.index_all <greenday_core.indexers.index_all>`
    """
    @mock.patch("greenday_core.indexers.index_project_document")
    def test_index_single_object(self, mock_index_project_document):
        """
            Index single project ID
        """
        project = milkman.deliver(Project)

        index_all(Project, object_ids=project.pk)
        mock_index_project_document.assert_called_once_with(str(project.pk))

    @mock.patch("greenday_core.indexers.index_project_document")
    def test_index_all_of_model(self, mock_index_project_document):
        """
            Index all projects
        """
        project = milkman.deliver(Project)
        project_2 = milkman.deliver(Project)

        index_all(Project)
        mock_index_project_document.assert_any_call(str(project.pk))
        mock_index_project_document.assert_any_call(str(project_2.pk))

    @mock.patch("greenday_core.indexers.index_project_document")
    def test_index_all_of_model_string(self, mock_index_project_document):
        """
            Index all projects by passing "Project" as string
        """
        project = milkman.deliver(Project)
        project_2 = milkman.deliver(Project)

        index_all("Project")
        mock_index_project_document.assert_any_call(str(project.pk))
        mock_index_project_document.assert_any_call(str(project_2.pk))

    def test_index_all(self):
        """
            Index all model types
        """
        project = milkman.deliver(Project)
        video = self.create_video(project=project)
        global_tag = milkman.deliver(GlobalTag, created_from_project=project)
        pendinguser = milkman.deliver(
            PendingUser, email="pending@example.com")

        with mock.patch(
            "greenday_core.indexers.index_project_document") as mk_project,\
                mock.patch(
                    "greenday_core.indexers.index_video_document") as mk_video,\
                mock.patch(
                    "greenday_core.indexers.index_global_tag_document") as mk_globaltag,\
                mock.patch(
                    "greenday_core.indexers.index_auto_complete_user"
                    ) as mk_user:
            index_all()

        mk_project.assert_called_once_with(str(project.pk))
        mk_video.assert_called_once_with(str(video.pk))
        mk_globaltag.assert_called_once_with(str(global_tag.pk))
        mk_user.assert_any_call(pendinguser.email)
        mk_user.assert_any_call(self.admin.email)

    @mock.patch("greenday_core.indexers.index_auto_complete_user")
    def test_index_user(self, mock_index_auto_complete_user):
        """
            Index a user
        """
        index_all(get_user_model(), self.admin.pk)
        mock_index_auto_complete_user.assert_called_once_with(self.admin.email)

    @mock.patch("greenday_core.indexers.index_auto_complete_user")
    def test_index_pending_user(self, mock_index_auto_complete_user):
        """
            Index a pending user
        """
        pending_user = milkman.deliver(PendingUser)

        index_all(PendingUser, pending_user.pk)
        mock_index_auto_complete_user.assert_called_once_with(
            pending_user.email)

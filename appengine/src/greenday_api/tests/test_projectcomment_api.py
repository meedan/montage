"""
    Tests for :mod:`greenday_api.projectcomment.projectcomment_api <greenday_api.projectcomment.projectcomment_api>`
"""
import datetime
from milkman.dairy import milkman

from greenday_core.api_exceptions import (
    BadRequestException, ForbiddenException, NotFoundException)
from greenday_core.constants import EventKind
from greenday_core.models import (
    Project, ProjectComment, TimedVideoComment
)

from .base import ApiTestCase, TestEventBusMixin

from ..projectcomment.projectcomment_api import ProjectCommentAPI
from ..projectcomment.containers import (
    ProjectCommentListContainer,
    ProjectCommentEntityContainer,
    CreateProjectRootCommentContainer,
    CreateProjectCommentReplyContainer,
    UpdateProjectCommentContainer,
    UpdateProjectCommentReplyContainer,
    ProjectCommentReplyEntityContainer
)


class ProjectCommentAPIListTestCase(ApiTestCase, TestEventBusMixin):
    """
        Test case for
        :func:`greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.list_comments <greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.list_comments>`
    """
    api_type = ProjectCommentAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectCommentAPIListTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.project_2 = milkman.deliver(Project)

        # create root comments
        self.root_comments = [
            ProjectComment.add_root(
                project=self.project,
                user=self.user,
                text="foo{0}".format(i),
                created=datetime.datetime(2014, 1, 1, i, i, i))
            for i in range(1, 6)
        ]

        self.other_comments = [
            ProjectComment.add_root(
                project=self.project_2,
                user=self.user,
                text="bar{0}".format(i))
            for i in range(0, 5)
        ]

    def test_list_comments(self):
        """
            List project comments
        """
        self._sign_in(self.user)

        self.replies = [
            self.root_comments[0].add_reply("baz{0}".format(i), self.admin)
            for i in range(0, 5)
        ]

        request = ProjectCommentListContainer.combined_message_class(
            project_id=self.project.pk)

        with self.assertNumQueries(5):
            response = self.api.list_comments(request)

        self.assertEqual(len(self.root_comments), len(response.items))

        first_comment_obj = self.root_comments[0]
        reply_comment_obj = self.replies[0]

        first_comment = response.items[0]
        self.assertEqual(first_comment_obj.text, first_comment.text)
        self.assertEqual(first_comment_obj.user_id, first_comment.user.id)
        self.assertEqual(first_comment_obj.project_id, self.project.pk)
        self.assertTrue(first_comment_obj.modified)
        self.assertEqual(5, len(first_comment.replies))
        self.assertEqual(
            reply_comment_obj.text, first_comment.replies[0].text)
        self.assertTrue(first_comment.replies[0].modified)
        self.assertEqual(
            reply_comment_obj.user_id, first_comment.replies[0].user.id)
        self.assertEqual(
            reply_comment_obj.project_id, self.project.pk)

    def test_list_comments_with_video_comments(self):
        """
            Aggregated feed of project comments and video comments
        """
        video = self.create_video(project=self.project)

        video_comments = [
            TimedVideoComment.add_root(
                video=video,
                user=self.user,
                text="vid foo{0}".format(i),
                start_seconds=i)
            for i in range(0, 5)
        ]

        first_video_comment_obj = video_comments[0]
        video_reply = first_video_comment_obj.add_reply("vid baz", self.admin)

        self._sign_in(self.user)

        request = ProjectCommentListContainer.combined_message_class(
            project_id=self.project.pk, show_video_comments=True)

        with self.assertNumQueries(8):
            response = self.api.list_comments(request)

        self.assertEqual(len(self.root_comments), len(response.items))
        self.assertEqual(len(video_comments), len(response.video_comments))

        first_video_comment = next(
            c for c in response.video_comments
            if c.id == first_video_comment_obj.pk)

        self.assertEqual(
            first_video_comment_obj.text, first_video_comment.text)
        self.assertEqual(
            first_video_comment_obj.start_seconds,
            first_video_comment.start_seconds)
        self.assertEqual(
            first_video_comment_obj.user_id, first_video_comment.user.id)
        self.assertEqual(1, len(first_video_comment.replies))

        self.assertEqual(video_reply.text, first_video_comment.replies[0].text)
        self.assertEqual(
            video_reply.user_id, first_video_comment.replies[0].user.id)

    def test_list_comments_since(self):
        """
            All comments created after x
        """
        video = self.create_video(project=self.project)

        video_comments = [
            TimedVideoComment.add_root(
                video=video,
                user=self.user,
                text="vid foo{0}".format(i),
                start_seconds=i,
                created=datetime.datetime(2014, 1, 1, i, i, i))
            for i in range(1, 6)
        ]

        video_comments[0].add_reply("vid baz", self.admin)

        self._sign_in(self.user)

        request = ProjectCommentListContainer.combined_message_class(
            project_id=self.project.pk,
            show_video_comments=True,
            since=datetime.datetime(2014, 1, 1, 3, 3, 3))

        with self.assertNumQueries(8):
            response = self.api.list_comments(request)

        self.assertEqual(3, len(response.items))
        self.assertEqual(4, len(response.video_comments))

        self.assertEqual(self.root_comments[-1].pk, response.items[0].id)

        # oldest video has a recent reply on it so should come first
        self.assertEqual(video_comments[0].pk, response.video_comments[0].id)
        self.assertEqual(video_comments[-1].pk, response.video_comments[1].id)


class ProjectCommentAPIGetTestCase(ApiTestCase, TestEventBusMixin):
    """
        Test case for
        :func:`greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.get_comment <greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.get_comment>`
    """
    api_type = ProjectCommentAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectCommentAPIGetTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.project.add_assigned(self.user, pending=False)

        self.root_comment = ProjectComment.add_root(
            project=self.project, user=self.user, text="foo")

        self.replies = [
            self.root_comment.add_reply("baz{0}".format(i), self.admin)
            for i in range(0, 5)
        ]

    def test_get_comments(self):
        """
            Get a single project comment thread
        """
        self._sign_in(self.user)

        request = ProjectCommentEntityContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk)

        with self.assertNumQueries(5):
            response = self.api.get_comment(request)

        self.assertEqual(self.root_comment.text, response.text)
        self.assertEqual(self.root_comment.user_id, response.user.id)
        self.assertEqual(self.root_comment.project_id, self.project.pk)
        self.assertTrue(response.modified)
        self.assertEqual(5, len(response.replies))
        self.assertEqual(
            self.replies[0].text, response.replies[0].text)
        self.assertEqual(
            self.replies[0].user_id, response.replies[0].user.id)


class ProjectCommentAPICreateTestCase(ApiTestCase, TestEventBusMixin):
    """
        Test case for
        :func:`greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.create_root_comment <greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.create_root_comment>`
    """
    api_type = ProjectCommentAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectCommentAPICreateTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

    def test_ok(self):
        """
            Create a new comment thread
        """
        self._sign_in(self.admin)

        request = CreateProjectRootCommentContainer.combined_message_class(
            project_id=self.project.pk,
            text="foo")

        with self.assertEventRecorded(
                EventKind.PROJECTROOTCOMMENTCREATED,
                object_id=True,
                project_id=self.project.pk), self.assertNumQueries(9):
            response = self.api.create_root_comment(request)

        comment = ProjectComment.objects.get(pk=response.id)

        self.assertEqual(self.admin.pk, comment.user.pk)
        self.assertEqual(request.text, comment.text)

    def test_no_auth(self):
        """
            User not assigned to project creates comment thread
        """
        self._sign_in(self.user2)

        request = CreateProjectRootCommentContainer.combined_message_class(
            project_id=self.project.pk,
            text="foo")

        self.assertRaises(
            ForbiddenException,
            self.api.create_root_comment,
            request)

    def test_404(self):
        """
            Create comment on non-existant project
        """
        self._sign_in(self.admin)

        request = CreateProjectRootCommentContainer.combined_message_class(
            project_id=999,
            text="foo")

        self.assertRaises(
            NotFoundException,
            self.api.create_root_comment,
            request)


class ProjectCommentAPIAddReplyTestCase(ApiTestCase, TestEventBusMixin):
    """
        Test case for
        :func:`greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.create_comment_reply <greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.create_comment_reply>`
    """
    api_type = ProjectCommentAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectCommentAPIAddReplyTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

        self.root_comment = ProjectComment.add_root(
            project=self.project, user=self.admin, text="foo")

    def test_ok(self):
        """
            Create a reply on a comment thread
        """
        self._sign_in(self.admin)

        request = CreateProjectCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.id,
            text="foobar")

        with self.assertEventRecorded(
                EventKind.PROJECTREPLYCOMMENTCREATED,
                object_id=True,
                project_id=self.project.pk,
                meta=str(self.root_comment.id)), self.assertNumQueries(9):
            response = self.api.create_comment_reply(request)

        reply = self.reload(self.root_comment).get_replies()[0]
        self.assertEqual(self.admin.pk, reply.user.pk)
        self.assertEqual(request.text, reply.text)

        self.assertEqual(reply.text, response.text)
        self.assertEqual(reply.user_id, response.user.id)
        self.assertEqual(reply.project_id, self.project.pk)
        self.assertEqual(self.root_comment.pk, response.thread_id)

    def test_reply_to_reply_fail(self):
        """
            Reply to a reply rather than a root comment
        """
        self._sign_in(self.admin)

        reply = self.root_comment.add_reply("baz", self.admin)

        request = CreateProjectCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=reply.id,
            text="foobar")

        self.assertRaises(
            BadRequestException,
            self.api.create_comment_reply,
            request
        )

    def test_no_auth(self):
        """
            User not assigned to project creates a reply
        """
        self._sign_in(self.user2)

        request = CreateProjectCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.id,
            text="foo")

        self.assertRaises(
            ForbiddenException,
            self.api.create_comment_reply,
            request)

    def test_404(self):
        """
            Create reply on non-existant comment thread

            Create reply on non-existant project
        """
        self._sign_in(self.admin)

        request = CreateProjectCommentReplyContainer.combined_message_class(
            project_id=999,
            comment_id=self.root_comment.id,
            text="foo")

        self.assertRaises(
            NotFoundException,
            self.api.create_comment_reply,
            request)

        request = CreateProjectCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=999,
            text="foo")

        self.assertRaises(
            NotFoundException,
            self.api.create_comment_reply,
            request)


class ProjectCommentAPIUpdateTestCase(ApiTestCase, TestEventBusMixin):
    """
        Test case for
        :func:`greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.update_comment <greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.update_comment>`
    """
    api_type = ProjectCommentAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectCommentAPIUpdateTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

        self.root_comment = ProjectComment.add_root(
            project=self.project, user=self.admin, text="foo")

    def test_ok(self):
        """
            Update a root comment
        """
        self._sign_in(self.admin)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk,
            text="bar")

        with self.assertEventRecorded(
                EventKind.PROJECTCOMMENTUPDATED,
                object_id=self.root_comment.pk,
                project_id=self.project.pk), self.assertNumQueries(8):
            self.api.update_comment(request)

        self.root_comment = self.reload(self.root_comment)
        self.assertEqual(request.text, self.root_comment.text)

    def test_update_reply_ok(self):
        """
            Update a comment reply
        """
        self._sign_in(self.admin)

        reply = self.root_comment.add_reply("baz", self.admin)

        request = UpdateProjectCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk,
            reply_id=reply.pk,
            text="bar"
        )

        with self.assertEventRecorded(
                EventKind.PROJECTREPLYCOMMENTUPDATED,
                object_id=reply.pk,
                project_id=self.project.pk,
                meta=str(self.root_comment.pk)), self.assertNumQueries(9):
            response = self.api.update_reply(request)

        reply = self.reload(reply)

        self.assertEqual(request.text, reply.text)

    def test_404(self):
        """
            Update non-existant root comment

            Update comment on non-existant project
        """
        self._sign_in(self.admin)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=999,
            comment_id=self.root_comment.pk,
            text="bar")

        self.assertRaises(
            NotFoundException,
            self.api.update_comment,
            request)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=999,
            text="bar")

        self.assertRaises(
            NotFoundException,
            self.api.update_comment,
            request)

    def test_no_auth_on_project(self):
        """
            User not assigned to project updates comment
        """
        self._sign_in(self.user2)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk,
            text="bar")

        self.assertRaises(
            ForbiddenException,
            self.api.update_comment,
            request)

    def test_no_auth_not_comment_owner(self):
        """
            User updates a comment that they did not create
        """
        self.project.add_assigned(self.user, pending=False)
        self._sign_in(self.user)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk,
            text="bar")

        self.assertRaises(
            ForbiddenException,
            self.api.update_comment,
            request)


class ProjectCommentAPIPatchTestCase(ApiTestCase, TestEventBusMixin):
    """
        Test case for
        :func:`greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.patch_comment <greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.patch_comment>`
    """
    api_type = ProjectCommentAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectCommentAPIPatchTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

        self.root_comment = ProjectComment.add_root(
            project=self.project, user=self.admin, text="foo")

    def test_ok(self):
        """
            Patch a comment
        """
        self._sign_in(self.admin)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk,
            text="bar")

        with self.assertEventRecorded(
                EventKind.PROJECTCOMMENTUPDATED,
                object_id=self.root_comment.pk,
                project_id=self.project.pk), self.assertNumQueries(8):
            self.api.patch_comment(request)

        self.root_comment = self.reload(self.root_comment)
        self.assertEqual(request.text, self.root_comment.text)

    def test_update_reply_ok(self):
        """
            Patch a comment reply
        """
        self._sign_in(self.admin)

        reply = self.root_comment.add_reply("baz", self.admin)

        request = UpdateProjectCommentReplyContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk,
            reply_id=reply.pk,
            text="bar"
        )

        with self.assertEventRecorded(
                EventKind.PROJECTREPLYCOMMENTUPDATED,
                object_id=reply.pk,
                project_id=self.project.pk,
                meta=str(self.root_comment.pk)), self.assertNumQueries(9):
            response = self.api.patch_reply(request)

        reply = self.reload(reply)
        self.assertEqual(request.text, reply.text)

    def test_no_text(self):
        """
            Patch a comment without passing a value for the 'text' field
        """
        self._sign_in(self.admin)

        initial_text = self.root_comment.text

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk)

        with self.assertNumQueries(6):
            self.api.patch_comment(request)

        self.root_comment = self.reload(self.root_comment)
        self.assertEqual(initial_text, self.root_comment.text)

    def test_404(self):
        """
            Patch non-existant root comment

            Patch comment on non-existant project
        """
        self._sign_in(self.admin)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=999,
            comment_id=self.root_comment.pk,
            text="bar")

        self.assertRaises(
            NotFoundException,
            self.api.patch_comment,
            request)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=999,
            text="bar")

        self.assertRaises(
            NotFoundException,
            self.api.patch_comment,
            request)

    def test_no_auth_on_project(self):
        """
            User not assigned to project patches comment
        """
        self._sign_in(self.user2)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk,
            text="bar")

        self.assertRaises(
            ForbiddenException,
            self.api.patch_comment,
            request)

    def test_no_auth_not_comment_owner(self):
        """
            User patches comment that they did not create
        """
        self.project.add_assigned(self.user, pending=False)
        self._sign_in(self.user)

        request = UpdateProjectCommentContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk,
            text="bar")

        self.assertRaises(
            ForbiddenException,
            self.api.patch_comment,
            request)


class ProjectCommentAPIDeleteTestCase(ApiTestCase, TestEventBusMixin):
    """
        Test case for
        :func:`greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.delete_comment <greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.delete_comment>`
        and :func:`greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.delete_reply <greenday_api.projectcomment.projectcomment_api.ProjectCommentAPI.delete_reply>`
    """
    api_type = ProjectCommentAPI

    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectCommentAPIDeleteTestCase, self).setUp()
        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

        self.root_comment = ProjectComment.add_root(
            project=self.project, user=self.admin, text="foo")

    def test_ok(self):
        """
            Delete a comment thread
        """
        self._sign_in(self.admin)

        # We're testing the deletion of replies here. It really makes no
        # difference whether it's a root or a reply. We have two separate
        # endpoints for the FE to have a restful API
        reply1 = self.root_comment.add_reply("baz", self.admin)
        reply2 = self.root_comment.add_reply("boo", self.user)

        request = ProjectCommentEntityContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=reply1.pk)

        with self.assertEventRecorded(
                EventKind.PROJECTCOMMENTDELETED,
                object_id=reply1.pk,
                project_id=self.project.pk), self.assertNumQueries(11):
            self.api.delete_comment(request)

        self.assertObjectAbsent(reply1)
        self.assertTrue(self.reload(self.root_comment))
        self.assertTrue(self.reload(reply2))

    def test_delete_reply(self):
        """
            Delete a single reply
        """
        self._sign_in(self.admin)

        reply1 = self.root_comment.add_reply("baz", self.admin)
        reply2 = self.root_comment.add_reply("boo", self.user)

        request = ProjectCommentReplyEntityContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk,
            reply_id=reply1.pk)

        with self.assertEventRecorded(
                EventKind.PROJECTREPLYCOMMENTDELETED,
                object_id=reply1.pk,
                project_id=self.project.pk,
                meta=str(self.root_comment.pk)), self.assertNumQueries(11):
            self.api.delete_reply(request)

        self.assertObjectAbsent(reply1)
        self.assertTrue(self.reload(self.root_comment))
        self.assertTrue(self.reload(reply2))

    def test_no_auth(self):
        """
            User not assigned to project deletes a comment thread
        """
        self._sign_in(self.user2)

        request = ProjectCommentEntityContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=self.root_comment.pk)

        self.assertRaises(
            ForbiddenException,
            self.api.delete_comment,
            request)

    def test_404(self):
        """
            Delete a comment on a non-existant project

            Delte a non-existant comment
        """
        self._sign_in(self.admin)

        request = ProjectCommentEntityContainer.combined_message_class(
            project_id=999,
            comment_id=self.root_comment.pk)

        self.assertRaises(
            NotFoundException,
            self.api.delete_comment,
            request)

        request = ProjectCommentEntityContainer.combined_message_class(
            project_id=self.project.pk,
            comment_id=999)

        self.assertRaises(
            NotFoundException,
            self.api.delete_comment,
            request)

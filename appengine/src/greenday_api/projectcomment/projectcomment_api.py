"""
    Defines the project comment API
"""
from collections import defaultdict
import endpoints
from protorpc import message_types

from greenday_core.api_exceptions import (
    BadRequestException, NotFoundException, ForbiddenException)
from greenday_core.constants import EventKind
from greenday_core.models import ProjectComment, TimedVideoComment

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required
)
from ..project.mixins import ProjectAPIMixin
from ..utils import get_obj_or_api_404, api_appevent

from ..comment.mappers import CommentFullMapper, CommentMapper
from ..comment.messages import (
    CommentResponseMessage,
    CommentResponseMessageSlim,
)

from ..videocomment.messages import (
    VideoCommentResponseMessageSlim, VideoCommentResponseMessage
)
from .containers import (
    ProjectCommentListContainer,
    ProjectCommentEntityContainer,
    CreateProjectRootCommentContainer,
    CreateProjectCommentReplyContainer,
    UpdateProjectCommentContainer,
    UpdateProjectCommentReplyContainer,
    ProjectCommentReplyEntityContainer
)
from .messages import ProjectCommentListResponse


@greenday_api.api_class(
    resource_name='project_comments', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class ProjectCommentAPI(BaseAPI, ProjectAPIMixin):
    """
        API to handle comments on projects

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        """
            Creates the project comment API
        """
        super(ProjectCommentAPI, self).__init__(*args, **kwargs)
        self.slim_mapper = CommentMapper(CommentResponseMessageSlim)
        self.mapper = CommentFullMapper(
            CommentResponseMessage)

        self.videocomment_slim_mapper = CommentMapper(
            VideoCommentResponseMessageSlim)
        self.videocomment_mapper = CommentFullMapper(
            VideoCommentResponseMessage,
            slim_mapper=self.videocomment_slim_mapper,
            reverse_order=True)

    @greenday_method(
        ProjectCommentListContainer, ProjectCommentListResponse,
        path='project/{project_id}/comments',
        http_method='GET', name='list_comments',
        pre_middlewares=[auth_required])
    def list_comments(self, request):
        """
            Gets all comments on a project

            This end point is designed to be used as an aggregated comment feed
        """
        project = self.get_project(request.project_id, assigned_only=True)

        comments = get_all_comments(
            ProjectComment.objects,
            since=request.since,
            filter_args={"tagged_object_id": request.project_id})

        if request.show_video_comments:
            video_comments = get_all_comments(
                TimedVideoComment.objects
                    .prefetch_related("tagged_content_object"),
                since=request.since,
                filter_args={"project": project})
        else:
            video_comments = []

        return ProjectCommentListResponse(
            items=map(self.mapper.map, comments),
            video_comments=map(self.videocomment_mapper.map, video_comments),
            is_list=True)

    @greenday_method(
        ProjectCommentEntityContainer, CommentResponseMessage,
        path='project/{project_id}/comments/{comment_id}',
        http_method='GET', name='get_comments',
        pre_middlewares=[auth_required])
    def get_comment(self, request):
        """
            Gets a root level comment on a project
        """
        self.get_project(request.project_id, assigned_only=True)

        comment = get_obj_or_api_404(
            ProjectComment.objects.select_related('user'),
            tagged_object_id=request.project_id,
            pk=request.comment_id)

        return self.mapper.map(comment)

    @greenday_method(
        CreateProjectRootCommentContainer, CommentResponseMessage,
        path='project/{project_id}/comments',
        http_method='POST', name='create_root_comment',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTROOTCOMMENTCREATED,
        id_getter_post=lambda s, req, res: res.id,
        project_id_getter=lambda s, req: req.project_id)
    def create_root_comment(self, request):
        """
            Creates a new root level comment on the project
        """
        project = self.get_project(request.project_id, assigned_only=True)

        comment = ProjectComment.add_root(
            project=project,
            text=request.text,
            user=self.current_user)

        return self.mapper.map(comment)

    @greenday_method(
        CreateProjectCommentReplyContainer, CommentResponseMessageSlim,
        path='project/{project_id}/comments/{comment_id}/replies',
        http_method='POST', name='create_reply',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTREPLYCOMMENTCREATED,
        id_getter_post=lambda s, req, res: res.id,
        project_id_getter=lambda s, req: req.project_id,
        meta_getter=lambda s, req: req.comment_id)
    def create_comment_reply(self, request):
        """
            Creates a reply to a root comment
        """
        project = self.get_project(request.project_id, assigned_only=True)

        comment = get_obj_or_api_404(ProjectComment, pk=request.comment_id)

        if comment.project_id != request.project_id:
            raise NotFoundException

        if not comment.is_root():
            raise BadRequestException(
                "Replies can only be added to root comments")

        reply = comment.add_reply(
            request.text,
            self.current_user)

        return self.slim_mapper.map(reply)

    @greenday_method(
        UpdateProjectCommentContainer, CommentResponseMessage,
        path='project/{project_id}/comments/{comment_id}',
        http_method='PUT', name='update_comment',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTCOMMENTUPDATED,
        id_getter=lambda s, req: req.comment_id,
        project_id_getter=lambda s, req: req.project_id)
    def update_comment(self, request):
        """
            Updates any project comment
        """
        project = self.get_project(request.project_id, assigned_only=True)

        comment = get_obj_or_api_404(
            ProjectComment,
            tagged_object_id=request.project_id,
            pk=request.comment_id)

        if (self.current_user != comment.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        comment.text = request.text
        comment.save()

        return self.mapper.map(comment)

    @greenday_method(
        UpdateProjectCommentReplyContainer, CommentResponseMessage,
        path='project/{project_id}/comments/{comment_id}/replies/{reply_id}',
        http_method='PUT', name='update_reply',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTREPLYCOMMENTUPDATED,
        id_getter=lambda s, req: req.reply_id,
        project_id_getter=lambda s, req: req.project_id,
        meta_getter=lambda s, req: req.comment_id)
    def update_reply(self, request):
        """
            Updates any project comment reply
        """
        project = self.get_project(request.project_id, assigned_only=True)

        reply = get_obj_or_api_404(
            ProjectComment,
            tagged_object_id=project.pk,
            pk=request.reply_id)

        if (self.current_user != reply.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        reply.text = request.text
        reply.save()

        return self.mapper.map(reply)

    @greenday_method(
        UpdateProjectCommentContainer, CommentResponseMessage,
        path='project/{project_id}/comments/{comment_id}',
        http_method='PATCH', name='patch_comment',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTCOMMENTUPDATED,
        id_getter=lambda s, req: req.comment_id,
        project_id_getter=lambda s, req: req.project_id)
    def patch_comment(self, request):
        """
            Patches any project comment
        """
        project = self.get_project(request.project_id, assigned_only=True)

        comment = get_obj_or_api_404(
            ProjectComment,
            tagged_object_id=request.project_id,
            pk=request.comment_id)

        if (self.current_user != comment.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        if request.text is not None:
            comment.text = request.text
            comment.save()

        return self.mapper.map(comment)

    @greenday_method(
        UpdateProjectCommentReplyContainer, CommentResponseMessage,
        path='project/{project_id}/comments/{comment_id}/replies/{reply_id}',
        http_method='PATCH', name='patch_reply',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTREPLYCOMMENTUPDATED,
        id_getter=lambda s, req: req.reply_id,
        project_id_getter=lambda s, req: req.project_id,
        meta_getter=lambda s, req: req.comment_id)
    def patch_reply(self, request):
        """
            Patches any project comment reply
        """
        project = self.get_project(request.project_id, assigned_only=True)

        reply = get_obj_or_api_404(
            ProjectComment,
            tagged_object_id=project.pk,
            pk=request.reply_id)

        if (self.current_user != reply.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        if request.text is not None:
            reply.text = request.text
            reply.save()

        return self.mapper.map(reply)

    @greenday_method(
        ProjectCommentEntityContainer, message_types.VoidMessage,
        path='project/{project_id}/comments/{comment_id}',
        http_method='DELETE', name='delete_comment',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTCOMMENTDELETED,
        id_getter=lambda s, req: req.comment_id,
        project_id_getter=lambda s, req: req.project_id)
    def delete_comment(self, request):
        """
            Deletes a comment. Can be a root comment or a reply.
        """
        self.get_project(request.project_id, assigned_only=True)

        comment = get_obj_or_api_404(
            ProjectComment.objects.select_related('user'),
            tagged_object_id=request.project_id,
            pk=request.comment_id)

        if (self.current_user != comment.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        comment.delete()

        return message_types.VoidMessage()

    @greenday_method(
        ProjectCommentReplyEntityContainer, message_types.VoidMessage,
        path='project/{project_id}/comments/{comment_id}/replies/{reply_id}',
        http_method='DELETE', name='delete_reply',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTREPLYCOMMENTDELETED,
        id_getter=lambda s, req: req.reply_id,
        project_id_getter=lambda s, req: req.project_id,
        meta_getter=lambda s, req: req.comment_id)
    def delete_reply(self, request):
        """
            Deletes a comment. Can be a root comment or a reply.
        """
        self.get_project(request.project_id, assigned_only=True)

        reply = get_obj_or_api_404(
            ProjectComment.objects.select_related('user'),
            tagged_object_id=request.project_id,
            pk=request.reply_id)

        if (self.current_user != reply.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        reply.delete()

        return message_types.VoidMessage()


def get_all_comments(qs, since=None, filter_args=None):
    """
        Gets all comment trees with any comments within the tree having been
        created after the `since` date or matching filter_args
    """

    tree_qs = (
        qs
        .filter(**filter_args)
        .order_by('-created')
    )

    if since:
        tree_qs = tree_qs.filter(created__gte=since)

    comment_tree_ids = set(
        tree_qs
        .values_list('tree_id', flat=True)
    )

    root_comments = {}
    replies = defaultdict(list)

    for comment in (
            qs
            .filter(tree_id__in=comment_tree_ids)
            .select_related('user')
            .prefill_parent_cache()):
        if comment.is_root():
            root_comments[comment.tree_id] = comment
        else:
            replies[comment.tree_id].append(comment)

    for tree_id, comment in root_comments.items():
        comment._reply_cache = replies.get(tree_id, ())

    return sorted(
        root_comments.values(),
        key=lambda o: max([o.created] + [
            reply.created for reply in o._reply_cache]),
        reverse=True)

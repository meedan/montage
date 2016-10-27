"""
    Video comment API
"""
import endpoints
from protorpc import message_types

from greenday_core.api_exceptions import (
    BadRequestException, NotFoundException, ForbiddenException)
from greenday_core.constants import EventKind
from greenday_core.eventbus import publish_appevent
from greenday_core.models import (
    TimedVideoComment,
    Video
)

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required
)
from ..common.containers import VideoEntityContainer
from ..project.mixins import ProjectAPIMixin
from ..utils import get_obj_or_api_404

from .containers import (
    VideoCommentEntityContainer,
    CreateVideoRootCommentContainer,
    UpdateVideoCommentContainer,
    CreateVideoCommentReplyContainer,
    UpdateVideoCommentReplyContainer,
    VideoCommentReplyContainer
)
from .mappers import VideoCommentMapper, VideoCommentFullMapper

from .messages import (
    VideoCommentResponseMessage,
    VideoCommentListResponse,
    VideoCommentResponseMessageSlim
)


@greenday_api.api_class(
    resource_name='video_comments', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class VideoCommentAPI(BaseAPI, ProjectAPIMixin):
    """
        API to handle comments on videos

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        """
            Creates the video comment API
        """
        super(VideoCommentAPI, self).__init__(*args, **kwargs)
        self.slim_mapper = VideoCommentMapper(VideoCommentResponseMessageSlim)
        self.mapper = VideoCommentFullMapper(
            VideoCommentResponseMessage, slim_mapper=self.slim_mapper)

    @greenday_method(
        VideoEntityContainer, VideoCommentListResponse,
        path='project/{project_id}/video/{youtube_id}/comments',
        http_method='GET', name='list_comments',
        pre_middlewares=[auth_required])
    def list_comments(self, request):
        """
            Gets all root level comments on a video
        """
        project = self.get_project(request.project_id, assigned_only=True)

        try:
            video = Video.objects.select_related('youtube_video').get(
                project=project, youtube_id=request.youtube_id)
        except Video.DoesNotExist:
            try:
                video = Video.archived_objects.select_related(
                    'youtube_video').get(
                    project=project, youtube_id=request.youtube_id)
            except Video.DoesNotExist:
                raise NotFoundException('Video instance not found!')

        comments = (
            TimedVideoComment.get_root_comments_for(
                video, prefetch_replies=True)
        )

        return VideoCommentListResponse(
            items=[
                self.mapper.map(c, project=project, video=video)
                for c in comments
            ],
            is_list=True
        )

    @greenday_method(
        VideoCommentEntityContainer, VideoCommentResponseMessage,
        path='project/{project_id}/video/{youtube_id}/comments/{comment_id}',
        http_method='GET', name='get_comments',
        pre_middlewares=[auth_required])
    def get_comment(self, request):
        """
            Gets a root level comment on a video
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video.objects.select_related('youtube_video'),
            project=project, youtube_id=request.youtube_id)

        comment = get_obj_or_api_404(
            TimedVideoComment.objects.select_related('user'),
            tagged_object_id=video.pk,
            pk=request.comment_id)
        comment.video = video  # attach for mapping

        return self.mapper.map(comment, project=project, video=video)

    @greenday_method(
        CreateVideoRootCommentContainer, VideoCommentResponseMessage,
        path='project/{project_id}/video/{youtube_id}/comments',
        http_method='POST', name='create_root_comment',
        pre_middlewares=[auth_required])
    def create_root_comment(self, request):
        """
            Creates a new root level comment on the video
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video = get_obj_or_api_404(
            Video.objects.select_related('youtube_video'),
            project=project, youtube_id=request.youtube_id)

        comment = TimedVideoComment.add_root(
            video=video,
            start_seconds=request.start_seconds,
            text=request.text,
            user=self.current_user)

        publish_appevent(
            EventKind.TIMEDVIDEOROOTCOMMENTCREATED,
            object_id=comment.pk,
            video_id=video.pk,
            project_id=project.pk,
            user=self.current_user
        )

        return self.mapper.map(comment, project=project, video=video)

    @greenday_method(
        CreateVideoCommentReplyContainer, VideoCommentResponseMessageSlim,
        path='project/{project_id}/video/{youtube_id}/comments/{comment_id}/replies',
        http_method='POST', name='create_reply',
        pre_middlewares=[auth_required])
    def create_comment_reply(self, request):
        """
            Creates a reply to a root comment
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video.objects.select_related('youtube_video'),
            project=project, youtube_id=request.youtube_id)
        comment = get_obj_or_api_404(
            TimedVideoComment.objects.select_related('user'),
            tagged_object_id=video.pk,
            pk=request.comment_id)

        if not comment.is_root():
            raise BadRequestException(
                "Replies can only be added to root comments")

        reply = comment.add_reply(
            request.text,
            self.current_user)

        publish_appevent(
            EventKind.TIMEDVIDEOREPLYCOMMENTCREATED,
            object_id=reply.pk,
            video_id=video.pk,
            project_id=project.pk,
            meta=comment.pk,
            user=self.current_user
        )

        return self.slim_mapper.map(reply, project=project, video=video)

    @greenday_method(
        UpdateVideoCommentContainer, VideoCommentResponseMessage,
        path='project/{project_id}/video/{youtube_id}/comments/{comment_id}',
        http_method='PUT', name='update_comment',
        pre_middlewares=[auth_required])
    def update_comment(self, request):
        """
            Updates any video comment
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video.objects.select_related('youtube_video'),
            project=project, youtube_id=request.youtube_id)

        comment = get_obj_or_api_404(
            TimedVideoComment.objects.select_related('user'),
            tagged_object_id=video.pk,
            pk=request.comment_id)

        if (self.current_user != comment.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        comment.text = request.text

        if (comment.start_seconds != request.start_seconds
                and comment.is_root()):
            # update start_seconds on all children
            comment.start_seconds = request.start_seconds
            reply_ids = list(
                comment.get_children().values_list('pk', flat=True))
            (TimedVideoComment.objects
                .filter(pk__in=reply_ids)
                .update(start_seconds=request.start_seconds))

        comment.save()

        publish_appevent(
            EventKind.TIMEDVIDEOCOMMENTUPDATED,
            object_id=comment.pk,
            video_id=video.pk,
            project_id=project.pk,
            user=self.current_user)

        return self.mapper.map(comment, project=project, video=video)

    @greenday_method(
        UpdateVideoCommentReplyContainer, VideoCommentResponseMessage,
        path='project/{project_id}/video/{youtube_id}/comments/{comment_id}/replies/{reply_id}',
        http_method='PUT', name='update_reply',
        pre_middlewares=[auth_required])
    def update_reply(self, request):
        """
            Updates a video comment reply
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video.objects.select_related('youtube_video'),
            project=project, youtube_id=request.youtube_id)

        reply = get_obj_or_api_404(
            TimedVideoComment.objects.select_related('user'),
            tagged_object_id=video.pk,
            pk=request.reply_id)

        if (self.current_user != reply.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        reply.text = request.text

        reply.save()

        publish_appevent(
            EventKind.TIMEDVIDEOREPLYCOMMENTUPDATED,
            object_id=reply.pk,
            video_id=video.pk,
            project_id=project.pk,
            meta=request.comment_id,
            user=self.current_user)

        return self.mapper.map(reply, project=project, video=video)

    @greenday_method(
        UpdateVideoCommentContainer, VideoCommentResponseMessage,
        path='project/{project_id}/video/{youtube_id}/comments/{comment_id}',
        http_method='PATCH', name='patch_comment',
        pre_middlewares=[auth_required])
    def patch_comment(self, request):
        """
            Patches any video comment
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video.objects.select_related('youtube_video'),
            project=project, youtube_id=request.youtube_id)

        comment = get_obj_or_api_404(
            TimedVideoComment.objects.select_related('user'),
            tagged_object_id=video.pk,
            pk=request.comment_id)

        if (self.current_user != comment.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        if request.text is not None:
            comment.text = request.text

        if (request.start_seconds is not None and
                comment.start_seconds != request.start_seconds and
                comment.is_root()):
            # update start_seconds on all children
            comment.start_seconds = request.start_seconds
            reply_ids = list(
                comment.get_children().values_list('pk', flat=True))
            (TimedVideoComment.objects
                .filter(pk__in=reply_ids)
                .update(start_seconds=request.start_seconds))

        if request.text is not None or request.start_seconds is not None:
            comment.save()

            publish_appevent(
                EventKind.TIMEDVIDEOCOMMENTUPDATED,
                object_id=comment.pk,
                video_id=video.pk,
                project_id=project.pk,
                user=self.current_user)

        return self.mapper.map(comment, project=project, video=video)

    @greenday_method(
        VideoCommentEntityContainer, message_types.VoidMessage,
        path='project/{project_id}/video/{youtube_id}/comments/{comment_id}',
        http_method='DELETE', name='delete_comment',
        pre_middlewares=[auth_required])
    def delete_comment(self, request):
        """
            Deletes a comment. Can be a root comment or a reply.
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video.objects.select_related('youtube_video'),
            project=project,
            youtube_id=request.youtube_id)

        comment = get_obj_or_api_404(
            TimedVideoComment.objects.select_related('user'),
            tagged_object_id=video.pk,
            pk=request.comment_id)

        if (self.current_user != comment.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        comment.delete()

        publish_appevent(
            EventKind.TIMEDVIDEOCOMMENTDELETED,
            object_id=comment.pk,
            video_id=video.pk,
            project_id=project.pk,
            user=self.current_user)

        return message_types.VoidMessage()

    @greenday_method(
        VideoCommentReplyContainer, message_types.VoidMessage,
        path='project/{project_id}/video/{youtube_id}/comments/{comment_id}/replies/{reply_id}',
        http_method='DELETE', name='delete_reply',
        pre_middlewares=[auth_required])
    def delete_reply(self, request):
        """
            Deletes a video comment reply
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video.objects.select_related('youtube_video'),
            project=project,
            youtube_id=request.youtube_id)

        reply = get_obj_or_api_404(
            TimedVideoComment.objects.select_related('user'),
            tagged_object_id=video.pk,
            pk=request.reply_id)

        if (self.current_user != reply.user and
                not self.current_user.is_superuser):
            raise ForbiddenException

        reply.delete()

        publish_appevent(
            EventKind.TIMEDVIDEOREPLYCOMMENTDELETED,
            object_id=reply.pk,
            video_id=video.pk,
            project_id=project.pk,
            meta=request.comment_id,
            user=self.current_user)

        return message_types.VoidMessage()

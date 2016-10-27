"""
    Video tag API
"""
import endpoints
from protorpc import message_types

from django.db.models import Q

from greenday_core.api_exceptions import BadRequestException
from greenday_core.models import (
    Project, GlobalTag, ProjectTag, VideoTag, VideoTagInstance, Video
)
from ..mapper import GeneralMapper
from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required
)
from ..project.mixins import ProjectAPIMixin
from ..utils import (
    get_obj_or_api_404, update_object_from_request, patch_object_from_request
)

from ..tag.messages import OthersTaggedWithListResponse, TagResponseMessage

from .messages import (
    VideoTagResponseMessage,
    VideoTagListResponse,
    VideoTagInstanceResponseMessage,
)
from .containers import (
    VideoEntityContainer,
    VideoTagEntityContainer,
    VideoTagInsertEntityContainer,
    VideoTagUpdateEntityContainer,
    VideoTagInstanceEntityContainer,
    VideoTagInstanceInsertEntityContainer,
    VideoTagInstanceUpdateEntityContainer
)
from .mappers import VideoTagInstanceMapper, VideoTagMapper


@greenday_api.api_class(
    resource_name='video_tags', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class VideoTagAPI(BaseAPI, ProjectAPIMixin):
    """
        API to handle video tags.

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        """
            Creates the video tag API
        """
        super(VideoTagAPI, self).__init__(*args, **kwargs)
        self.mapper = VideoTagMapper(VideoTagResponseMessage)
        self.instance_mapper = VideoTagInstanceMapper(
            VideoTagInstanceResponseMessage)
        self.global_tag_mapper = GeneralMapper(GlobalTag, TagResponseMessage)

    @greenday_method(
        VideoEntityContainer, VideoTagListResponse,
        path='project/{project_id}/video/{youtube_id}/tags',
        http_method='GET', name='list_tags',
        pre_middlewares=[auth_required])
    def list_tags(self, request):
        """
            API Endpoint to get all video tags with nested video
            tag instances for the current video.
        """
        project = self.get_project(request.project_id, assigned_only=True)
        tags = [
            self.mapper.map(tag) for tag in
            VideoTag.objects
            .select_related('video', 'project_tag__global_tag')
            .prefetch_related('tag_instances')
            .filter(
                project_id=project.pk, video__youtube_id=request.youtube_id)
            .order_by('project_tag__global_tag__name')]
        return VideoTagListResponse(items=tags, is_list=True)

    @greenday_method(
        VideoEntityContainer, OthersTaggedWithListResponse,
        path='project/{project_id}/video/{youtube_id}/others-tagged-with',
        http_method='GET', name='others_tagged_with',
        pre_middlewares=[auth_required])
    def list_others_tagged_with(self, request):
        """
            API Endpoint to return a list of other relevant global tags not
            currently applied to the video that the user may wish to apply.

            This list consists of any current project tags that are not
            assigned to the video plus any tags assigned to the same video
            but in a different project that are also not assigned to
            this video. Tags from other projects are only provided for
            projects that have their tag privacy marked as public.
        """
        # grab project and video 404ing if they dont exist
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video.objects.select_related("youtube_video"),
            youtube_id=request.youtube_id,
            project_id=project.pk)

        # first grab a list of all the global tag ids that have already
        # been assigned to this video
        used_global_tags = list(video.videotags.all().values_list(
            'project_tag__global_tag_id', flat=True))

        # next we build a list of global tag ids that are assigned to the
        # current project, but not yet on the video
        project_tags = list(project.projecttags.exclude(
            global_tag_id__in=used_global_tags).values_list(
                'global_tag_id', flat=True))

        # next we build a list of global tag ids that are assigned to the
        # same video but in other projects provided that the project tag
        # privacy is public and that the tag has not already been applied
        # to the current video in question
        from_other_projects = list(
            VideoTag.objects
            .exclude(
                project_id=project.pk,
                project_tag__global_tag_id__in=used_global_tags)
            .filter(
                project__privacy_tags=2,
                video__youtube_id=video.youtube_id)
            .values_list('project_tag__global_tag_id', flat=True)
        )

        # join the two global tag lists together - this will also remove
        # duplicated global_tag_ids giving us a single list of un-used
        # global tag_ids for tags relevant to the same video
        unused_tag_ids = set(project_tags + from_other_projects)

        # grab the global tag objects
        unused_tags = GlobalTag.objects.filter(pk__in=unused_tag_ids)

        # build the response using the un-used tags.
        return OthersTaggedWithListResponse(
            items=[
                self.global_tag_mapper.map(tag) for tag in unused_tags
            ],
            is_list=True)

    @greenday_method(
        VideoTagInsertEntityContainer, VideoTagResponseMessage,
        path='project/{project_id}/video/{youtube_id}/tags',
        http_method='POST', name='create_tag',
        pre_middlewares=[auth_required])
    def create_tag(self, request):
        """
            API Endpoint to create a global tag and then apply it to the
            project and video.
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video, youtube_id=request.youtube_id, project_id=project.pk)

        global_tag = None
        if request.global_tag_id:
            global_tag = get_obj_or_api_404(
                GlobalTag, pk=request.global_tag_id)
        else:
            request.name = request.name.strip()
            if not request.name:
                raise BadRequestException("name cannot be blank")

            existing_tags = (
                GlobalTag.objects
                .filter(name=request.name)
                .filter(
                    Q(created_from_project=project) |
                    Q(created_from_project__privacy_tags=Project.PUBLIC))
                .select_related("created_from_project")
            )

            if existing_tags:
                global_tag = next(
                    (t for t in existing_tags if t.created_from_project == project),
                    None)

                if not global_tag:
                    global_tag = next(iter(existing_tags), None)

            if not global_tag:
                global_tag = GlobalTag.objects.create(
                    name=request.name,
                    description=request.description,
                    image_url=request.image_url,
                    user=self.current_user,
                    created_from_project=project
                )

        try:
            project_tag = ProjectTag.objects.get(
                project=project, global_tag=global_tag)
        except ProjectTag.DoesNotExist:
            project_tag = ProjectTag.add_root(
                project=project, global_tag=global_tag, user=self.current_user
            )

        video_tag, created = VideoTag.objects.get_or_create(
            project_tag=project_tag,
            video=video,
            defaults={
                "project": project,
                "user": self.current_user
            }
        )

        if not created:
            raise BadRequestException("Video tag already exists")
        return self.mapper.map(video_tag)

    @greenday_method(
        VideoTagUpdateEntityContainer, VideoTagResponseMessage,
        path='project/{project_id}/video/{youtube_id}/tags/{video_tag_id}',
        http_method='PUT', name='update_tag',
        pre_middlewares=[auth_required])
    def update_tag(self, request):
        """
            API Endpoint to update the attributes on a global tag
            from the video tag API.
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video_tag = get_obj_or_api_404(
            VideoTag.objects.select_related("project_tag__global_tag"),
            pk=request.video_tag_id,
            video__youtube_id=request.youtube_id,
            video__project_id=project.pk)

        update_object_from_request(request, video_tag.project_tag.global_tag)
        return self.mapper.map(video_tag)

    @greenday_method(
        VideoTagUpdateEntityContainer, VideoTagResponseMessage,
        path='project/{project_id}/video/{youtube_id}/tags/{video_tag_id}',
        http_method='PATCH', name='patch_tag',
        pre_middlewares=[auth_required])
    def patch_tag(self, request):
        """
            API Endpoint to patch the attributes on a global tag
            from the video tag API.
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video_tag = get_obj_or_api_404(
            VideoTag.objects.select_related("project_tag__global_tag"),
            pk=request.video_tag_id,
            video__youtube_id=request.youtube_id,
            video__project_id=project.pk)

        patch_object_from_request(request, video_tag.project_tag.global_tag)
        return self.mapper.map(video_tag)

    @greenday_method(
        VideoTagEntityContainer, VideoTagResponseMessage,
        path='project/{project_id}/video/{youtube_id}/tags/{video_tag_id}',
        http_method='GET', name='get_tag',
        pre_middlewares=[auth_required])
    def get_tag(self, request):
        """
            API Endpoint to get all video tag instances for the current
            video tag.
        """
        project = self.get_project(request.project_id, assigned_only=True)
        tag = get_obj_or_api_404(
            VideoTag,
            video__youtube_id=request.youtube_id,
            project=project,
            pk=request.video_tag_id)

        return self.mapper.map(tag)

    @greenday_method(
        VideoTagEntityContainer, message_types.VoidMessage,
        path='project/{project_id}/video/{youtube_id}/tags/{video_tag_id}',
        http_method='DELETE', name='delete_tag',
        pre_middlewares=[auth_required])
    def delete_tag(self, request):
        """
            API Endpoint to delete a video tag and all it's VideoTagInstance
            children.
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video_tag = get_obj_or_api_404(
            VideoTag,
            pk=request.video_tag_id,
            video__youtube_id=request.youtube_id,
            project_id=project.pk)
        video_tag.delete()
        return message_types.VoidMessage()

    @greenday_method(
        VideoTagInstanceEntityContainer, message_types.VoidMessage,
        path='project/{project_id}/video/{youtube_id}/tags/{video_tag_id}/'
        'instances/{instance_id}', http_method='DELETE',
        name='delete_instance',
        pre_middlewares=[auth_required])
    def delete_instance(self, request):
        """
            API Endpoint to delete an instance of a VideoTag
        """
        project = self.get_project(request.project_id, assigned_only=True)
        instance = get_obj_or_api_404(
            VideoTagInstance,
            pk=request.instance_id,
            video_tag_id=request.video_tag_id,
            video_tag__video__youtube_id=request.youtube_id,
            video_tag__video__project_id=project.pk)

        instance.delete()

        if not instance.video_tag.tag_instances.exists():
            instance.video_tag.delete()

        return message_types.VoidMessage()

    @greenday_method(
        VideoTagInstanceInsertEntityContainer, VideoTagInstanceResponseMessage,
        path='project/{project_id}/video/{youtube_id}/tags/{video_tag_id}/'
        'instances', http_method='POST',
        name='create_instance',
        pre_middlewares=[auth_required])
    def create_instance(self, request):
        """
            API Endpoint to create an instance of a VideoTag
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video_tag = get_obj_or_api_404(
            VideoTag,
            pk=request.video_tag_id,
            video__project_id=project.pk,
            video__youtube_id=request.youtube_id)

        instance = video_tag.tag_video(
            user=self.current_user,
            start_seconds=request.start_seconds,
            end_seconds=request.end_seconds)

        return self.instance_mapper.map(instance)

    @greenday_method(
        VideoTagInstanceUpdateEntityContainer,
        VideoTagInstanceResponseMessage,
        path='project/{project_id}/video/{youtube_id}/tags/{video_tag_id}/'
        'instances/{instance_id}', http_method='PUT',
        name='update_instance',
        pre_middlewares=[auth_required])
    def update_instance(self, request):
        """
            API Endpoint to update an instance of a VideoTag
        """
        project = self.get_project(request.project_id, assigned_only=True)
        instance = get_obj_or_api_404(
            VideoTagInstance, pk=request.instance_id,
            video_tag__id=request.video_tag_id,
            video_tag__video__youtube_id=request.youtube_id,
            video_tag__video__project_id=project.pk)
        update_object_from_request(request, instance)
        return self.instance_mapper.map(instance)

    @greenday_method(
        VideoTagInstanceUpdateEntityContainer,
        VideoTagInstanceResponseMessage,
        path='project/{project_id}/video/{youtube_id}/tags/{video_tag_id}/'
        'instances/{instance_id}',
        http_method='PATCH',
        name='patch_instance',
        pre_middlewares=[auth_required])
    def patch_instance(self, request):
        """
            API endpoint to patch an instance of a VideoTag
        """
        project = self.get_project(request.project_id, assigned_only=True)

        instance = get_obj_or_api_404(
            VideoTagInstance, pk=request.instance_id,
            video_tag__id=request.video_tag_id,
            video_tag__video__youtube_id=request.youtube_id,
            video_tag__video__project_id=project.pk)

        patch_object_from_request(request, instance)
        return self.instance_mapper.map(instance)

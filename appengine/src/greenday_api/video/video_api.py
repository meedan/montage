"""
    The Video API
"""
import endpoints
import itertools
from protorpc import message_types
from django.utils import timezone
from django.db.models import Q

from greenday_core.api_exceptions import (
    BadRequestException, ForbiddenException, NotFoundException)
from greenday_core.documents.video import VideoDocument
from greenday_core.eventbus import publish_appevent
from greenday_core.memoize_cache import cache_manager
from greenday_core.models import (
    Video,
    VideoCollection,
    UserVideoDetail,
    DuplicateVideoMarker
)
from greenday_core.constants import EventKind
from greenday_core.youtube_client import YouTubeClient

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required,
    add_order_to_repeated
)
from ..searchbot import VideoSearch, process_comma_seperate_filters
from ..utils import (
    get_obj_or_api_404,
    api_appevent,
)
from ..project.mixins import ProjectAPIMixin
from ..mapper import GeneralMapper
from .mappers import VideoTagSearchMapper, VideoMapper

from .caching import remove_video_list_cache
from .messages import (
    VideoResponseMessage,
    VideoListResponse,
    UserVideoDetailResponseMessage,
    BatchVideoResponseMessage,
    BatchListResponseMessage,
    VideoTagListResponse,
    VideoBatchListResponseMessage,
    VideoResponseMessageSlim
)

from .containers import(
    VideoEntityContainer, VideoInsertEntityContainer,
    VideoUpdateEntityContainer,
    VideoDuplicateEntityContainer,
    VideoBooleanFlagEntityContainer,
    VideoBatchContainer,
    VideoIDBatchContainer,
    CreateVideoBatchContainer,
    VideoFavouriteBatchContainer,
    VideoFilterContainer,
    ArchiveVideoBatchContainer
)

from .utils import make_batch_response_message, has_video_search_args


@greenday_api.api_class(
    resource_name='video', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class VideoAPI(BaseAPI, ProjectAPIMixin):
    """
        API for Videos

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        """
            Creates Video API
        """
        super(VideoAPI, self).__init__(*args, **kwargs)

        # standard video mapper
        self.mapper = VideoMapper()
        self.slim_mapper = VideoMapper(message_cls=VideoResponseMessageSlim)

        # favourite mapper to handle responses from favouriting.
        self.fave_mapper = GeneralMapper(
            UserVideoDetail, UserVideoDetailResponseMessage)

        # mapper for video tag filter
        self.video_tag_mapper = VideoTagSearchMapper()

    @greenday_method(
        VideoFilterContainer,
        VideoListResponse,
        path='project/{project_id}/video',
        http_method='GET',
        name='list',
        pre_middlewares=[auth_required],
        post_middlewares=[add_order_to_repeated])
    def video_list(self, request):
        """
            API Endpoint to list all videos within the passed project
        """
        project = self.get_project(
            request.project_id,
            assigned_only=True
        )

        def _video_list(request, project):

            if request.archived:
                qs = Video.archived_objects.all()
            else:
                qs = Video.objects.all()

            ordered_video_ids = None
            if request.collection_id:
                collection = get_obj_or_api_404(
                    VideoCollection,
                    pk=request.collection_id,
                    project_id=project.pk)

                ordered_video_ids = list(
                    collection.videocollectionvideos
                    .values_list('video_id', flat=True)
                )

            if has_video_search_args(request):
                # build search bot
                video_search = VideoSearch.create(
                    "videos", VideoDocument, ids_only=True)

                video_search = video_search.multi_filter(request)

                # grab 1000 results and run the pks into an ORM lookup so that
                # we can return database objects to the front end.
                ids = video_search[:1000]  # DN: this must be a slice
                qs = qs.filter(pk__in=ids)
            else:
                qs = qs.filter(project=project)

            videos = (
                qs
                .select_related("youtube_video")
                .prefetch_related("videocollectionvideos")
                .order_by('-modified')
            )

            if ordered_video_ids:
                video_dict = {v.pk: v for v in videos}
                videos = [
                    video_dict[vid] for vid in ordered_video_ids
                    if vid in video_dict
                ]

            # build the response
            return VideoListResponse(
                items=map(self.slim_mapper.map, videos),
                is_list=True
            )

        if has_video_search_args(request):
            # don't cache search results
            return _video_list(request, project)
        else:
            return cache_manager.get_or_set(
                _video_list,
                request,
                project,
                message_type=VideoListResponse,
                timeout=10)

    @greenday_method(VideoEntityContainer, VideoResponseMessage,
                      path='project/{project_id}/video/{youtube_id}',
                      http_method='GET',
                      name='get',
                      pre_middlewares=[auth_required])
    def video_get(self, request):
        """
            API Endpoint to retrieve a project video.
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video = get_obj_or_api_404(
            Video.non_trashed_objects
            .select_related("youtube_video")
            .prefetch_related('videocollectionvideos'),
            youtube_id=request.youtube_id,
            project_id=project.pk
        )

        try:
            user_video_detail = video.related_users.get(
                user=self.current_user)
        except UserVideoDetail.DoesNotExist:
            watched = False
        else:
            watched = user_video_detail.watched

        return self.mapper.map(video, watched=watched)

    @greenday_method(VideoInsertEntityContainer, VideoResponseMessage,
                      path='project/{project_id}/video', http_method='POST',
                      name='insert',
                      pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.VIDEOCREATED,
        id_getter_post=lambda s, req, res: res.id,
        video_id_getter_post=lambda s, req, res: res.id,
        project_id_getter=lambda s, req: req.project_id)
    def video_insert(self, request):
        """
            API Endpoint to add a video to a project
        """
        project = self.get_project(request.project_id, assigned_only=True)

        youtube_client = YouTubeClient()
        yt_video = youtube_client.update_or_create_videos(
            (request.youtube_id,))[0]

        try:
            video = (
                Video.all_objects
                .get(
                    youtube_video__youtube_id=request.youtube_id,
                    project_id=project.pk
                ))
        except Video.DoesNotExist:
            video = Video(
                project_id=project.pk,
                youtube_video=yt_video,
                youtube_id=yt_video.youtube_id,
                user_id=self.current_user.pk,
            )
        else:
            if not (video.trashed_at or video.archived_at):
                raise BadRequestException(
                    "The video '%s' already exists in this project" %
                    request.youtube_id)
            else:
                # if it's trashed or archived then restore it
                video.archived_at = video.trashed_at = None

        video.save()
        # attach youtube video for mapping response
        video.youtube_video = yt_video

        remove_video_list_cache(project)

        return self.mapper.map(video)

    @greenday_method(VideoUpdateEntityContainer, VideoResponseMessage,
                      path='project/{project_id}/video/{youtube_id}',
                      http_method='PUT',
                      name='update',
                      pre_middlewares=[auth_required])
    def video_update(self, request):
        """
            API Endpoint to update a project video
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video = get_obj_or_api_404(
            Video.objects.select_related("youtube_video"),
            youtube_id=request.youtube_id,
            project_id=project.pk
        )

        video.location_overridden = request.location_overridden
        video.recorded_date_overridden = request.recorded_date_overridden
        video.precise_location = request.precise_location

        if request.location_overridden:
            video.latitude = request.latitude
            video.longitude = request.longitude
        else:
            video.latitude = video.longitude = None

        if request.recorded_date_overridden:
            video.recorded_date = request.recorded_date
        else:
            video.recorded_date = None

        video.save()

        client = YouTubeClient()
        client.update_videos((video.youtube_video,))
        video.youtube_video.save()

        publish_appevent(
            EventKind.VIDEOUPDATED,
            object_id=video.pk,
            video_id=video.pk,
            project_id=project.pk,
            user=self.current_user)

        return self.mapper.map(video)

    @greenday_method(VideoUpdateEntityContainer, VideoResponseMessage,
                      path='project/{project_id}/video/{youtube_id}',
                      http_method='PATCH',
                      name='patch',
                      pre_middlewares=[auth_required])
    def video_patch(self, request):
        """
            API Endpoint to patch a project video
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video = get_obj_or_api_404(
            Video.objects.select_related("youtube_video"),
            youtube_id=request.youtube_id,
            project_id=project.pk
        )

        if request.location_overridden is not None:
            video.location_overridden = request.location_overridden
        if request.recorded_date_overridden is not None:
            video.recorded_date_overridden = request.recorded_date_overridden
        if request.precise_location is not None:
            video.precise_location = request.precise_location

        if video.location_overridden:
            if request.latitude is not None:
                video.latitude = request.latitude
            if request.longitude is not None:
                video.longitude = request.longitude
        else:
            video.latitude = video.longitude = None

        if video.recorded_date_overridden:
            video.recorded_date = request.recorded_date
        else:
            video.recorded_date = None

        video.save()

        publish_appevent(
            EventKind.VIDEOUPDATED,
            object_id=video.pk,
            video_id=video.pk,
            project_id=project.pk,
            user=self.current_user)

        return self.mapper.map(video)

    @greenday_method(VideoEntityContainer, message_types.VoidMessage,
                      path='project/{project_id}/video/{youtube_id}',
                      http_method='DELETE',
                      name='delete',
                      pre_middlewares=[auth_required])
    def video_delete(self, request):
        """
            API Endpoint to delete a project video
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video = get_obj_or_api_404(
            Video.non_trashed_objects.all(),
            project=project,
            youtube_id=request.youtube_id)

        if (not self.current_user.is_superuser and
                not project.is_owner_or_admin(self.current_user) and
                self.current_user.pk != video.user_id):
            raise ForbiddenException

        video_id = video.pk
        video.delete(trash=False)

        remove_video_list_cache(project)

        publish_appevent(
            EventKind.VIDEODELETED,
            object_id=video_id,
            video_id=video_id,
            project_id=project.pk,
            user=self.current_user
        )
        return message_types.VoidMessage()

    @greenday_method(
        VideoBatchContainer, BatchListResponseMessage,
        path='project/{project_id}/video/batch-delete',
        http_method='PUT', name='video_batch_delete',
        pre_middlewares=[auth_required])
    def video_batch_delete(self, request):
        """
            API Endpoint to soft delete a batch of videos.

            This will never hard delete a video
        """
        project = self.get_project(request.project_id, assigned_only=True)
        is_owner_or_admin = project.is_owner_or_admin(self.current_user)

        videos = {
            v.youtube_id: v for v in
            Video.all_objects
            .filter(
                trashed_at__isnull=True,
                project_id=project.pk,
                youtube_id__in=request.youtube_ids
            )
        }

        does_not_exist = [
            make_batch_response_message(yt_id, not_found=True)
            for yt_id in set(request.youtube_ids) - set(videos.keys())
        ]

        video_ids_to_delete, permission_denied, success = [], [], []
        for yt_id, video in videos.items():
            if self.current_user.id != video.user_id and not (
                    self.current_user.is_superuser or is_owner_or_admin):
                permission_denied.append(
                    make_batch_response_message(yt_id, forbidden=True))
            else:
                video_ids_to_delete.append(video.pk)
                success.append(
                    make_batch_response_message(yt_id, success=True))

        (Video.all_objects
            .filter(project=project, pk__in=video_ids_to_delete)
            .delete())

        remove_video_list_cache(project)

        return BatchListResponseMessage(
            items=success + does_not_exist + permission_denied,
            is_list=True)

    @greenday_method(
        ArchiveVideoBatchContainer, VideoBatchListResponseMessage,
        path='project/{project_id}/video/batch-archive',
        http_method='PUT', name='video_batch_archive',
        pre_middlewares=[auth_required])
    def video_batch_archive(self, request):
        """
            Archive or unarchive a batch of videos

            Pass unarchive=true to unarchive
        """
        project = self.get_project(request.project_id, assigned_only=True)
        is_owner_or_admin = project.is_owner_or_admin(self.current_user)

        qs = Video.archived_objects if request.unarchive else Video.objects

        videos = {
            v.youtube_id: v for v in
            qs
            .filter(
                project_id=project.pk,
                youtube_id__in=request.youtube_ids
            )
        }

        does_not_exist = [
            make_batch_response_message(yt_id, not_found=True)
            for yt_id in set(request.youtube_ids) - set(videos.keys())
        ]

        video_ids_to_update, permission_denied, success = [], [], []
        for yt_id, video in videos.items():
            if self.current_user.id != video.user_id and not (
                    self.current_user.is_superuser or is_owner_or_admin):
                permission_denied.append(
                    make_batch_response_message(yt_id, forbidden=True))
            else:
                video_ids_to_update.append(video.pk)
                success.append(
                    make_batch_response_message(yt_id, success=True))

        (
            qs
            .filter(project=project, pk__in=video_ids_to_update)
            .update(archived_at=None if request.unarchive else timezone.now()))

        remove_video_list_cache(project)

        for video_id in video_ids_to_update:
            publish_appevent(
                kind=EventKind.VIDEOUNARCHIVED if
                    request.unarchive else EventKind.VIDEOARCHIVED,
                object_id=video_id,
                video_id=video_id,
                project_id=project.pk,
                user=self.current_user)

        videos = (
            Video.all_objects
            .select_related("youtube_video")
            .filter(pk__in=video_ids_to_update)
            if video_ids_to_update else []
        )

        return VideoBatchListResponseMessage(
            items=success + does_not_exist + permission_denied,
            videos=map(self.mapper.map, videos),
            is_list=True)

    @greenday_method(
        VideoBatchContainer, VideoBatchListResponseMessage,
        path='project/{project_id}/video/batch-mark-as-duplicate',
        http_method='PUT', name='video_batch_mark_as_duplicate',
        pre_middlewares=[auth_required])
    def video_batch_mark_as_duplicate(self, request):
        """
            Takes a list of video IDs are marks them all as duplicates of
            one another
        """
        project = self.get_project(request.project_id, assigned_only=True)

        videos = {
            v.pk: v for v in
            Video.objects
            .select_related("youtube_video")
            .filter(
                project_id=project.pk,
                youtube_id__in=request.youtube_ids
            )
        }
        video_ids = videos.keys()
        youtube_ids = [v.youtube_id for v in videos.values()]
        combinations = [sorted(x) for x in itertools.combinations(video_ids, 2)]

        existing_marker_query = Q()
        for id1, id2 in combinations:
            existing_marker_query = (
                existing_marker_query |
                Q(video_1=id1, video_2=id2)
            )

        existing_markers = list(
            DuplicateVideoMarker.objects
            .filter(existing_marker_query)
            .values_list("video_1", "video_2")
        )

        new_markers = []
        for id1, id2 in combinations:
            if (id1, id2,) not in existing_markers:
                new_markers.append(DuplicateVideoMarker(
                    video_1=videos[id1],
                    video_2=videos[id2]))

        DuplicateVideoMarker.objects.bulk_create(new_markers)

        return VideoBatchListResponseMessage(
            items=[
                make_batch_response_message(yt_id, not_found=True)
                for yt_id in set(request.youtube_ids) - set(youtube_ids)
            ] + [
                make_batch_response_message(yt_id, success=True)
                for yt_id in youtube_ids
            ],
            videos=map(self.mapper.map, videos.values()),
            is_list=True)

    @greenday_method(
        VideoIDBatchContainer, VideoBatchListResponseMessage,
        path='project/{project_id}/video/{youtube_id}/batch-mark-video-as-duplicate',
        http_method='PUT', name='video_batch_mark_video_as_duplicate',
        pre_middlewares=[auth_required])
    def video_batch_mark_video_as_duplicate(self, request):
        """
            Takes a list of video IDs and makes them all as a duplicate of the
            given video
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video, project=project, youtube_id=request.youtube_id)

        videos = {
            v.pk: v for v in
            Video.objects
            .select_related("youtube_video")
            .filter(
                project_id=project.pk,
                youtube_id__in=request.youtube_ids
            )
        }
        video_ids = videos.keys()
        youtube_ids = [v.youtube_id for v in videos.values()]
        combinations = [sorted((video.pk, vid,)) for vid in video_ids]

        existing_marker_query = Q()
        for id1, id2 in combinations:
            existing_marker_query = (
                existing_marker_query |
                Q(video_1=id1, video_2=id2)
            )

        existing_markers = list(
            DuplicateVideoMarker.objects
            .filter(existing_marker_query)
            .values_list("video_1", "video_2")
        )

        new_markers = []
        for vid in video_ids:
            if tuple(sorted((video.pk, vid,))) not in existing_markers:
                new_markers.append(DuplicateVideoMarker(
                    video_1=video,
                    video_2=videos[vid]))

        DuplicateVideoMarker.objects.bulk_create(new_markers)

        return VideoBatchListResponseMessage(
            items=[
                make_batch_response_message(yt_id, not_found=True)
                for yt_id in set(request.youtube_ids) - set(youtube_ids)
            ] + [
                make_batch_response_message(yt_id, success=True)
                for yt_id in youtube_ids
            ],
            videos=map(self.mapper.map, videos.values()),
            is_list=True)

    @greenday_method(
        CreateVideoBatchContainer, VideoBatchListResponseMessage,
        path='project/{project_id}/video/batch-create',
        http_method='PUT', name='video_batch_create',
        pre_middlewares=[auth_required])
    def video_batch_create(self, request):
        project = self.get_project(request.project_id, assigned_only=True)

        duplicate_videos = {
            v.youtube_video.youtube_id: v for v in
            Video.objects
            .filter(
                project=project,
                youtube_video__youtube_id__in=request.youtube_ids
            )
        }

        success, error, videos = [], [], []

        for youtube_id in request.youtube_ids:
            if youtube_id in duplicate_videos:
                video = duplicate_videos[youtube_id]
                error.append(
                    make_batch_response_message(
                        video.youtube_id,
                        error="The video '{0}' already exists in this project"
                        .format(youtube_id)))
                videos.append(duplicate_videos[youtube_id])
                continue

        youtube_ids_of_videos_to_add = [
            yt_id for yt_id in request.youtube_ids
            if yt_id not in duplicate_videos]

        youtube_client = YouTubeClient()
        youtube_videos = {
            v.youtube_id: v for v in
            youtube_client.update_or_create_videos(
                youtube_ids_of_videos_to_add)
        }

        for yt_id, yt_video in youtube_videos.items():
            try:
                video = (
                    Video.all_objects
                    .get(
                        youtube_video__youtube_id=yt_id,
                        project_id=project.pk
                    ))
            except Video.DoesNotExist:
                video = Video(
                    project_id=project.pk,
                    youtube_video=yt_video,
                    youtube_id=yt_video.youtube_id,
                    user_id=self.current_user.pk,
                )
            else:
                if not (video.trashed_at or video.archived_at):
                    error.append(
                        make_batch_response_message(
                            None,
                            error="The video '{0}' already exists in "
                            "this project".format(yt_id))
                    )
                else:
                    # if it's trashed or archived then restore it
                    video.archived_at = video.trashed_at = None

            video.save()
            # attach youtube video for mapping response
            video.youtube_video = yt_video
            videos.append(video)

            success.append(
                make_batch_response_message(video.youtube_id, success=True))

            publish_appevent(
                EventKind.VIDEOCREATED,
                object_id=video.pk,
                video_id=video.pk,
                project_id=project.pk,
                user=self.current_user)

        remove_video_list_cache(project)
        return VideoBatchListResponseMessage(
            items=success + error,
            videos=map(self.mapper.map, videos),
            is_list=True)

    @greenday_method(
        VideoDuplicateEntityContainer, VideoResponseMessage,
        path='project/{project_id}/video/{youtube_id}/duplicates',
        http_method='PUT',
        name='mark_duplicate', pre_middlewares=[auth_required])
    def video_mark_duplicate(self, request):
        """
            API Endpoint to mark a video as a duplicate of another video
            even if the 2 videos have unique YouTube ID's.
        """
        project = self.get_project(request.project_id, assigned_only=True)

        if request.youtube_id == request.duplicate_of_id:
            raise ForbiddenException(
                'You cannot mark a video as a duplicate of itself.')

        videos = {
            v.youtube_id: v for v in
            Video.objects
            .select_related("youtube_video")
            .filter(
                project=project,
                youtube_id__in=(
                request.youtube_id, request.duplicate_of_id,)
            )
        }

        if not len(videos) == 2:
            raise NotFoundException

        video = videos[request.youtube_id]
        duplicate_of = videos[request.duplicate_of_id]

        DuplicateVideoMarker.add_marker(video, duplicate_of)

        return self.mapper.map(duplicate_of)

    @greenday_method(
        VideoEntityContainer, VideoListResponse,
        path='project/{project_id}/video/{youtube_id}/duplicates',
        http_method='GET',
        name='list_duplicates',
        pre_middlewares=[auth_required])
    def video_duplicates_list(self, request):
        """
            API Endpoint to list all videos in the current project that have
            been marked as duplicates of other project videos.
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video = get_obj_or_api_404(
            Video, project=project, youtube_id=request.youtube_id)

        return VideoListResponse(
            items=map(self.slim_mapper.map, video.get_duplicates()),
            is_list=True
        )

    @greenday_method(
        VideoIDBatchContainer, VideoBatchListResponseMessage,
        path='project/{project_id}/video/{youtube_id}/batch-delete-duplicate-markers',
        http_method='PUT',
        name='batch_delete_duplicate_markers',
        pre_middlewares=[auth_required])
    def video_batch_delete_duplicate_marker(self, request):
        """
            Deletes the duplicate marker for a list of videos which are already
            marked as a duplicate of the given video
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video, project=project, youtube_id=request.youtube_id)

        videos = {
            v.pk: v for v in
            Video.objects
            .select_related("youtube_video")
            .filter(
                project_id=project.pk,
                youtube_id__in=request.youtube_ids)
        }
        video_ids = videos.keys()
        youtube_ids = [v.youtube_id for v in videos.values()]
        combinations = [sorted((video.pk, vid,)) for vid in video_ids]

        existing_marker_query = Q()
        for id1, id2 in combinations:
            existing_marker_query = (
                existing_marker_query | Q(video_1=id1, video_2=id2))
        existing_markers = list(
            DuplicateVideoMarker.objects
            .filter(existing_marker_query)
            .values_list("video_1", "video_2")
        )

        missing_marker_ids = [
            v.youtube_id for v in videos.values()
            if tuple(sorted((video.pk, v.pk,))) not in existing_markers
        ]

        DuplicateVideoMarker.objects.filter(existing_marker_query).delete()

        return VideoBatchListResponseMessage(
            items=[
                make_batch_response_message(yt_id, not_found=True)
                for yt_id in set(request.youtube_ids) - set(youtube_ids)
            ] + [
                make_batch_response_message(yt_id, success=True)
                for yt_id in youtube_ids if yt_id not in missing_marker_ids
            ] + [
                BatchVideoResponseMessage(
                    youtube_id=yt_id,
                    success=False,
                    msg='Video with youtube_id {0} is not marked as a duplicate'
                    .format(yt_id)) for yt_id in missing_marker_ids
            ],
            videos=map(self.mapper.map, videos.values()),
            is_list=True)

    @greenday_method(
        VideoEntityContainer, message_types.VoidMessage,
        path='project/{project_id}/video/{youtube_id}/unarchive',
        http_method='PUT',
        name='unarchive',
        pre_middlewares=[auth_required])
    def video_unarchive(self, request):
        """
            Unarchives the given video
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video = get_obj_or_api_404(
            Video.archived_objects.all(),
            youtube_id=request.youtube_id,
            project=project)

        video.unarchive()

        remove_video_list_cache(project)

        publish_appevent(
            kind=EventKind.VIDEOUNARCHIVED,
            object_id=video.pk,
            video_id=video.pk,
            project_id=project.pk,
            user=self.current_user)

        return message_types.VoidMessage()

    @greenday_method(
        VideoBooleanFlagEntityContainer, VideoResponseMessage,
        path='project/{project_id}/video/{youtube_id}/set-favourite',
        http_method='PUT', name='video_set_favourite',
        pre_middlewares=[auth_required])
    def video_set_favourite(self, request):
        """
            API Endpoint to allow a user to set whether a video is favourite
            or not
        """
        project = self.get_project(request.project_id, assigned_only=True)
        video = get_obj_or_api_404(
            Video.objects.select_related("youtube_video"),
            youtube_id=request.youtube_id,
            project_id=project.pk)

        video.favourited = request.value
        video.save()

        return self.mapper.map(video)

    @greenday_method(
        VideoFavouriteBatchContainer,
        BatchListResponseMessage,
        path='project/{project_id}/video/batch-favourite',
        http_method='PUT', name='video_batch_mark_favourite',
        pre_middlewares=[auth_required])
    def video_batch_mark_favourite(self, request):
        """
            API Endpoint to mark a batch of videos as favourites.
        """
        project = self.get_project(request.project_id, assigned_only=True)

        video_ids = {
            youtube_id: pk for pk, youtube_id in
            Video.objects
            .filter(project_id=project.pk, youtube_id__in=request.youtube_ids)
            .values_list('pk', 'youtube_id')
        }

        (Video.objects
            .filter(project=project, pk__in=video_ids.values())
            .update(favourited=request.value))

        remove_video_list_cache(project)

        return BatchListResponseMessage(
            items=[
                make_batch_response_message(yt_id, not_found=True)
                for yt_id in set(request.youtube_ids) - set(video_ids.keys())
            ] + [
                make_batch_response_message(yt_id, success=True)
                for yt_id in video_ids.keys()
            ],
            is_list=True
        )

    @greenday_method(
        VideoBooleanFlagEntityContainer, UserVideoDetailResponseMessage,
        path='project/{project_id}/video/{youtube_id}/mark-watched',
        http_method='PUT', name='video_user_mark_watched',
        pre_middlewares=[auth_required])
    def video_user_mark_watched(self, request):
        """
            API Endpoint to allow a user to mark whether they have
            watched a video or not.
        """
        project = self.get_project(request.project_id, assigned_only=True)
        try:
            video = Video.objects.get(
                youtube_id=request.youtube_id, project=project.pk)
        except Video.DoesNotExist:
            try:
                video = Video.archived_objects.get(
                    youtube_id=request.youtube_id, project=project.pk)
            except Video.DoesNotExist:
                raise NotFoundException('Video instance not found!')
        try:
            user_detail = UserVideoDetail.objects.get(
                video_id=video.pk, user=self.current_user)
        except UserVideoDetail.DoesNotExist:
            user_detail = UserVideoDetail.objects.create(
                video=video, user=self.current_user, watched=request.value)
        else:
            user_detail.watched = request.value
            user_detail.save()
        return self.fave_mapper.map(user_detail)

    @greenday_method(
        VideoFilterContainer, VideoTagListResponse,
        path='project/{project_id}/video/filter_by_tags',
        http_method='GET', name='video_tag_filter',
        pre_middlewares=[auth_required])
    def video_tag_filter(self, request):
        """
            API endpoint to return tag instances applied to videos

            Accepts filters to restrict the set of videos to return tag
            instances for.
        """
        project = self.get_project(request.project_id, assigned_only=True)

        def _video_tag_filter(request):
            if request.archived:
                qs = Video.archived_objects.all()
            else:
                qs = Video.objects.all()

            qs = qs.select_related("youtube_video")

            if has_video_search_args(request):
                video_search = VideoSearch.create(
                    "videos", VideoDocument, ids_only=True)

                video_search = video_search.multi_filter(request)
                # for now, this is a plain search on the video index.
                # We then get all of the tags from the database and
                # map them in memory
                ids = video_search[:1000]

                video_map = qs.in_bulk(ids)
            else:
                video_map = {v.id: v for v in qs.filter(project=project)}

            return self.video_tag_mapper.map(video_map)

        if has_video_search_args(request):
            # don't cache search results
            return _video_tag_filter(request)

        return cache_manager.get_or_set(
            _video_tag_filter,
            request,
            message_type=VideoTagListResponse)

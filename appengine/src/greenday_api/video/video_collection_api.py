"""
    VideoCollection API
"""
import endpoints
from protorpc import message_types

from greenday_core.api_exceptions import BadRequestException, NotFoundException
from greenday_core.models import VideoCollection, Video, VideoCollectionVideo
from greenday_core.documents.video import VideoDocument
from greenday_core.constants import EventKind
from greenday_core.eventbus import publish_appevent

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required,
    add_order_to_repeated
)
from ..mapper import GeneralMapper
from ..searchbot import VideoSearch
from ..utils import (
    get_obj_or_api_404,
    update_object_from_request,
    api_appevent
)
from ..project.mixins import ProjectAPIMixin

from .mappers import VideoCollectionMapper, VideoMapper
from .messages import (
    CollectionResponseMessage,
    CollectionResponseMessageSkinny,
    CollectionListResponseMessage,
    VideoBatchListResponseMessage,
    VideoListResponse,
    VideoResponseMessageSlim
)
from .containers import(
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

from .utils import make_batch_response_message, has_video_search_args


@greenday_api.api_class(
    resource_name='collection', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class VideoCollectionAPI(BaseAPI, ProjectAPIMixin):
    """
        API for VideoCollections

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        """
            Creates the video collection API
        """
        super(VideoCollectionAPI, self).__init__(*args, **kwargs)

        self.skinny_mapper = GeneralMapper(
            VideoCollection, CollectionResponseMessageSkinny)
        self.mapper = VideoCollectionMapper()
        self.video_mapper = VideoMapper()
        self.slim_mapper = VideoMapper(message_cls=VideoResponseMessageSlim)

    @greenday_method(CollectionInsertEntityContainer,
                      CollectionResponseMessage,
                      path='project/{project_id}/collection',
                      http_method='POST',
                      name='insert',
                      pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.VIDEOCOLLECTIONCREATED,
        id_getter_post=lambda s, req, res: res.id,
        project_id_getter=lambda s, req: req.project_id)
    def video_collection_insert(self, request):
        """
            Creates a new VideoCollection
        """
        project = self.get_project(request.project_id, assigned_only=True)
        collection = VideoCollection.objects.create(
            project=project,
            name=request.name)
        return self.mapper.map(collection)

    @greenday_method(CollectionEntityContainer,
                      CollectionResponseMessage,
                      path='project/{project_id}/collection/{id}',
                      http_method='GET',
                      name='get',
                      pre_middlewares=[auth_required],
                      post_middlewares=[add_order_to_repeated])
    def video_collection_get(self, request):
        """ Gets a VideoCollection entity """
        project = self.get_project(request.project_id, assigned_only=True)
        collection = get_obj_or_api_404(
            VideoCollection, pk=request.id, project_id=project.pk)
        return self.mapper.map(collection)

    @greenday_method(CollectionListContainer,
                      CollectionListResponseMessage,
                      path='project/{project_id}/collection',
                      http_method='GET',
                      name='list',
                      pre_middlewares=[auth_required])
    def video_collection_list(self, request):
        """
            Lists all VideoCollections on a given `Project`
        """
        project = self.get_project(request.project_id, assigned_only=True)

        return CollectionListResponseMessage(items=map(
            self.skinny_mapper.map, project.collections.all()),
            is_list=True
        )

    @greenday_method(
        CollectionVideoFilterContainer,
        VideoListResponse,
        path='project/{project_id}/collection/{id}/video',
        http_method='GET',
        name='list_videos',
        pre_middlewares=[auth_required],
        post_middlewares=[add_order_to_repeated])
    def video_collection_video_list(self, request):
        """
            Lists all videos within the given collection
        """
        project = self.get_project(request.project_id, assigned_only=True)

        collection = get_obj_or_api_404(
            VideoCollection, pk=request.id, project_id=project.pk)

        ordered_video_ids = list(
            collection.videocollectionvideos
            .values_list('video_id', flat=True)
        )

        qs = project.videos

        if has_video_search_args(request):
            # see VideoAPI.video_list
            video_search = VideoSearch.create(
                "videos", VideoDocument, ids_only=True)

            video_search = video_search.multi_filter(request)
            video_search = video_search.filter_collections(unicode(request.id))

            # grab 1000 results and run the pks into an ORM lookup so that
            # we can return database objects to the front end.
            ids = video_search[:1000]  # DN: this must be a slice
            qs = qs.filter(pk__in=ids)

        videos = (
            qs
            .select_related("youtube_video")
            .in_bulk(ordered_video_ids)
        )

        ordered_videos = [
            videos[vid] for vid in ordered_video_ids
            if vid in videos
        ]

        return VideoListResponse(
            items=map(self.slim_mapper.map, ordered_videos),
            is_list=True
        )

    @greenday_method(CollectionUpdateEntityContainer,
                      CollectionResponseMessage,
                      path='project/{project_id}/collection/{id}',
                      http_method='PUT',
                      name='update',
                      pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.VIDEOCOLLECTIONUPDATED,
        id_getter=lambda s, req: req.id,
        project_id_getter=lambda s, req: req.project_id)
    def video_collection_update(self, request):
        """
            Updates a VideoCollection
        """
        project = self.get_project(request.project_id, assigned_only=True)
        collection = get_obj_or_api_404(
            VideoCollection, pk=request.id, project_id=project.pk)
        update_object_from_request(request, collection)

        return self.mapper.map(collection)

    @greenday_method(CollectionEntityContainer,
                      message_types.VoidMessage,
                      path='project/{project_id}/collection/{id}',
                      http_method='DELETE',
                      name='delete',
                      pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.VIDEOCOLLECTIONDELETED,
        id_getter=lambda s, req: req.id,
        project_id_getter=lambda s, req: req.project_id)
    def video_collection_delete(self, request):
        """
            Deletes a VideoCollection
        """
        project = self.get_project(request.project_id, assigned_only=True)
        collection = get_obj_or_api_404(
            VideoCollection, pk=request.id, project_id=project.pk)
        collection.delete()
        return message_types.VoidMessage()

    @greenday_method(
        CollectionVideoContainer, message_types.VoidMessage,
        path='project/{project_id}/collection/{id}/video',
        http_method='PUT',
        name='add_video',
        pre_middlewares=[auth_required])
    def add_video_to_collection(self, request):
        """
            Adds a Video to a VideoCollection
        """
        project = self.get_project(request.project_id, assigned_only=True)
        collection = get_obj_or_api_404(VideoCollection, pk=request.id)
        video = get_obj_or_api_404(
            Video, project=project, youtube_id=request.youtube_id)

        if (video.pk not in
                collection.videos.all().values_list('pk', flat=True)):
            collection.add_video(video)

            publish_appevent(
                EventKind.VIDEOADDEDTOCOLLECTION,
                object_id=video.pk,
                video_id=video.pk,
                project_id=project.pk,
                meta=collection.pk,
                user=self.current_user)
        return message_types.VoidMessage()

    @greenday_method(
        MoveCollectionVideoContainer,
        message_types.VoidMessage,
        path='project/{project_id}/collection/{id}/video/{youtube_id}/move',
        http_method='POST',
        name='move_video',
        pre_middlewares=[auth_required])
    def move_video_in_collection(self, request):
        """
            Moves a video within a collection
        """
        if request.youtube_id == request.sibling_youtube_id:
            raise BadRequestException(
                "youtube_id and sibling_youtube_id must be different")

        self.get_project(request.project_id, assigned_only=True)

        collection = get_obj_or_api_404(VideoCollection, pk=request.id)

        video_collection_videos = (
            VideoCollectionVideo.objects
            .select_related('video')
            .filter(
                collection=collection,
                video__youtube_id__in=(
                    request.youtube_id, request.sibling_youtube_id)
            )
        )

        try:
            video_to_move = next(
                vcv for vcv in video_collection_videos
                if vcv.video.youtube_id == request.youtube_id)
        except StopIteration:
            raise NotFoundException("youtube_id")

        try:
            video_sibling = next(
                vcv for vcv in video_collection_videos
                if vcv.video.youtube_id == request.sibling_youtube_id)
        except StopIteration:
            raise NotFoundException("sibling_youtube_id")

        video_to_move.move(
            video_sibling,
            pos="left" if request.before else "right")

        return message_types.VoidMessage()

    @greenday_method(
        CollectionVideoBatchContainer,
        VideoBatchListResponseMessage,
        path='project/{project_id}/collection/{id}/add_batch',
        http_method='PUT', name='add_video_batch',
        pre_middlewares=[auth_required])
    def add_video_batch_to_collection(self, request):
        """
            API Endpoint to add a batch of videos to a collection.
        """
        project = self.get_project(request.project_id, assigned_only=True)
        collection = get_obj_or_api_404(VideoCollection, pk=request.id)

        videos = {
            v.pk: v for v in
            Video.objects
            .select_related("youtube_video")
            .filter(
                project_id=project.pk,
                youtube_id__in=request.youtube_ids)
        }

        does_not_exist = [
            make_batch_response_message(yt_id, not_found=True)
            for yt_id in set(request.youtube_ids) - set(v.youtube_id for v in videos.values())
        ]

        already_in_collection_ids = list(VideoCollectionVideo.objects.filter(
            video_id__in=videos.keys(),
            collection=collection).values_list("video_id", flat=True))

        already_in_collection = [
            make_batch_response_message(
                videos[vid].youtube_id,
                error='Video is already in collection')
            for vid in already_in_collection_ids]

        success, errors = [], []

        for vid, video in videos.items():
            if vid in already_in_collection_ids:
                continue

            try:
                collection.add_video(video)
            except Exception as e:
                errors.append(
                    make_batch_response_message(
                        video.youtube_id, error=unicode(e)))
            else:
                success.append(
                    make_batch_response_message(video.youtube_id, success=True))

                publish_appevent(
                    EventKind.VIDEOADDEDTOCOLLECTION,
                    object_id=video.pk,
                    video_id=video.pk,
                    project_id=project.pk,
                    meta=collection.pk,
                    user=self.current_user)

        return VideoBatchListResponseMessage(
            items=success + errors + already_in_collection + does_not_exist,
            videos=map(self.video_mapper.map, videos.values()))

    @greenday_method(
        CollectionDeleteVideoContainer,
        message_types.VoidMessage,
        path='project/{project_id}/collection/{id}/video/{youtube_id}',
        http_method='DELETE',
        name='remove_video',
        pre_middlewares=[auth_required])
    def remove_video_from_collection(self, request):
        """
            Removes a Video from a VideoCollection
        """
        project = self.get_project(request.project_id, assigned_only=True)
        collection = get_obj_or_api_404(
            VideoCollection, pk=request.id, project_id=project.pk)
        video = get_obj_or_api_404(
            Video, project=project, youtube_id=request.youtube_id)
        if (video.pk in
                collection.videos.all().values_list('pk', flat=True)):
            collection.remove_video(video.pk)

            publish_appevent(
                EventKind.VIDEOREMOVEDFROMCOLLECTION,
                object_id=video.pk,
                video_id=video.pk,
                project_id=project.pk,
                meta=collection.pk,
                user=self.current_user)
        return message_types.VoidMessage()

    @greenday_method(
        CollectionVideoBatchContainer,
        message_types.VoidMessage,
        path='project/{project_id}/collection/{id}/remove_batch',
        http_method='PUT', name='remove_video_batch',
        pre_middlewares=[auth_required])
    def remove_video_batch_from_collection(self, request):
        """
            API Endpoint to remove a batch of videos from a collection.
        """
        project = self.get_project(request.project_id, assigned_only=True)
        collection = get_obj_or_api_404(VideoCollection, pk=request.id)
        collection_videos = (
            VideoCollectionVideo.objects
            .filter(
                video__youtube_id__in=request.youtube_ids,
                collection=collection,
                collection__project=project)
        )
        removed_from_collection = [vcv.video_id for vcv in collection_videos]
        collection_videos.delete()
        for video_id in removed_from_collection:
            publish_appevent(
                EventKind.VIDEOREMOVEDFROMCOLLECTION,
                object_id=video_id,
                video_id=video_id,
                project_id=project.pk,
                meta=collection.pk,
                user=self.current_user
            )
        return message_types.VoidMessage()

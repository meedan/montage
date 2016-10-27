"""
    Defines the OneSearch API
"""
import endpoints

from django.db import models

# import project deps
from greenday_core.api_exceptions import NotFoundException
from greenday_core.documents.project import ProjectDocument
from greenday_core.documents.video import VideoDocument
from greenday_core.models import Video, ProjectUser
from search.indexes import Index
from search.ql import Q
from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required
)
from ..searchbot import VideoSearch
from ..project.mixins import ProjectAPIMixin
from .mappers import (
    OneSearchProjectIndexMapper, OneSearchVideoIndexMapper,
    OneSearchVideoFilterMapper
)
from .messages import (
    OneSearchProjectResponseMessage,
    OneSearchProjectListResponse,
    OneSearchAdvancedVideoListResponse,
    OneSearchVideoResponseMessage,
    OneSearchVideoListResponse,
)
from .containers import (
    OneSearchEntityContainer,
    OneSearchProjectContextEntityContainer,
    OneSearchAdvancedVideoEntityContainer
)


# OneSearch API.
@greenday_api.api_class(
    resource_name='onesearch', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class OneSearchAPI(BaseAPI, ProjectAPIMixin):
    """
        API to handle universal searches.
        Extends BaseAPI and the ProjectAPIMixin. This gives
        us helper methods to access projects and current user.

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        super(OneSearchAPI, self).__init__(*args, **kwargs)
        self.project_index_mapper = OneSearchProjectIndexMapper(
            None, OneSearchProjectResponseMessage)
        self.video_index_mapper = OneSearchVideoIndexMapper(
            None, OneSearchVideoResponseMessage)
        self.video_filter_mapper = OneSearchVideoFilterMapper()

    @greenday_method(
        OneSearchEntityContainer, OneSearchProjectListResponse,
        path='onesearch/project', http_method='GET', name='projects',
        pre_middlewares=[auth_required])
    def search_projects(self, request):
        """
            API Endpoint to quick search user projects.

            TODO: This endpoint may need extending to search all
            public projects at a global level at some point. However, this
            means adding more context to the ProjectDocument search index.
            We are trying to keep them small and only add fields as required.
            For now this will suit our needs.

            DEPERECATED
            -----------
            This code is currently deprecated as this search has been removed
            from all designs and concepts along with the PRD. Leaving code here
            in case the client decides to re-implement at some point in the
            future.
        """
        projects = []
        search_query = Index(name='projects').search(ProjectDocument)

        if request.q:
            search_query = search_query.keywords(request.q)

        for p in search_query.filter(
                assigned_users=self.current_user.pk)[:1000]:
            projects.append(self.project_index_mapper.map(p))
        return OneSearchProjectListResponse(items=projects, is_list=True)

    @greenday_method(
        OneSearchProjectContextEntityContainer,
        OneSearchVideoListResponse,
        path='onesearch/video', http_method='GET', name='videos',
        pre_middlewares=[auth_required])
    def search_videos(self, request):
        """
            API Endpoint to quick search videos. A project ID can be passed
            in order to restrict the search to project context. Default
            is to search all videos within a users assigned projects plus
            any other videos in Montage that are assigned to public projects.
        """
        user_projects = self.get_user_project_ids()

        if request.project_id and request.project_id not in user_projects:
            raise NotFoundException

        # now search for all videos matching the query
        video_search = (
            VideoSearch.create('videos', VideoDocument, ids_only=False)
        )

        if request.q:
            video_search = video_search.keywords(request.q)

        if request.exclude_ids:
            ids = request.exclude_ids.split(',')
            if ids:
                video_search = video_search.filter(~Q(id=ids))

        # if we are constraining to a project then do that.
        # otherwise, we want to search for videos in projects that the user has
        # access to
        if request.project_id:
            video_search = video_search.filter(project_id=request.project_id)
        else:
            video_search = video_search.filter_private_to_project_ids(
                user_projects)

        return OneSearchVideoListResponse(
            items=map(self.video_index_mapper.map, video_search[:1000]),
            is_list=True)

    @greenday_method(
        OneSearchAdvancedVideoEntityContainer,
        OneSearchAdvancedVideoListResponse,
        path='onesearch/advanced/video',
        http_method='GET', name='advanced_videos',
        pre_middlewares=[auth_required])
    def advanced_search_videos(self, request):
        """
            API Endpoint to carry out and advanced search on videos.
            A project ID can be passed in order to restrict the search to
            project context. Default is to search all videos within a users
            assigned projects plus any other videos in Montage that are
            assigned to public projects.
        """
        user_projects = self.get_user_project_ids()

        if request.project_id and request.project_id not in user_projects:
            raise NotFoundException

        video_search = VideoSearch.create(
            "videos", VideoDocument, ids_only=True)

        # if we are constraining to a project then do that.
        # otherwise, we want to search for videos in projects that the user has
        # access to
        if request.project_id:
            video_search = video_search.filter_projects(request.project_id)
        else:
            video_search = video_search.filter_private_to_project_ids(
                user_projects)

        video_search = video_search.multi_filter(request)

        ids = video_search[:1000]

        # query the db for the videos.
        videos = (
            Video.objects
            .select_related('youtube_video')
            .prefetch_related('videocollectionvideos')
            .filter(pk__in=ids)
        )

        # return the response.
        return OneSearchAdvancedVideoListResponse(
            items=map(self.video_filter_mapper.map, videos),
            is_list=True)

    def get_user_project_ids(self):
        """
            Returns the IDs of all projects that the user is assigned to
        """
        return list(
            ProjectUser.objects
            .filter(user=self.current_user)
            .filter(
                models.Q(is_owner=True) |
                models.Q(is_admin=True) |
                models.Q(is_assigned=True)
            )
            .values_list('project_id', flat=True)
        )

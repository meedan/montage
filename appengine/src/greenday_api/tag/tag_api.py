"""
    Tag API
"""
import endpoints
from protorpc import message_types

from django.db import models

from search.indexes import Index
from search.ql import Q

from greenday_core.api_exceptions import ForbiddenException, NotFoundException
from greenday_core.documents.tag import AutoCompleteTagDocument
from greenday_core.memoize_cache import cache_manager
from greenday_core.models import GlobalTag, ProjectTag
from greenday_core.tag_merger import TagMerger

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required,
    auth_superuser
)
from ..mapper import GeneralMapper
from .mappers import TagMapper
from .messages import (
    TagResponseMessage,
    TagListResponse,
    TagSplitListResponse,
    MergeTagRequestMessage
)
from .containers import (
    TagEntityContainer,
    TagSearchEntityContainer,
)


@greenday_api.api_class(
    resource_name='tags', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class TagAPI(BaseAPI):
    """
        API to handle global tags.
    """
    def __init__(self, *args, **kwargs):
        """
            Creates tag API
        """
        super(TagAPI, self).__init__(*args, **kwargs)
        self.mapper = GeneralMapper(GlobalTag, TagResponseMessage)
        self.tag_document_mapper = TagMapper(None, TagResponseMessage)

    @greenday_method(
        TagSearchEntityContainer, TagSplitListResponse,
        path='tags/search', http_method='GET', name='search',
        pre_middlewares=[auth_required])
    def search_tags(self, request):
        """
            API Endpoint to search global tags.

            Object disposed after request is completed.
        """
        results_limit = 10
        project_search_results = []
        global_search_results = []

        i = Index(name='tags')
        search_query = i.search(AutoCompleteTagDocument)

        if request.q:
            search_query = search_query.filter(n_grams=request.q)

        if request.project_id:
            search_query = search_query.filter(project_ids=request.project_id)

            project_search_results = list(search_query[:results_limit])

            # get 5 global results or more if we don't have enough project
            # results
            if len(project_search_results) < (results_limit / 2):
                remaining = results_limit - len(project_search_results)
            else:
                remaining = results_limit / 2

            # hack - need to get the search package to clone queries
            # shouldn't need to build up an entirely new object
            search_query = i.search(AutoCompleteTagDocument).filter(
                ~Q(project_ids=request.project_id))

            if request.q:
                search_query = search_query.filter(n_grams=request.q)

            # get global results
            global_search_results = list(search_query[:remaining])
        else:
            global_search_results = search_query[:results_limit]

        return TagSplitListResponse(
            project_tags=[
                self.tag_document_mapper.map(
                    tag, project_id=request.project_id)
                for tag in project_search_results
            ],
            global_tags=[
                self.tag_document_mapper.map(tag)
                for tag in global_search_results
            ])

    @greenday_method(
        message_types.VoidMessage, TagListResponse,
        path='tags', http_method='GET', name='list',
        pre_middlewares=[auth_superuser])
    def tag_list(self, request):
        """
            API Endpoint to get a specific global tag.
        """
        def _tag_list():
            return TagListResponse(
                items=map(
                    self.tag_document_mapper.map,
                    GlobalTag.objects.all()),
                is_list=True
            )

        return cache_manager.get_or_set(
            _tag_list,
            message_type=TagListResponse)

    @greenday_method(
        TagEntityContainer, TagResponseMessage,
        path='tags/{id}', http_method='GET', name='get',
        pre_middlewares=[auth_superuser])
    def tag_get(self, request):
        """
            API Endpoint to get a specific global tag.
        """
        index = Index(name='tags')
        tag = index.get(
            str(request.id), document_class=AutoCompleteTagDocument)
        if not tag:
            raise NotFoundException(
                "Tag with id: {0} not found".format(
                    request.id))
        return self.tag_document_mapper.map(tag)

    @greenday_method(
        MergeTagRequestMessage,
        TagResponseMessage,
        path='tags/merge',
        http_method='POST',
        name='merge',
        pre_middlewares=[auth_required]
    )
    def tag_merge(self, request):
        """
            Merges two tags together.

            This takes effect for all tags across projects
        """
        tags = GlobalTag.objects.in_bulk(
            (request.merging_from_tag_id, request.merging_into_tag_id,))

        if not self.current_user.is_superuser:
            project_tags = (
                ProjectTag.objects
                .filter(global_tag__in=tags)
                .filter(
                    models.Q(project__projectusers__user=self.current_user) &
                    (
                        models.Q(project__projectusers__is_owner=True) |
                        models.Q(project__projectusers__is_admin=True) |
                        models.Q(project__projectusers__is_assigned=True)
                    )
                )
            ).values("project_id").annotate(models.Count("id")).order_by()

            # both tags should be present in at least one of the user projects
            if not project_tags or not max(
                    p["id__count"] for p in project_tags) == 2:
                raise ForbiddenException

        for tag_id in (
                request.merging_from_tag_id, request.merging_into_tag_id,):
            if tag_id not in tags:
                raise NotFoundException(tag_id)

        merger = TagMerger(
            tags[request.merging_from_tag_id],
            tags[request.merging_into_tag_id])

        merger.do_merge()

        return self.mapper.map(tags[request.merging_into_tag_id])

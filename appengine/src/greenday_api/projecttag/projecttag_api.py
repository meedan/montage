"""
    Defines the project tag API
"""
import endpoints
from protorpc import message_types
from django.db import IntegrityError
from django.db.models import Count, Q

from greenday_core.api_exceptions import (
    BadRequestException,
    NotFoundException,
    TagAlreadyAppliedToProject
)
from greenday_core.memoize_cache import cache_manager
from greenday_core.models import ProjectTag, GlobalTag, Project

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required
)
from ..utils import (
    get_obj_or_api_404,
    update_object_from_request,
    patch_object_from_request
)
from ..project.mixins import ProjectAPIMixin

from .mappers import ProjectTagMapper
from .messages import (
    ProjectTagListResponse,
    ProjectTagSlimMessage,
    ProjectTagMessage,
)
from .containers import (
    ProjectIDContainer,
    ProjectTagIDContainer,
    PutProjectTagContainer,
    CreateProjectTagContainer,
    MoveProjectTagContainer
)


@greenday_api.api_class(
    resource_name='projecttag', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class ProjectTagAPI(BaseAPI, ProjectAPIMixin):
    """
        API for ProjectTags

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        """
            Creates the project tag API
        """
        self.mapper = ProjectTagMapper(ProjectTagMessage)
        self.slim_mapper = ProjectTagMapper(ProjectTagSlimMessage)
        super(ProjectTagAPI, self).__init__(*args, **kwargs)

    @greenday_method(
        ProjectIDContainer,
        ProjectTagListResponse,
        path='project/{project_id}/tags',
        http_method='GET',
        name='list',
        pre_middlewares=[auth_required]
    )
    def projecttag_list(self, request):
        """ Lists all tags on the project """
        project = self.get_project(request.project_id, assigned_only=True)

        def _projecttag_list(project):
            tags = list(
                ProjectTag.get_tree()
                .filter(project=project)
                .select_related('global_tag')
                .with_taginstance_sum()
                .prefill_parent_cache()
            )
            return ProjectTagListResponse(
                items=map(self.slim_mapper.map, tags),
                is_list=True)

        return cache_manager.get_or_set(
            _projecttag_list,
            project,
            message_type=ProjectTagListResponse)

    @greenday_method(
        ProjectTagIDContainer,
        ProjectTagMessage,
        path='project/{project_id}/tags/{project_tag_id}',
        http_method='GET',
        name='get',
        pre_middlewares=[auth_required]
    )
    def projecttag_get(self, request):
        """ Gets a specific tag on the given project """
        project = self.get_project(request.project_id, assigned_only=True)

        tag = (
            project.projecttags
            .select_related('global_tag')
            .annotate(videotag_count=Count('videotags'))
            .get(pk=request.project_tag_id)
        )

        return self.mapper.map(tag)

    @greenday_method(
        PutProjectTagContainer,
        ProjectTagMessage,
        path='project/{project_id}/tags/{project_tag_id}',
        http_method='PUT',
        name='add_and_update',
        pre_middlewares=[auth_required]
    )
    def projecttag_put(self, request):
        """
            Updates the given global tag.
        """
        project = self.get_project(request.project_id, assigned_only=True)

        project_tag = get_obj_or_api_404(
            ProjectTag, project=project, pk=request.project_tag_id)

        update_object_from_request(request, project_tag.global_tag)

        return self.mapper.map(project_tag)

    @greenday_method(
        PutProjectTagContainer,
        ProjectTagMessage,
        path='project/{project_id}/tags/{project_tag_id}',
        http_method='PATCH',
        name='add_and_patch',
        pre_middlewares=[auth_required]
    )
    def projecttag_patch(self, request):
        """
            Patches the given global tag and assigns it to the project if it
            isn't already assigned. Use patch behaviour when updating
        """
        project = self.get_project(request.project_id, assigned_only=True)

        project_tag = get_obj_or_api_404(
            ProjectTag, project=project, pk=request.project_tag_id)

        patch_object_from_request(request, project_tag.global_tag)

        return self.mapper.map(project_tag)

    @greenday_method(
        CreateProjectTagContainer,
        ProjectTagMessage,
        path='project/{project_id}/tags',
        http_method='POST',
        name='create',
        pre_middlewares=[auth_required]
    )
    def projecttag_create(self, request):
        """
            Creates a new global tag and assigns it to the project
        """
        project = self.get_project(request.project_id, assigned_only=True)

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
            project_tag = ProjectTag.add_root(
                global_tag=global_tag,
                project=project,
                user=self.current_user
            )
        except IntegrityError:
            raise TagAlreadyAppliedToProject(
                "Tag \"{0}\" has already been added to this project".format(
                    global_tag.name))

        return self.mapper.map(project_tag)

    @greenday_method(
        ProjectTagIDContainer,
        message_types.VoidMessage,
        path='project/{project_id}/tags/{project_tag_id}',
        http_method='DELETE',
        name='delete',
        pre_middlewares=[auth_required]
    )
    def projecttag_delete(self, request):
        """
            Deletes the given tag from the project.

            This also deletes all tags from videos and all instances of
            those tags
        """
        project = self.get_project(request.project_id, assigned_only=True)

        project_tag = get_obj_or_api_404(
            ProjectTag, project=project, pk=request.project_tag_id)

        project_tag.delete()

        return message_types.VoidMessage()

    @greenday_method(
        MoveProjectTagContainer,
        ProjectTagMessage,
        path='project/{project_id}/tags/{project_tag_id}/move',
        http_method='PUT',
        name='move',
        pre_middlewares=[auth_required]
    )
    def projecttag_move(self, request):
        """
            Moves the tag within the hierarchy.

            Takes the ID of a sibling tag and orders the tag
            to appear after it (unless before: true is passed)

            Also takes the ID of a parent tag
        """
        project = self.get_project(request.project_id, assigned_only=True)

        if request.project_tag_id in (request.parent_tag_id, request.sibling_tag_id,):
            raise BadRequestException(
                "Cannot move tag relative to itself")

        tags = {
            pt.pk: pt for pt in
            ProjectTag.objects.filter(
                project=project,
                pk__in=filter(None, (
                    request.project_tag_id,
                    request.sibling_tag_id,
                    request.parent_tag_id))
            ).select_related('global_tag')
        }

        project_tag = tags.get(request.project_tag_id)
        if not project_tag:
            raise NotFoundException(request.project_tag_id)

        if request.sibling_tag_id:
            sibling_tag = tags.get(request.sibling_tag_id)
            if not sibling_tag:
                raise NotFoundException(
                    "sibling_tag_id: {0}".format(request.sibling_tag_id))

            project_tag.move(
                sibling_tag,
                pos="left" if request.before else "right")
        elif request.parent_tag_id:
            parent_tag = tags.get(request.parent_tag_id)
            if not parent_tag:
                raise NotFoundException(
                    "parent_tag_id: {0}".format(request.parent_tag_id))

            project_tag.move(parent_tag, "last-child")

        elif request.parent_tag_id is 0:
            last_root_tag = ProjectTag.get_last_root_node()
            project_tag.move(last_root_tag, "last-sibling")

        # reload because treebeard uses updates and doesn't update mode
        project_tag = ProjectTag.objects.get(pk=project_tag.pk)

        return self.mapper.map(project_tag)

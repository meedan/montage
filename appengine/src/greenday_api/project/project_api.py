"""
    Defines the project API
"""
import endpoints, re
from protorpc import message_types

from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.conf import settings
from django.utils import timezone

from greenday_core import eventbus
from greenday_core.memoize_cache import cache_manager
from greenday_core.api_exceptions import (
    BadRequestException, ForbiddenException, NotFoundException)
from greenday_core.constants import EventKind
from greenday_core.models import (
    Project,
    ProjectUser,
    Video,
    VideoTagInstance,
    PendingUser,
    YouTubeVideo
)
from greenday_core.email_templates import (
    NEW_USER_INVITED,
    EXISTING_USER_INVITED
)
from greenday_core.utils import (
    get_gcs_image_serving_url,
    send_email
)

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required
)
from ..utils import (
    get_obj_or_api_404,
    update_object_from_request,
    patch_object_from_request,
    api_appevent
)
from ..common.containers import IDContainer

from .caching import remove_project_list_user_cache
from .messages import (
    ProjectRequestMessage,
    ProjectResponseMessage,
    ProjectResponseMessageSlim,
    ProjectListResponse,
    ProjectCollaboratorsResponseMessage,
    ProjectUserListResponse,
    ProjectUpdatesMessage,
    ProjectUpdateCountsMessage,
    ProjectStatsMessage,
    TagCountMessage,
    DistinctChannelListResponse,
    DistinctChannelMessage
)
from .mixins import ProjectAPIMixin
from .mappers import (
    ProjectMapper, GenericProjectUpdateMapper, ProjectCollaboratorMapper)

# Custom request containers for all API methods
from .containers import (
    ProjectListRequest,
    ProjectUpdateEntityContainer,
    ProjectUserEntityContainer,
    ProjectUserIDEntityContainer,
    ProjectIDContainer,
)

"""
    In order to extract multiple emails that might have been mistakenly added
"""
def get_emails(s):

    regex = re.compile(("([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                        "{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                        "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"))
    """Returns an iterator of matched emails found in string s."""
    # Removing lines that start with '//' because the regular expression
    # mistakenly matches patterns like 'http://foo@bar.com' as '//foo@bar.com'.
    return (email[0] for email in re.findall(regex, s) if not email[0].startswith('//'))

# PROJECT
@greenday_api.api_class(
    resource_name='project', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class ProjectAPI(BaseAPI, ProjectAPIMixin):
    """
        API for Projects

        Object disposed after request is completed.
    """
    PROJECT_LIST_QUERYSET = (
        Project.objects
        .prefetch_related("projectusers__user")
        .with_videos()
    )

    def __init__(self, *args, **kwargs):
        """
            Creates the project API
        """
        super(ProjectAPI, self).__init__(*args, **kwargs)
        self.mapper = ProjectMapper(Project, ProjectResponseMessage)
        self.slim_mapper = ProjectMapper(Project, ProjectResponseMessageSlim)
        self.user_mapper = ProjectCollaboratorMapper(
            ProjectUser, ProjectCollaboratorsResponseMessage)
        self.project_update_mapper = GenericProjectUpdateMapper()

    @greenday_method(ProjectListRequest, ProjectListResponse,
                      path='project', http_method='GET', name='myprojects',
                      pre_middlewares=[auth_required])
    def project_list_user(self, request):
        """
            Lists all projects that the current user is assigned to
        """
        def _project_list_user(user, pending):
            qry = self.PROJECT_LIST_QUERYSET.get_projects_for(self.current_user)

            if pending is not None:
                qry = qry.filter(
                    Q(projectusers__user=user) &
                    Q(projectusers__is_pending=pending)
                )

            items = [
                self.slim_mapper.map(p, current_user=user)
                for p in qry
            ]
            return ProjectListResponse(items=items, is_list=True)

        return cache_manager.get_or_set(
            _project_list_user,
            self.current_user,
            request.pending,
            message_type=ProjectListResponse)

    @greenday_method(IDContainer, ProjectResponseMessage,
                      path='project/{id}', http_method='GET', name='get',
                      pre_middlewares=[auth_required])
    def project_get(self, request):
        """
            Gets a single project
        """
        project = self.get_project(
            request.id,
            assigned_only=True
        )

        project.fill_prefetch_cache("collections", project.collections.all())
        project.fill_prefetch_cache(
            "projectusers", project.projectusers.select_related("user"))
        project.fill_prefetch_cache(
            "projecttags",
            (
                project.projecttags
                .select_related("global_tag")
                .with_taginstance_sum()
            )
        )

        return self.mapper.map(project, current_user=self.current_user)

    @greenday_method(ProjectRequestMessage, ProjectResponseMessage,
                      path='project', http_method='POST', name='insert',
                      pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTCREATED,
        id_getter_post=lambda s, req, res: res.id,
        project_id_getter_post=lambda s, req, res: res.id,)
    def project_insert(self, request):
        """
            Creates a new project
        """
        if not self.current_user.is_whitelisted:
            raise ForbiddenException(
                "User must be whitelisted to create projects")

        project = Project.objects.create(
            name=request.name,
            description=request.description,
            image_url=request.image_url,
            image_gcs_filename=request.image_gcs_filename,
            privacy_project=request.privacy_project or Project.PRIVATE,
            privacy_tags=request.privacy_tags or Project.PUBLIC
        )

        project.set_owner(self.current_user)

        # cheeky hack to prevent further DB queries
        project.fill_prefetch_cache("collections", project.collections.none())
        project.fill_prefetch_cache("projecttags", project.projecttags.none())
        project.fill_prefetch_cache("videotags", project.videotags.none())
        project.fill_prefetch_cache("projectusers", project.projectusers.all())

        remove_project_list_user_cache(self.current_user)

        return self.mapper.map(project, current_user=self.current_user)

    @greenday_method(ProjectUpdateEntityContainer, ProjectResponseMessage,
                      path='project/{id}', http_method='PUT', name='update',
                      pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTUPDATED,
        id_getter=lambda s, req: req.id,
        project_id_getter=lambda s, req: req.id)
    def project_update(self, request):
        """
            Updates a project
        """
        project = self.get_project(
            request.id,
            check_fn=lambda p: p.is_owner_or_admin(self.current_user)
        )

        update_object_from_request(request, project)

        project.fill_prefetch_cache("collections", project.collections.all())
        project.fill_prefetch_cache(
            "projectusers", project.projectusers.select_related("user"))
        project.fill_prefetch_cache(
            "projecttags",
            (
                project.projecttags
                .select_related("global_tag")
                .with_taginstance_sum()
            )
        )
        remove_project_list_user_cache(self.current_user)

        return self.mapper.map(project, current_user=self.current_user)

    @greenday_method(ProjectUpdateEntityContainer, ProjectResponseMessage,
                      path='project/{id}', http_method='PATCH', name='patch',
                      pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTUPDATED,
        id_getter=lambda s, req: req.id,
        project_id_getter=lambda s, req: req.id)
    def project_patch(self, request):
        """
            Patches a project
        """
        project = self.get_project(
            request.id,
            check_fn=lambda p: p.is_owner_or_admin(self.current_user)
        )

        patch_object_from_request(request, project)

        project.fill_prefetch_cache("collections", project.collections.all())
        project.fill_prefetch_cache(
            "projectusers", project.projectusers.select_related("user"))
        project.fill_prefetch_cache(
            "projecttags",
            (
                project.projecttags
                .select_related("global_tag")
                .with_taginstance_sum()
            )
        )
        remove_project_list_user_cache(self.current_user)

        return self.mapper.map(project, current_user=self.current_user)

    @greenday_method(IDContainer, message_types.VoidMessage,
                      path='project/{id}', http_method='DELETE', name='delete',
                      pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTDELETED,
        id_getter=lambda s, req: req.id,
        project_id_getter=lambda s, req: req.id)
    def project_delete(self, request):
        """
            Deletes a project
        """
        project = self.get_project(
            request.id, check_fn=lambda p: p.owner == self.current_user)
        project.delete(trash=False)

        remove_project_list_user_cache(self.current_user)

        return message_types.VoidMessage()

    @greenday_method(IDContainer, ProjectResponseMessage,
                      path='project/{id}/restore', http_method='POST',
                      name='restore', pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.PROJECTRESTORED,
        id_getter=lambda s, req: req.id,
        project_id_getter=lambda s, req: req.id)
    def project_restore(self, request):
        """
            Restores a deleted project
        """
        try:
            project = Project.trash.get(pk=request.id)
        except Project.DoesNotExist:
            raise NotFoundException(
                "{0} instance with {1} not found".format(
                    Project.__name__, 'pk=%s' % request.id))

        if (not self.current_user.is_superuser and
                self.current_user != project.owner):
            raise ForbiddenException

        project.restore()

        project.fill_prefetch_cache("collections", project.collections.all())
        project.fill_prefetch_cache(
            "projectusers", project.projectusers.select_related("user"))

        remove_project_list_user_cache(self.current_user)

        return self.mapper.map(project, current_user=self.current_user)

    @greenday_method(ProjectIDContainer, ProjectUserListResponse,
                      path='project/{project_id}/users', http_method='GET',
                      name='users', pre_middlewares=[auth_required])
    def project_users(self, request):
        """
            Gets all users assigned to a project
        """
        project = self.get_project(
            request.project_id,
            assigned_only=True
        )

        query = project.projectusers.select_related('user').all()
        if not (
                self.current_user.is_superuser or
                project.is_owner_or_admin(self.current_user)
                ):
            query = query.filter(is_pending=False)

        return ProjectUserListResponse(
            items=map(self.user_mapper.map, query),
            is_list=True)

    @greenday_method(ProjectUserEntityContainer, ProjectUserListResponse,
                      path='project/{project_id}/users', http_method='POST',
                      name='add_user', pre_middlewares=[auth_required])
    def project_add_user(self, request):
        project_users = []
        for email in get_emails(request.email):
            """
            Adds a user to the project
            """
            project = self.get_project(
                request.project_id,
                check_fn=lambda p: p.is_owner_or_admin(self.current_user)
            )

            def send_invite_email():
                send_email(
                    "You've been invited to collaborate on a Montage project",
                    EXISTING_USER_INVITED.format(
                        project_name=project.name,
                        home_link='https://montage.storyful.com'),
                    email
                )

            User = get_user_model()

            project_user = None
            try:
                user = User.objects.get(email=email)

                project_user = (project.add_admin
                    if request.as_admin
                    else project.add_assigned)(user)

                eventbus.publish_appevent(
                    kind=EventKind.USERINVITEDASPROJECTADMIN
                    if request.as_admin else EventKind.USERINVITEDASPROJECTUSER,
                    object_id=user.pk,
                    project_id=project.pk,
                    user=self.current_user
                )

                send_invite_email()

            except User.DoesNotExist:
                pending_user, created = User.objects.get_or_create(
                    email=email,
                    username=email)

                project_user = (project.add_admin
                    if request.as_admin
                    else project.add_assigned)(pending_user)

                eventbus.publish_appevent(
                    kind=EventKind.PENDINGUSERINVITEDASPROJECTADMIN
                    if request.as_admin
                    else EventKind.PENDINGUSERINVITEDASPROJECTUSER,
                    object_id=pending_user.pk,
                    project_id=project.pk,
                    meta=pending_user.email,
                    user=self.current_user
                )

                if created:
                    send_email(
                        "You've been invited to join Montage",
                        NEW_USER_INVITED.format(
                            project_name=project.name,
                            home_link='https://montage.storyful.com'),
                        pending_user.email
                    )
                else:
                    send_invite_email()
            project_users.append(project_user)

        return ProjectUserListResponse(
            items=map(self.user_mapper.map, project_users),
            is_list=True)
        # return self.user_mapper.map(project_users)

    @greenday_method(ProjectUserIDEntityContainer, message_types.VoidMessage,
                      path='project/{project_id}/users/{id}',
                      http_method='DELETE',
                      name='remove_user',
                      pre_middlewares=[auth_required])
    def project_remove_user(self, request):
        """
            Removes a user from the project

            id: The ProjectUser ID
        """
        project = self.get_project(
            request.project_id,
            check_fn=lambda p: p.is_owner_or_admin(self.current_user)
        )

        projectuser = get_obj_or_api_404(ProjectUser, pk=request.id)

        projectuser.delete()

        if projectuser.user_id:
            eventbus.publish_appevent(
                kind=EventKind.USERREMOVED,
                object_id=projectuser.user_id,
                project_id=project.pk,
                user=self.current_user
            )
        elif projectuser.pending_user_id:
            eventbus.publish_appevent(
                kind=EventKind.PENDINGUSERREMOVED,
                object_id=projectuser.pending_user_id,
                project_id=project.pk,
                user=self.current_user
            )

        return message_types.VoidMessage()

    @greenday_method(ProjectIDContainer, ProjectUpdatesMessage,
                      path='project/my/{project_id}/updates',
                      http_method='GET', name='my_project_updates',
                      pre_middlewares=[auth_required])
    def project_updates_user(self, request):
        """
            Gets a list of all project updates that the user has not yet seen
        """
        project = self.get_project(
            request.project_id, assigned_only=True
        )

        user_relation = project.get_user_relation(self.current_user)
        if not user_relation:
            raise ForbiddenException(
                "User has no relationship with this project")

        events, objects = eventbus.get_events_with_objects(
            user_relation.last_updates_viewed,
            kind=(
                EventKind.VIDEOCREATED,
                EventKind.USERACCEPTEDPROJECTINVITE,
            ),
            project_id=request.project_id
        )

        items = {
            "created_videos": [],
            "users_joined": []
        }
        model_type_to_event_type = {
            "video": "created_videos",
            "user": "users_joined"
        }

        for model_type, models in objects.items():
            for model in models:
                # assuming that there should only be one event per object
                event = next(
                    (e for e in events if e.object_id == model.id), None)

                update_message = self.project_update_mapper.map(model, event)
                items[model_type_to_event_type[model_type]].append(
                    update_message)

        return ProjectUpdatesMessage(**items)

    @greenday_method(ProjectIDContainer, ProjectUpdateCountsMessage,
                      path='project/my/{project_id}/updates/counts',
                      http_method='GET', name='my_project_update_counts',
                      pre_middlewares=[auth_required])
    def project_update_counts_user(self, request):
        """
            Gets a count of all project updates that the user has not seen
        """
        project = self.get_project(
            request.project_id, assigned_only=True
        )

        user_relation = project.get_user_relation(self.current_user)
        if not user_relation:
            raise ForbiddenException(
                "User has no relationship with this project")

        event_counts = eventbus.get_event_counts(
            user_relation.last_updates_viewed,
            kind=(
                EventKind.VIDEOCREATED,
                EventKind.USERACCEPTEDPROJECTINVITE,
            ),
            project_id=request.project_id)

        event_type_to_model_type = {
            "created_videos": "video",
            "users_joined": "user"
        }

        items = {
            event_type: event_counts.get(model_type, 0)
            for event_type, model_type in event_type_to_model_type.items()
        }

        return ProjectUpdateCountsMessage(**items)

    @greenday_method(
        ProjectIDContainer,
        message_types.VoidMessage,
        path='project/my/{project_id}/update-last-viewed',
        http_method='POST',
        name='update_last_viewed',
        pre_middlewares=[auth_required])
    def update_last_viewed(self, request):
        """
            Updates the timestamp at which the user last viewed project updates
        """
        project = self.get_project(
            request.project_id, assigned_only=True
        )

        project.set_updates_viewed(self.current_user)

        return message_types.VoidMessage()

    @greenday_method(
        ProjectIDContainer,
        ProjectResponseMessage,
        path='project/my/{project_id}/accept',
        http_method='POST',
        name='accept_project_invitation',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.USERACCEPTEDPROJECTINVITE,
        id_getter=lambda s, req: s.current_user.id,
        project_id_getter=lambda s, req: req.project_id)
    def accept_project_invitation(self, request):
        """
            Accepts an invitation to be assigned to a project
        """
        project = self.get_project(request.project_id)

        projectuser = project.get_user_relation(self.current_user)

        if not projectuser:
            raise ForbiddenException

        if not projectuser.is_pending:
            raise BadRequestException("User is not pending")

        projectuser.is_pending = False
        projectuser.last_updates_viewed = timezone.now()

        projectuser.save()

        project.fill_prefetch_cache(
            "projectusers", project.projectusers.select_related("user").all())

        remove_project_list_user_cache(self.current_user)

        return self.mapper.map(project, current_user=self.current_user)

    @greenday_method(
        ProjectIDContainer,
        message_types.VoidMessage,
        path='project/my/{project_id}/reject',
        http_method='POST',
        name='reject_project_invitation',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.USERREJECTEDPROJECTINVITE,
        id_getter=lambda s, req: s.current_user.id,
        project_id_getter=lambda s, req: req.project_id)
    def reject_project_invitation(self, request):
        """
            Rejects an invitation to be assigned to a project
        """
        project = self.get_project(request.project_id)

        projectuser = project.get_user_relation(self.current_user)

        if not projectuser:
            raise ForbiddenException

        if not projectuser.is_pending:
            raise BadRequestException("User is not pending")

        projectuser.delete()

        remove_project_list_user_cache(self.current_user)

        # TODO: email?

        return message_types.VoidMessage()

    @greenday_method(
        ProjectIDContainer,
        ProjectStatsMessage,
        path='project/{project_id}/stats',
        http_method='GET',
        name='get_project_stats',
        pre_middlewares=[auth_required])
    def get_project_stats(self, request):
        """
            Gets stats on videos and tag counts for the project
        """
        project = self.get_project(request.project_id)

        def _get_project_stats(project):
            total_tags = VideoTagInstance.objects.filter(
                video_tag__project=project).count()

            tag_name_path = "video_tag__project_tag__global_tag__name"
            tag_name_count_path = "{0}__count".format(tag_name_path)
            tags = (
                VideoTagInstance.objects
                .filter(video_tag__project=project)
                .values(tag_name_path)
                .annotate(Count(tag_name_path))
                .order_by("-" + tag_name_count_path)
            )[:20]

            return {
                "total_videos": (
                    Video.non_trashed_objects
                    .filter(project=project)
                    .count()
                ),
                "archived_videos": Video.trash.filter(project=project).count(),
                "favourited_videos": (
                    Video.objects
                    .filter(project=project)
                    .filter(favourited=True)
                    .count()
                ),
                "video_tags": total_tags,
                "watched_videos": (
                    Video.objects
                    .values("related_users")
                    .filter(related_users__watched=True)
                    .annotate(Count('related_users'))
                    .filter(related_users__count__gt=0)
                    .count()
                ),
                "total_tags": total_tags,
                "top_tags": [
                    TagCountMessage(
                        name=tag_obj[tag_name_path],
                        count=tag_obj[tag_name_count_path]
                    ) for tag_obj in tags]
            }
        items = cache_manager.get_or_set(
            _get_project_stats,
            project)

        return ProjectStatsMessage(**items)

    @greenday_method(
        ProjectIDContainer,
        DistinctChannelListResponse,
        path='project/{project_id}/distinct_channels',
        http_method='GET',
        name='distinct_channels',
        pre_middlewares=[auth_required])
    def get_distinct_channels(self, request):
        """
            Gets a distinct list of channels from videos in this project
        """
        project = self.get_project(
            request.project_id, assigned_only=True
        )

        def _get_project_distinct_channels(project):
            return {
                o['channel_id']: o['channel_name']
                for o in (
                    YouTubeVideo.objects
                    .filter(projectvideos__project=project)
                    .values('channel_id', 'channel_name')
                    .distinct()
                )
            }
        channels = cache_manager.get_or_set(
            _get_project_distinct_channels,
            project)

        return DistinctChannelListResponse(
            items=[
                DistinctChannelMessage(
                    id=channel_id,
                    name=channel_name)
                for channel_id, channel_name in channels.items()],
            is_list=True
        )

    def _get_image_url(self, image_gcs_filename):
        """
            Takes the filename of an image stored in Cloud Storage
            and calls the images API to serve it from there.

            Returns the images API serving URL

            No longer used.
        """
        if settings.TESTING or not settings.DEBUG:
            if image_gcs_filename:
                return get_gcs_image_serving_url(
                    image_gcs_filename)
        else:
            # Little local dev hack. We're using the Images API with GCS.
            # This doesn't work locally so instead we pass the image dataUri
            # and use it directly
            return image_gcs_filename

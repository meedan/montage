"""
    The user API
"""
import endpoints
from protorpc import message_types

from django.contrib.auth import get_user_model
from django.db.models import Q

from greenday_core.api_exceptions import ForbiddenException
from greenday_core.constants import EventKind
from greenday_core.memoize_cache import cache_manager
from greenday_core.models import get_sentinel_user
from greenday_core.user_deletion import defer_delete_user

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_superuser,
    auth_required
)
from ..mapper import GeneralMapper
from ..utils import (
    get_obj_or_api_404,
    update_object_from_request,
    api_appevent
)

from .messages import (
    UserResponseMessage,
    UserResponseBasic,
    UserListResponse,
    UserStatsResponse,
)

from .containers import (
    UserFilterContainer,
    UserCreateContainer,
    UserUpdateContainer,
    CurrentUserUpdateContainer,
)


@greenday_api.api_class(
    resource_name='user', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class UserAPI(BaseAPI):
    """
        API for Users

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        """
            Creates the user API
        """
        super(UserAPI, self).__init__(*args, **kwargs)

        User = get_user_model()
        self.mapper = GeneralMapper(
            User, UserResponseMessage)
        self.basic_mapper = GeneralMapper(
            User, UserResponseBasic)

    @greenday_method(message_types.VoidMessage, UserResponseMessage,
                      path='users/me', http_method='GET', name='current_user',
                      pre_middlewares=[auth_required])
    def get_current_user(self, request):
        """ Gets the current user """
        return self.mapper.map(self.current_user)

    @greenday_method(CurrentUserUpdateContainer, UserResponseMessage,
                      path='users/me',
                      http_method='PUT',
                      name='current_user_update',
                      pre_middlewares=[auth_required])
    def update_current_user(self, request):
        """ Updates the current user """
        user = self.current_user
        update_object_from_request(request, user)
        return self.mapper.map(user)

    @greenday_method(
        message_types.VoidMessage, message_types.VoidMessage, path='users/me',
        http_method='DELETE', name='current_user_delete',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.USERDELETED, id_getter=lambda s, req: s.current_user.pk,
        user_getter=lambda s, req: get_sentinel_user())
    def delete_current_user(self, request):
        """
            API endpoint to delete a the current user along with all their
            content and anything built on top of their content.
        """
        defer_delete_user(self.current_user)
        return message_types.VoidMessage()

    @greenday_method(UserFilterContainer, UserListResponse,
                      path='users', http_method='GET', name='list',
                      pre_middlewares=[auth_required])
    def users_filter(self, request):
        """
            Searches the application's users

            Super users can list all users
        """
        User = get_user_model()
        # TODO: consider indexing users instead of doing these complex queries
        if request.q:
            # Since we don't have a full_name field we can filter on,
            # we have to split the filter query in multiple words and
            # then intersect all the results, in order to support filters
            # like 'FirstName LastName'
            words = request.q.split(' ')
            users = []
            for word in words:
                # Create a list of lists with the results for each word in the
                # query
                users.append(
                    list(
                        User.objects
                        .filter(
                            Q(first_name__icontains=word) |
                            Q(last_name__icontains=word) |
                            Q(email__icontains=word)
                        )
                    )
                )

            users = set(users[0]).intersection(*users)
        else:
            if not self.current_user.is_superuser:
                raise ForbiddenException

            users = list(User.objects.all())

        return UserListResponse(items=map(self.basic_mapper.map, users), is_list=True)

    @greenday_method(UserCreateContainer, UserResponseMessage, path='users',
                      http_method='POST', name='create',
                      pre_middlewares=[auth_superuser])
    @api_appevent(
        EventKind.USERCREATED,
        id_getter_post=lambda s, req, res: res.id)
    def users_create(self, request):
        """
            Creates a new user

            Super users only
        """

        # TODO: review the user invite flow
        user, created = get_user_model().objects.get_or_create(
            email=request.email,
            defaults={
                'username': request.email,
                'is_active': False
            }
        )

        subject = "Montage Invitation"
        message = """You've been invited to join Montage
 https://montage.meedan.com"""
        from greenday_core.utils import send_email
        send_email(subject, message, [request.email])

        return self.mapper.map(user)

    @greenday_method(
        UserUpdateContainer, UserResponseMessage, path='users/{id}',
        http_method='PUT', name='users_update',
        pre_middlewares=[auth_superuser])
    @api_appevent(
        EventKind.USERUPDATED, id_getter=lambda s, req: req.id)
    def users_update(self, request):
        """
            Updates a user

            Super users only
        """
        user = get_obj_or_api_404(get_user_model(), pk=request.id)
        update_object_from_request(request, user)

        return self.mapper.map(user)

    @greenday_method(
        message_types.VoidMessage, UserResponseMessage, path='users/nda',
        http_method='POST', name='accept_nda',
        pre_middlewares=[auth_required])
    @api_appevent(
        EventKind.USERACCEPTEDNDA, id_getter=lambda s, req: s.current_user.pk)
    def users_accept_nda(self, request):
        """
            Records the User has having accepted the NDA
        """
        user = self.current_user
        user.accepted_nda = True
        user.save()
        return self.mapper.map(user)

    @greenday_method(
        message_types.VoidMessage, UserStatsResponse,
        path='users/me/stats',
        http_method='GET',
        name='current_user_stats',
        pre_middlewares=[auth_required])
    def get_current_user_stats(self, request):
        """
            Gets the application stats for the current user
        """
        def _get_current_user_stats(user):
            videos_watched = (
                user.related_videos
                .filter(watched=True)
                .count()
            )

            return UserStatsResponse(
                id=user.id,
                videos_watched=videos_watched,
                tags_added=user.owner_of_tag_instances.count()
            )

        return cache_manager.get_or_set(
            _get_current_user_stats,
            self.current_user,
            message_type=UserStatsResponse)

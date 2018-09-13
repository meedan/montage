"""
    Defines Montage's Cloud Endpoints API

    Contains a custom version of the method decorator
    used to endpoints to wrap a method and make it
    invokable by the remote framework.

    Defines middleware methods which can be attached to
    API methods

    Creates the endpoints API handler and assigns to the
    `greenday_api.api` module attribute

    Recursively imports all *._api modules so that all API
    classes are made serveable.
"""
import endpoints
import os
from protorpc import remote
from protorpc import messages, message_types
from endpoints.api_config import (
    _MethodInfo, _CheckEnum, _CheckType)
import endpoints.util as endpoints_util
from django.conf import settings

from greenday_core.api_exceptions import (
    ForbiddenException,
    UnauthorizedException
)
from .utils import get_current_user

# Valid client IDs from the Google API Console
CLIENT_IDS = [
    settings.OAUTH_SETTINGS['client_id'],
    endpoints.API_EXPLORER_CLIENT_ID
]


greenday_api = endpoints.api(
    name='greenday', version='v1',
    description='Montage API',
    allowed_client_ids=CLIENT_IDS,
    audiences=[settings.OAUTH_SETTINGS['client_id']]
)


def auth_required(api_instance, request):
    """
        API method middleware to enforce that a user is authed
    """
    if not api_instance.current_user:
        raise UnauthorizedException


def auth_superuser(api_instance, request):
    """
        API method middleware to ensure that the current user is a
        super user
    """
    if not api_instance.current_user:
        raise UnauthorizedException

    if not api_instance.current_user.is_superuser:
        raise ForbiddenException


def add_order_to_repeated(api_instance, request, response):
    """
        Given a list of fields where each item has an "order" attribute
        this will assign the index of the item in the list to the order
        attribute
    """
    def _add_order_to_repeated(message):
        for field in message.all_fields():
            if field.repeated:
                for i, value in enumerate(
                        message.get_assigned_value(field.name)):
                    if hasattr(value, 'order'):
                        value.order = i

                    if isinstance(value, messages.Message):
                        _add_order_to_repeated(value)

    _add_order_to_repeated(response)


class BaseAPI(remote.Service):
    """
        A base class for all APIs
    """
    @property
    def current_user(self):
        """ Gets the current user and caches onto the API object """
        if not hasattr(self, '_user'):
            self._user = get_current_user()

        return self._user


class GreendayMethodDecorator(object):
    """
        Our API method decorator - wraps the endpoints one so that we can add
        some extra generic behaviour

        See endpoints.api_config.method() for the code this is based on
    """
    def __init__(
            self,
            request_message=message_types.VoidMessage,
            response_message=message_types.VoidMessage,
            name=None,
            path=None,
            http_method='POST',
            cache_control=None,
            scopes=None,
            audiences=None,
            allowed_client_ids=None,
            auth_level=None,
            pre_middlewares=None,
            post_middlewares=None,
            error_middlewares=None):
        self.request_message = request_message
        self.response_message = response_message
        self.name = name
        self.path = path
        self.http_method = http_method
        self.cache_control = cache_control
        self.scopes = scopes
        self.audiences = audiences
        self.allowed_client_ids = allowed_client_ids
        self.auth_level = auth_level
        self.pre_middlewares = pre_middlewares or []
        self.post_middlewares = post_middlewares or []
        self.error_middlewares = error_middlewares or []

        endpoints_util.check_list_type(scopes, basestring, 'scopes')
        endpoints_util.check_list_type(audiences, basestring, 'audiences')
        endpoints_util.check_list_type(allowed_client_ids, basestring, 'allowed_client_ids')
        _CheckEnum(auth_level, endpoints.AUTH_LEVEL, 'auth_level')

    def check_type(self, setting, allowed_type, name, allow_none=True):
        if (setting is None and allow_none or
                isinstance(setting, allowed_type)):
            return setting
        raise TypeError('%s is not of type %s' % (name, allowed_type.__name__))

    def __call__(self, api_method):
        # Append the API path to the docstring
        if api_method.__doc__ is None:
            api_method.__doc__ = ""
        api_method.__doc__ += " ( /{0} )".format(
            self.path or api_method.__name__)

        if isinstance(self.request_message, endpoints.ResourceContainer):
            remote_decorator = remote.method(
                self.request_message.combined_message_class,
                self.response_message)
        else:
            remote_decorator = remote.method(self.request_message,
                self.response_message)

        remote_method = remote_decorator(api_method)

        def invoke_remote(service_instance, request):
            endpoints.users_id_token._maybe_set_current_user_vars(
                invoke_remote,
                api_info=getattr(service_instance, 'api_info', None),
                request=request)

            try:
                for middleware in self.pre_middlewares:
                    resp = middleware(service_instance, request)
                    if resp:
                        return resp

                response = remote_method(service_instance, request)

                for middleware in self.post_middlewares:
                    resp = middleware(service_instance, request, response)
                    if resp:
                        response = resp

                return response
            except Exception as e:
                for middleware in self.error_middlewares:
                    resp = middleware(service_instance, request, e)
                    if resp:
                        return resp
                raise

        invoke_remote.remote = remote_method.remote
        if isinstance(self.request_message, endpoints.ResourceContainer):
            endpoints.ResourceContainer.add_to_cache(
                invoke_remote.remote, self.request_message)

        invoke_remote.method_info = _MethodInfo(
            name=self.name or api_method.__name__,
            path=self.path or api_method.__name__,
            http_method=self.http_method or "POST",
            scopes=self.scopes, audiences=self.audiences,
            allowed_client_ids=self.allowed_client_ids,
            auth_level=self.auth_level)
        invoke_remote.method_info.relative_path = self.path
        invoke_remote.api_method = api_method

        invoke_remote.__name__ = invoke_remote.method_info.name
        invoke_remote.__doc__ = api_method.__doc__  # for sphinx docs
        return invoke_remote

greenday_method = GreendayMethodDecorator

# import all *_api.py modules
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    package = root.split('/')[-1]
    if package == "tests":
        # don't import tests package
        continue
    for module in files:
        if module != "django_api.py" and module.endswith('_api.py'):
            __import__("{0}.{1}".format(package, module[:-3]),
                       locals(),
                       globals()
                       )
    if files:
        del module

import greenday_channel.endpoints_api.api

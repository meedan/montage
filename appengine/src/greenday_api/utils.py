"""
    Defines utilities used throughout the `greenday_api` package
"""
import endpoints
import json
import urllib
import urllib2
from endpoints.protojson import EndpointsProtoJson
from protorpc import messages
from google.appengine.api import users
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.fields import FieldDoesNotExist
from django.db.models import QuerySet

from greenday_core.api_exceptions import (
    UnauthorizedException, ForbiddenException, NotFoundException)
from greenday_core.eventbus import appevent


def get_current_user(silent=False):
    """
    Gets the greenday user from the OAuthed user's email.

    Pass silent=True to return None if the request is not oauthed or the user
    does not exist in greenday
    """
    if settings.DEBUG and settings.USERS_API_AUTH:
        email = users.get_current_user().email()
    else:
        try:
            current_user = endpoints.get_current_user()
        except endpoints.InvalidGetUserCall:
            current_user = None

        if current_user is None:
            if not silent:
                raise UnauthorizedException('Invalid or missing token.')
        else:
            email = current_user.email()

    User = get_user_model()
    try:
        return User.objects.get(
            email=email)
    except User.DoesNotExist:
        user, created = get_user_model().objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'is_active': True
            }
        )
        return user
        # we can't create a user here because we need their GAIA ID
        # if not silent:
        #     raise ForbiddenException(
        #         "User '%s' doesn't exist in Montage" %
        #         email)


def get_obj_or_api_404(model_class_or_queryset, **lookups):
    """
        Gets a object as per args in lookups dict.

        Can use either a model or a queryset to query on
    """
    if isinstance(model_class_or_queryset, QuerySet):
        qs = model_class_or_queryset
        model_class = model_class_or_queryset.model
    else:
        qs = model_class_or_queryset.objects
        model_class = model_class_or_queryset

    try:
        return qs.get(**lookups)

    except model_class.DoesNotExist:
        raise NotFoundException(
            "{0} instance with {1} not found".format(
                model_class.__name__, str(lookups)))


def get_foreign_key_objects(model_class, pks):
    """ Helper function for parsing a list of primary keys and
        returning the actual instances.

        Raises a comprehensible exception if an instance doesn't exist.
    """
    for pk in pks:
        try:
            yield model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            raise NotFoundException(
                "{0} with pk={1} not found".format(
                    model_class.__name__, pk))


def update_object_from_request(request, obj):
    """
        Iterates through all fields in the request message and
        tries to update the given object with their values
    """
    model_field_names = [
        f.name for f in obj.__class__._meta.fields]

    for field in request.all_fields():
        if field.name == 'id' or field.name not in model_field_names:
            continue
        value = getattr(request, field.name)
        # Skip this field if it's not an actual attribute on the object or
        # if we're trying to assign a None value to a non-nullable field
        if (not hasattr(obj, field.name) or
            (value is None and
                not is_field_nullable(obj.__class__, field.name)
             ) or field.name.endswith('_id')):
            continue
        setattr(obj, field.name, value)

    if hasattr(obj, 'validate'):
        obj.validate()
    obj.save()


def patch_object_from_request(request, obj):
    """
        Iterates through all fields in the request message which are not None
        and updates the object with their values
    """
    model_field_names = [
        f.name for f in obj.__class__._meta.fields]

    for field in request.all_fields():
        if field.name == 'id' or field.name not in model_field_names:
            continue
        value = getattr(request, field.name)
        if (
                value is None or
                not hasattr(obj, field.name) or
                field.name.endswith('_id')):
            continue

        setattr(obj, field.name, value)

    if hasattr(obj, 'validate'):
        obj.validate()
    obj.save()


def is_field_nullable(model_class, field_name):
    """ Helper function that checks if a field is nullable or not.
        It also handles the case of foreign key fields with the '_id' suffix
    """
    try:
        return model_class._meta.get_field(field_name).null
    except FieldDoesNotExist:
        # Make sure it's not foreign key
        if field_name.endswith('_id'):
            return model_class._meta.get_field(field_name[:-3]).null
        raise


def api_appevent(*args, **kwargs):
    """
        Wraps @appevent to record the API current_user property.
        Allows developer to override with passed user_getter if need be.
    """
    user_getter = kwargs.get('user_getter', None)
    if user_getter:
        return appevent(*args, **kwargs)
    return appevent(user_getter=lambda s, req: s.current_user, *args, **kwargs)


class MessageJSONEncoder(json.JSONEncoder):
    """
        Encodes ProtoRPC messages

        Based on the encoder in protojson.py
    """
    def __init__(self, protojson_protocol=None, **kwargs):
        super(MessageJSONEncoder, self).__init__(**kwargs)
        self.__protojson_protocol = protojson_protocol or EndpointsProtoJson.get_default()

    def default(self, value):
        if isinstance(value, messages.Enum):
            return str(value)

        if isinstance(value, messages.Message):
            result = {}
            for field in value.all_fields():
                item = value.get_assigned_value(field.name)

                if item not in (None, [], ()):
                    result[field.name] = self.__protojson_protocol.encode_field(
                        field, item)
                else:
                    # the normal serializer doesn't output falsey values
                    result[field.name] = item

            # Handle unrecognized fields, so they're included when a message is
            # decoded then encoded.
            for unknown_key in value.all_unrecognized_fields():
                unrecognized_field, _ = value.get_unrecognized_field_info(unknown_key)
                result[unknown_key] = unrecognized_field
            return result
        else:
            return super(MessageJSONEncoder, self).default(value)

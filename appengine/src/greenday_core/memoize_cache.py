"""
    Defines a cache manager
"""
import hashlib
import logging
import types

from protorpc.protojson import decode_message, encode_message

from google.appengine.api.app_identity import get_application_id
from django.db import models
from django.core.cache import caches
from django.conf import settings


class MemoiseCacheManager(object):
    """
        A basic caching manager designed to encapsulate caching
        function calls

        This wraps Django's cache backend

        This object is intended to be kept alive across requests
    """
    def __init__(self, default_timeout=None):
        """
            Creates the manager
        """
        self.cache = caches['default']

        try:
            self.version = get_application_id()
        except AttributeError:
            # this fails on local dev
            self.version = ''

        self.default_timeout = (
            settings.MEMOISE_CACHE_TIMEOUT
            if default_timeout is None
            else default_timeout
        )

    def get_or_set(self, fn, *args, **kwargs):
        """
            Wraps `fn` and caches the response

            Cache key varys by all *args and **kwargs
        """
        timeout = kwargs.pop("timeout", None)
        message_type = kwargs.pop("message_type", None)
        key = self.create_key(fn, args, kwargs)

        obj = self.get_by_key(key, message_type=message_type)

        if obj is None:
            obj = fn(*args, **kwargs)
            self.add_by_key(
                key, obj, timeout=timeout, message_type=message_type)

        return obj

    def get(self, fn, *args, **kwargs):
        """
            Get cached response of calling fn(*args, **kwargs)

            Returns None if response is not cached
        """
        message_type = kwargs.pop("message_type", None)

        key = self.create_key(fn, args, kwargs)
        return self.get_by_key(key, message_type=message_type)

    def get_by_key(self, key, message_type=None):
        """
            Gets cached response by the cache key

            Decodes protorpc messages
        """
        obj = self.cache.get(key, version=self.version)

        if obj is not None and message_type:
            return decode_message(message_type, obj)

        return obj

    def add(self, fn, *args, **kwargs):
        """
            Calls fn(*args, **kwargs) and caches the response

            Returns the result of the cache set call
        """
        timeout = kwargs.pop("timeout", None)
        message_type = kwargs.pop("message_type", None)

        key = self.create_key(fn, args, kwargs)

        obj = fn(*args, **kwargs)
        return self.add_by_key(
            key, obj, timeout=timeout, message_type=message_type)

    def add_by_key(self, key, obj, timeout=None, message_type=None):
        """
            Adds a value to the cache

            Encodes protorpc messages
        """
        if timeout is None:
            timeout = self.default_timeout

        if message_type:
            obj = encode_message(obj)

        try:
            return self.cache.add(key, obj, version=self.version, timeout=timeout)
        except ValueError as e:
            # might have exceeded the key/value memcache size limit
            logging.debug(e)

    def delete(self, fn, *args, **kwargs):
        """
            Removes the result of calling fn(*args, **kwargs) from the cache
        """
        key = self.create_key(fn, args, kwargs)
        return self.delete_by_key(key)

    def delete_many(self, *calls):
        """
            Removes multiple cache entries

            delete_many(
                ("_my_func", "arg1", {"foo": "bar"}),
                ("_my_func", "arg2", {"foo": "bar"}),
            )
        """
        keys = [self.create_key(*c) for c in calls]
        return self.delete_many_by_key(keys)

    def delete_by_key(self, key):
        """
            Deletes the given key from the cache
        """
        return self.cache.delete(key, version=self.version)

    def delete_many_by_key(self, keys):
        """
            Deletes list of keys from cache
        """
        return self.cache.delete_many(keys, version=self.version)

    @classmethod
    def create_key(cls, fn, args, kwargs):
        """
            Creates a cache key for the given function and its arguments
        """
        args = map(cls.sanitise_arg_for_key, args)
        kwargs = {k: cls.sanitise_arg_for_key(v) for k, v in kwargs.items()}

        if isinstance(fn, basestring):
            fn_repr = fn
        else:
            fn_repr = _get_func_repr(fn)

        query_key = u'{fn_repr}{args}{kwargs}'.format(
            fn_repr=fn_repr,
            args=unicode(args),
            kwargs=unicode(kwargs))

        return hashlib.md5(query_key).hexdigest()

    @classmethod
    def sanitise_arg_for_key(cls, arg):
        """
            Converts an arg to a value which can be used as part of a cache key
        """
        if isinstance(arg, models.Model):
            return _django_model_repr(arg)

        if isinstance(arg, models.QuerySet):
            return map(_django_model_repr, arg)

        return arg

cache_manager = MemoiseCacheManager()


def _django_model_repr(obj):
    """
        Gets a string uniquely representing a Django model
    """
    return u'<{0}: {1}>'.format(obj.__class__.__name__, obj.pk)


def _get_func_repr(func):
    """
        Gets a string representing a function object
    """
    if isinstance(func, types.MethodType):
        return "{cls}.{func}".format(
            cls=func.im_self.__class__,
            func=func.im_func.__name__
        )
    elif isinstance(func, types.BuiltinMethodType):
        if not func.__self__:
            return "{func}".format(
                func=func.__name__
            )
        else:
            return "{type}.{func}".format(
                type=func.__self__,
                func=func.__name__
            )
    elif (isinstance(func, types.ObjectType) and hasattr(func, "__call__")) or\
        isinstance(func, (types.FunctionType, types.BuiltinFunctionType,
                        types.ClassType, types.UnboundMethodType)):
        return "{module}.{func}".format(
            module=func.__module__,
            func=func.__name__
        )
    else:
        raise ValueError("func must be callable")

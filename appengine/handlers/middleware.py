import logging

from django.conf import settings
from django.db import connection
from django.db.backends import utils
from google.appengine.ext.appstats import recording

import django.core.signals as signals
from greenday_core.utils import log_sql_queries_to_console, AppstatsCursorDebugWrapper


def django_setup_teardown(f):
    """
        Database connections are opened on demand in Django, but need to be
        closed explicitly. This is done by sending a `request_finished`
        signal in Django's default WSGI handler.

        App Engine's built-in handlers don't normally trigger the signals -
        wrap them with this decorator to prevent leaking open DB connections.

        http://code.google.com/p/googleappengine/issues/detail?id=10118
    """
    def wrapper(*args, **kwargs):
        signals.request_started.send(sender=f)
        try:
            return f(*args, **kwargs)
        finally:
            signals.request_finished.send(sender=f)
    return wrapper


def error_logging_middleware(f):
    """
        Logs all exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
            raise
    return wrapper


def endpoints_debug_middleware(f):
    """
        endpoints debug decorator. This enables us to profile
        google endpoints SQL queries. We cant do this using standard
        middleware since these ULRs are not handled by Django.
        Data is only printed to the console if DEBUG = True.
    """
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        finally:
            if settings.LOG_SQL_TO_CONSOLE:
                log_sql_queries_to_console(args[0].get('PATH_INFO'))
    return wrapper

def appstats_db_conn_middleware(f):
    def wrapper(*args, **kwargs):
        recorder = recording.recorder_proxy

        if recorder.has_recorder_for_current_request():
            old_force_debug_cursor = connection.force_debug_cursor
            connection.force_debug_cursor = True

            OldCursorDebugWrapper = utils.CursorDebugWrapper
            utils.CursorDebugWrapper = AppstatsCursorDebugWrapper

        try:
            return f(*args, **kwargs)
        finally:
            if recorder.has_recorder_for_current_request():
                utils.CursorDebugWrapper = OldCursorDebugWrapper
                connection.force_debug_cursor = old_force_debug_cursor
    return wrapper

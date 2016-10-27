# Google Cloud Endpoints / API
from __future__ import absolute_import

import endpoints
import os

import fix_paths

from google.appengine.ext.appstats import recording

from greenday_core.utils import get_settings_name
os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_settings_name())

import django
django.setup()

from greenday_api.api import greenday_api

from .middleware import (
    endpoints_debug_middleware,
    django_setup_teardown,
    appstats_db_conn_middleware
)

server_fn = endpoints.api_server(
    [greenday_api],
    restricted=False)


@recording.appstats_wsgi_middleware
@appstats_db_conn_middleware
@django_setup_teardown
@endpoints_debug_middleware
def application(*args, **kwargs):
    return server_fn(*args, **kwargs)

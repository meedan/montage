import fix_paths
from django.core.wsgi import get_wsgi_application
from greenday_core.utils import get_settings_name
from urllib import quote
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_settings_name())

from .middleware import error_logging_middleware

_application = error_logging_middleware(get_wsgi_application())

def reconstruct(environ, server_name):
  # https://www.python.org/dev/peps/pep-0333/#url-reconstruction
  url = environ['wsgi.url_scheme']+'://'

  url += server_name

  url += quote(environ.get('SCRIPT_NAME', ''))
  url += quote(environ.get('PATH_INFO', ''))
  if environ.get('QUERY_STRING'):
    url += '?' + environ['QUERY_STRING']

  return url

def application(environ, start_response):
  # hard-redirect 'montage.storyful.com' to 'montage.meedan.com'
  if environ['SERVER_NAME'] == 'montage.storyful.com':
    start_response('301 Redirect', [
      ('Location', reconstruct(environ, 'montage.meedan.com')),
    ])
    return []

  return _application(environ, start_response)

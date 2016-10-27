"""
    Base settings for Django.

    Imported by all environment-specific settings modules
"""
import os
from google.appengine.api import app_identity, modules
from google.appengine.ext import ndb

class Secrets(ndb.Model):
  name = ndb.StringProperty()
  value = ndb.StringProperty()

  @staticmethod
  def get(name):
    NOT_SET_VALUE = "NOT SET"
    retval = Secrets.query(Secrets.name == name).get()
    if not retval:
      retval = Secrets()
      retval.name = name
      retval.value = NOT_SET_VALUE
      retval.put()
    if retval.value == NOT_SET_VALUE:
      raise Exception(('Setting %s not found in the database. A placeholder ' +
        'record has been created. Go to the Developers Console for your app ' +
        'in App Engine, look up the Settings record with name=%s and enter ' +
        'its value in that record\'s value field.') % (name, name))
    return retval.value

APPENGINE_PRODUCTION = os.getenv('SERVER_SOFTWARE', '').startswith(
    'Google App Engine')
HTTP_HOST = os.environ.get('HTTP_HOST')

SRC_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
APPENGINE_DIR = os.path.abspath(os.path.dirname(SRC_DIR))
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(APPENGINE_DIR)))

INTERNAL_IPS = (
    '127.0.0.1',
    'localhost',
    '::1'
)

DEBUG = not APPENGINE_PRODUCTION

TESTING = False

try:
    APP_ID = app_identity.get_application_id()
    HOME_LINK = app_identity.get_default_version_hostname()
    GCS_BUCKET = app_identity.get_default_gcs_bucket_name()
    CURRENT_VERSION = modules.get_current_version_name()
    CURRENT_MODULE = modules.get_current_module_name()
except AttributeError:
    APP_ID = 'greenday-project-v02-local'
    HOME_LINK = 'http://localhost:8080/'
    GCS_BUCKET = 'greenday-project-v02-local.appspot.com'
    CURRENT_VERSION = 'local'
    CURRENT_MODULE = ''

ALLOWED_HOSTS = [  # Django 1.5 requirement when DEBUG = False
    "localhost",
    "montage.storyful.com",
    app_identity.get_default_version_hostname(),

    # non-default versions
    "{0}.{1}".format(CURRENT_VERSION, HOME_LINK),
    "{0}-dot-{1}".format(CURRENT_VERSION, HOME_LINK),

    # modules
    "{0}.{1}".format(CURRENT_MODULE, HOME_LINK),
    "{0}-dot-{1}".format(CURRENT_MODULE, HOME_LINK),
    "{0}.{1}.{2}".format(CURRENT_VERSION, CURRENT_MODULE, HOME_LINK),
    "{0}-dot-{1}-dot-{2}".format(CURRENT_VERSION, CURRENT_MODULE, HOME_LINK),
]

import logging
logging.info(ALLOWED_HOSTS)

TEMPLATE_DEBUG = not APPENGINE_PRODUCTION

SOUTH_DATABASE_ADAPTERS = {
    'default': "south.db.mysql"
}

OAUTH_SETTINGS = {}
ENVS = {
    'LOCAL': 0,
    'STAGING': 1,
    'PROD': 2,
    'POTATO': 3
}

TIME_ZONE = 'Europe/London'
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = False
USE_TZ = True

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)


MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',

    # for admin only
    'django.contrib.sessions.middleware.SessionMiddleware',
    'greenday_core.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'djangosecure.middleware.SecurityMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.media",
    "django.core.context_processors.static",

    # for admin only
    "django.contrib.messages.context_processors.messages",
)

ROOT_URLCONF = 'greenday_core.urls'

INSTALLED_APPS = (
    # Django
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'django.contrib.contenttypes',

    # For admin only
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.admin',

    # Libs
    'treebeard',
    'search',

    # Montage apps
    'greenday_core',
    'greenday_api',
    'greenday_public',
    'greenday_admin',
)

STATIC_DIRNAME = 'static' if APPENGINE_PRODUCTION else 'static-dev'
STATIC_URL = '/%s/' % STATIC_DIRNAME
STATIC_ROOT = os.path.join(APPENGINE_DIR, 'greenday_public', STATIC_DIRNAME)

DEFAULT_CACHE_TIMEOUT = 60 * 60 * 24 * 365  # One year

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'TIMEOUT': DEFAULT_CACHE_TIMEOUT,
    }
}

MEMOISE_CACHE_TIMEOUT = 60

AUTH_USER_MODEL = 'greenday_core.User'

OAUTH_FAILED_REDIRECT = 'access_denied'

SEARCH_INDEXING = True

EMAIL_SENDING = True
LOG_SQL_TO_CONSOLE = DEBUG
USERS_API_AUTH = False  # only works with DEBUG=True

CHANNELS_API_BASE = "//long-poller-dot-{0}/_ah/api/greenday/v1/channels".format(
    HOME_LINK)
API_BASE = "{0}://{1}/_ah/api/greenday/v1".format(
    'http' if DEBUG else 'https',
    HOME_LINK
)


SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

X_FRAME_OPTIONS = 'DENY'

CSP_DEFAULT_SRC = (
    "'self'",
    "https://ssl.gstatic.com",
    "https://apis.google.com",
)

CSP_FONT_SRC = (
    "'self'",
    "fonts.gstatic.com"
)

CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "*.googleapis.com",
    "https://apis.google.com",
    "https://accounts.google.com",
    "https://maps.gstatic.com",
    "https://www.youtube.com",
    "*.ytimg.com",

    # Analytics / GTM
    "https://www.google.com",
    "https://www.google-analytics.com",
    "https://www.googletagmanager.com",
    "https://www.googleadservices.com",
    "cdn.heapanalytics.com",
)

CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    # Analytics / GTM
    "https://www.google.com",
    "https://fonts.googleapis.com",
)

CSP_FRAME_SRC = (
    "'self'",
    "*.googleapis.com",
    "*.google.com",
    "*.youtube.com",
)

CSP_IMG_SRC = (
    "'self'",
    "*.ytimg.com",
    "*.ggpht.com",
    "*.googleusercontent.com",
    "*.googleapis.com",
    "*.gstatic.com",
    "*.youtube.com",
    "https://www.google-analytics.com",
    "heapanalytics.com",
)

CSP_CONNECT_SRC = (
    "'self'",
    HOME_LINK,
    "long-poller-dot-{0}".format(HOME_LINK),
)

if DEBUG:
    CSP_IMG_SRC += ("'unsafe-inline'", "data:")
    CSP_CONNECT_SRC += ('localhost:8082',)

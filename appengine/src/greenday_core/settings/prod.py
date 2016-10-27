"""
    Django settings for production environment
"""
from .base import *

ENVIRONMENT = ENVS['PROD']

# Running in development, so use a local MySQL database.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '/cloudsql/greenday-project:v2',
        'NAME': 'greenday',
        'USER': 'root',
        'OPTIONS': {
            'init_command': 'SET storage_engine=INNODB',
        },
    }
}

ANALYTICS_ID = Secrets.get('BASE_ANALYTICS_ID')

# If we're connecting remotely, we need to update the settings
APPENGINE_PRODUCTION = (
    os.getenv('SERVER_SOFTWARE', '')
    .startswith('Google App Engine')
)
if not APPENGINE_PRODUCTION:
    DATABASES['default']['HOST'] = Secrets.get('PROD_DB_HOST')
    DATABASES['default']['OPTIONS']['read_default_file'] = \
        os.path.join(ROOT_DIR, 'keys', 'prod', 'mysql.cfg')

OAUTH_SETTINGS['client_id'] = Secrets.get('PROD_OAUTH_CLIENT_ID')
OAUTH_SETTINGS['api_key'] = Secrets.get('PROD_OAUTH_API_KEY')

SECRET_KEY = Secrets.get('SECRET_KEY')
"""
    Django settings for unit tests

    Imports settings from local dev environment
"""
from .local import *
import os

import logging

# disable logging for test runs. It drives me insane, is ugly as hell and
# makes it very difficult to work with PDB and print statements. :-)
logging.disable(logging.CRITICAL)

TESTING = True
EMAIL_SENDING = False

REPORTS_DIR = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), '../../../reports/')

# nose, coverage and xunit settings
# Please see .coveragerc file for coverage ommissions.
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '-s', '--nologcapture',
    '--with-coverage',
    '--cover-package=greenday_api',
    '--cover-package=greenday_core',
    '--cover-package=greenday_public',
    '--cover-package=greenday_channel',
    '--testmatch=^test',
    '--exclude=migrations$',
    '--cover-xml',
    '--cover-xml-file=%s' % os.path.join(
        REPORTS_DIR, 'coverage.xml'),
    '--with-xunit',
    '--xunit-file=%s' % os.path.join(
        REPORTS_DIR, 'xunit.xml'),
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'NAME': 'greenday',
        'USER': 'root',
        'OPTIONS': {
            'init_command': 'SET default_storage_engine=INNODB',
        },
    }
}

ANALYTICS_ID = 'test'

OAUTH_SETTINGS['client_id'] = 'test'
OAUTH_SETTINGS['api_key'] = 'test'
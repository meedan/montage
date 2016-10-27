#!/usr/bin/env python
import os
import sys
from django.conf import settings

DIRNAME = os.path.dirname(__file__)
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'ATOMIC_REQUESTS': True,
        }
    },
    INSTALLED_APPS=(
        'django_protorpc',
    ),
    MIDDLEWARE_CLASSES=()  # suppress warning
)

import django
django.setup()

from django.test.runner import DiscoverRunner
test_runner = DiscoverRunner(verbosity=1)
failures = test_runner.run_tests(['django_protorpc', ])
if failures:
    sys.exit(failures)

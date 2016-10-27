from __future__ import absolute_import
import os

import fix_paths

from greenday_core.utils import get_settings_name
os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_settings_name())

import django
django.setup()

from deferred_manager.handler import application as deferred_manager_app

from .middleware import django_setup_teardown

application = django_setup_teardown(deferred_manager_app)

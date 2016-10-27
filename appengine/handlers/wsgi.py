import fix_paths
from django.core.wsgi import get_wsgi_application
from greenday_core.utils import get_settings_name
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_settings_name())

from .middleware import error_logging_middleware

application = error_logging_middleware(get_wsgi_application())


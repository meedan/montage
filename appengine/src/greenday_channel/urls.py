"""
    Defines routes for Django to serve
"""
from django.conf.urls import url, patterns

from .views import (
    publish_event_task_handler
)

urlpatterns = patterns(
    '',
    url(
        r'^publish_event_task_handler/(?P<event_id>\d+)/$',
        publish_event_task_handler,
        name='publish_event_task'),
)

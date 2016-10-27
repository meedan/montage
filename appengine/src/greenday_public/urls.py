"""
    Defines Django routes
"""
# import django deps
from django.conf.urls import url, patterns, include

# import project deps
from .views import index_view, image_upload_view, yt_thumbnail_view, err_404_view
from .export_views import video_export_view, project_tag_export_view


export_patterns = patterns(
    '',
    url(
        r'^project/(?P<project_id>\d+)/videos/$',
        video_export_view,
        name='videos'),

    url(
        r'^project/(?P<project_id>\d+)/tags/$',
        project_tag_export_view,
        name='tags'),
)

urlpatterns = patterns(
    '',
    url(r'^image-upload/$', image_upload_view, name='image_upload'),

    url(r'^export/', include(export_patterns, namespace='export')),

    url(r'^yt-thumbnail/$', yt_thumbnail_view, name='yt_thumbnail'),

    url(r'^404/?$', err_404_view, name='404'),

    url(r'^.*$', index_view, name='index'),
)

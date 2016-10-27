"""
	Define Django routes
"""
from django.contrib import admin
from django.conf.urls import patterns, include, url
from django.conf import settings


# setup urls
urlpatterns = patterns(
    '',
    url(r'^_admin/', include(admin.site.urls)),
    url(r'^channel/', include('greenday_channel.urls', namespace='channel')),
    url(r'^admin/', include('greenday_admin.urls')),
    url(r'^api/', include('greenday_api.urls')),
    url(r'', include('greenday_public.urls')),
)

# if in debug mode let django handle the serving of static media.
if settings.DEBUG:  # pragma: nocover
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

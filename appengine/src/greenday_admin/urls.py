"""
    Defines routes for the admin app
"""
from django.conf.urls import url, patterns

from .utils import auto_patterns
from .views import keep_alive, user_list, delete_user, delete_pending_user, change_user_whitelist

# import modules with auto_views in them
import greenday_core.indexers
import greenday_core.youtube_client
import greenday_core.denormalisers


urlpatterns = auto_patterns(
    greenday_core.indexers,
    overview=True,
    prefix='search'
)

urlpatterns += auto_patterns(
    greenday_core.youtube_client,
    overview=True,
    prefix='yt_videos'
)

urlpatterns += auto_patterns(
    greenday_core.denormalisers,
    overview=True,
    prefix='denormalisers'
)

urlpatterns += patterns(
    '',
    url(r'^ka/?$', keep_alive, name='keep-alive'),
    url(r'^users/?$', user_list, name='user_management'),
    url(
        r'^users/delete_user/(?P<id>\d+)/$',
        delete_user,
        name='delete_user'),
    url(
        r'^users/delete_pending_user/(?P<id>\d+)/$',
        delete_pending_user,
        name='delete_pending_user'),
    url(
        r'^users/change_user_whitelist/(?P<id>\d+)/$',
        change_user_whitelist,
        name='change_user_whitelist')
)

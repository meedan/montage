"""
    Defines API to serve list of distinct YouTube channels across the application
"""
# FRAMEWORK
import endpoints
from protorpc import message_types

from greenday_core.memoize_cache import cache_manager
from greenday_core.models import YouTubeVideo

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required
)

from .messages import DistinctChannelListResponse, DistinctChannelMessage


@greenday_api.api_class(
    resource_name='distinct_channels', auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class DistinctChannelsAPI(BaseAPI):
    """
        API to get distinct channels

        Object disposed after request is completed.
    """
    @greenday_method(
        message_types.VoidMessage,
        DistinctChannelListResponse,
        path='distinct_channels',
        http_method='GET',
        name='all_distinct_channels',
        pre_middlewares=[auth_required])
    def get_distinct_channels(self, request):
        """
            Gets a distinct list of channels from videos in this project
        """

        def _get_distinct_channels():
            return {
                o['channel_id']: o['channel_name']
                for o in (
                    YouTubeVideo.objects
                    .values('channel_id', 'channel_name')
                    .distinct()
                )
            }

        channels = cache_manager.get_or_set(_get_distinct_channels)

        return DistinctChannelListResponse(
            items=[
                DistinctChannelMessage(
                    id=channel_id,
                    name=channel_name)
                for channel_id, channel_name in channels.items()],
            is_list=True
        )

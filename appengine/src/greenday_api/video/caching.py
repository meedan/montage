"""
    Video API caching utilities
"""
from greenday_core.memoize_cache import cache_manager

from .containers import VideoFilterContainer


def remove_video_list_cache(project):
    """
        Removes all cached keys for the video list
        for a given project.
    """
    fn_name = "greenday_api.video.video_api._video_list"

    cache_manager.delete_many(
        *[(
            fn_name,
            (VideoFilterContainer.combined_message_class(
                project_id=project.pk, archived=x),
            project), {})
        for x in (True, False, None)]
    )

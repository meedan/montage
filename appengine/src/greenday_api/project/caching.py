"""
    Project API caching utilities
"""

from greenday_core.memoize_cache import cache_manager


def remove_project_list_user_cache(user):
    """
        Deletes a given user's cache of their list of projects
    """
    fn_name = "greenday_api.project.project_api._project_list_user"

    cache_manager.delete_many(
        *[(fn_name, (user, x), {})
        for x in (True, False, None)]
    )

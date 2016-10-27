"""
    Django middleware classes
"""
# import project deps
from greenday_core.utils import log_sql_queries_to_console
from django.utils.functional import SimpleLazyObject

from greenday_public.auth_utils import auth_user


@auth_user
def get_user(request):
    """
        Get the current user
    """
    return request.user


# middleware to help us profile and optimise the app.
class DebugMiddleware(object):
    """
        Middle which wraps
        :func:`greenday_core.utils.log_sql_queries_to_console <greenday_core.utils.log_sql_queries_to_console>`
    """
    def process_response(self, request, response):
        """
            Process HTTP response
        """
        if response.status_code == 200:
            log_sql_queries_to_console(request.path)
        return response


class AuthenticationMiddleware(object):
    """
        Add a lazy reference to the current user onto the request object
    """
    def process_request(self, request):
        """
            Process HTTP response
        """
        request.user = SimpleLazyObject(lambda: get_user(request))

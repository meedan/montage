"""
    Functions to help decorate a method and make it callable via
    a URL and return a HTTP response
"""
import logging
from cStringIO import StringIO
from functools import wraps
from django.http import HttpResponse, HttpRequest

from .utils import redirect_logging
# The following is based on a SO answer found here: http://goo.gl/5xAeT


def auto_url(view):
    """Used in conjunction with `auto_patterns` to automatically generate URLs
    for views.
    """
    view.auto_url = True
    return view


def auto_response(view):
    """For the super lazy, decorate a view with this to automatically return
    a response.
    """
    @wraps(view)
    def wrapper(*args, **kwargs):
        if len(args) and isinstance(args[0], HttpRequest):
            request = args[0]
            kwargs = request.GET.dict()

            with redirect_logging(
                    StringIO(), log_level=logging.INFO) as redirect_ctx:
                view(**kwargs)
                redirect_ctx.flush()
                output = redirect_ctx.stream.getvalue()

            return HttpResponse(
                u"{0}View {1} finished".format(
                    output.replace('\n', '<br />'),
                    view.func_name))

        return view(*args, **kwargs)

    return wrapper


def auto_view(view):
    """
        Decorate a method and make it callable via
        a URL and return a HTTP response
    """
    return auto_url(auto_response(view))

import os
import sys
from google.appengine.api import apiproxy_stub_map
from google.appengine.api.taskqueue import taskqueue_stub
from google.appengine.api.search import simple_search_stub

import errno
import tempfile
import itertools
import getpass


def execute_from_command_line():
    _patch_deferred()

    # TODO: get app_id from app.yaml
    storage_path = _get_storage_path(None, "greenday-project-v02-dev")
    search_stub = simple_search_stub.SearchServiceStub(
        index_file=os.path.join(storage_path, 'search_indexes'))
    apiproxy_stub_map.apiproxy.RegisterStub('search', search_stub)

    from greenday_core.utils import get_settings_name
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_name())

    import django.core.management
    try:
        django.core.management.execute_from_command_line()
    finally:
        search_stub.Write()


def _generate_storage_paths(app_id):
    """Yield an infinite sequence of possible storage paths."""
    if sys.platform == 'win32':
        user_format = ''
    else:
        try:
            user_name = getpass.getuser()
        except Exception:  # The possible set of exceptions is not documented.
            user_format = ''
        else:
            user_format = '.%s' % user_name

    tempdir = tempfile.gettempdir()
    yield os.path.join(tempdir, 'appengine.%s%s' % (app_id, user_format))
    for i in itertools.count(1):
        yield os.path.join(
            tempdir, 'appengine.%s%s.%d' % (app_id, user_format, i))


def _get_storage_path(path, app_id):
    """Returns a path to the directory where stub data can be stored."""
    _, _, app_id = app_id.replace(':', '_').rpartition('~')
    if path is None:
        for path in _generate_storage_paths(app_id):
            try:
                os.mkdir(path, 0700)
            except OSError, e:
                if e.errno == errno.EEXIST:
                    if sys.platform == 'win32' or (
                        (
                            os.stat(path).st_mode & 0777) == 0700
                            and os.path.isdir(path)):
                        return path
                    else:
                        continue
                    raise
                else:
                    return path
    elif not os.path.exists(path):
        os.mkdir(path)
        return path
    elif not os.path.isdir(path):
        raise IOError('the given storage path %r is a file, a directory was '
                      'expected' % path)
    else:
        return path


def _patch_deferred():
    import deferred_manager as deferred

    def undefer(obj, *args, **kwargs):
        for arg in (
            "_countdown", "_eta", "_headers", "_name", "_target",
            "_transactional", "_url", "_queue", "unique_until",
            "task_reference"
        ):
            kwargs.pop(arg, None)
        obj(*args, **kwargs)

    deferred.defer = undefer

import datetime
import os

from google.appengine.ext import db
from google.appengine.api import taskqueue, queueinfo


def nested_getattr(obj, key, *args):
    path_keys = key.split(".")
    for key in path_keys:
        try:
            obj = getattr(obj, key, *args)
        except AttributeError:
            if len(args):
                return args[0]
            else:
                raise
    return obj


def get_queue_info():
    """
        Walk up the tree until queue.yaml is found
    """
    directory = os.path.abspath(".")
    while directory:
        file_path = os.path.join(directory, 'queue.yaml')
        if os.path.isfile(file_path):
            with open(os.path.join(directory, 'queue.yaml'), 'r') as fh:
                return queueinfo.LoadSingleQueue(fh)
        else:
            directory = os.path.dirname(directory)
            if os.path.realpath(directory) == directory:
                break

all_queue_info = get_queue_info()


class TaskState(db.Model):
    task_name = db.StringProperty(required=True)
    task_reference = db.StringProperty(required=False)

    unique_until = db.DateTimeProperty(default=False)
    is_complete = db.BooleanProperty(default=False)
    is_running = db.BooleanProperty(default=False)
    is_permanently_failed = db.BooleanProperty(default=False)
    was_purged = db.BooleanProperty(default=False)
    first_run = db.DateTimeProperty(required=False, default=None)
    retry_count = db.IntegerProperty(default=0)
    deferred_function = db.TextProperty()
    deferred_args = db.TextProperty()
    deferred_kwargs = db.TextProperty()
    deferred_at = db.DateTimeProperty(auto_now_add=True)

    request_log_ids = db.StringListProperty()

    def __init__(self, *args, **kwargs):
        if 'key' not in kwargs:
            kwargs['key_name'] = kwargs['task_name']
        super(TaskState, self).__init__(*args, **kwargs)

    @property
    def age(self):
        if self.first_run is not None:
            return (datetime.datetime.utcnow() - self.first_run).total_seconds()


class QueueState(db.Model):
    name = db.StringProperty(required=True)

    def __init__(self, *args, **kwargs):
        if 'key' not in kwargs:
            kwargs['key_name'] = kwargs['name']
        super(QueueState, self).__init__(*args, **kwargs)

    def _get_queueinfo_key(self, key, default=None):
        queue_info_obj = getattr(self, "_queue_info_obj", None)
        if not queue_info_obj:
            self._queue_info_obj = queue_info_obj = next(qi for qi in all_queue_info.queue if qi.name == self.name)
        return nested_getattr(queue_info_obj, key, None)

    @property
    def retry_limit(self):
        limit = self._get_queueinfo_key("retry_parameters.task_retry_limit", None)

        if limit is not None:
            return int(limit)

    @property
    def age_limit(self):
        limit = self._get_queueinfo_key("retry_parameters.task_age_limit", None)

        if limit:
            return queueinfo.ParseTaskAgeLimit(limit)

    def get_queue_statistics(self):
        return taskqueue.QueueStatistics.fetch(self.name)


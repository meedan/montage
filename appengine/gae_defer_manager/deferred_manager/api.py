import datetime
import json
import webapp2

from operator import itemgetter

from google.appengine.ext import db
from google.appengine.api.logservice import logservice

from .models import TaskState, QueueState

def _serializer(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    if hasattr(obj, '__dict__'):
        return obj.__dict__

    raise ValueError(obj)

def serialize_model(obj):
    return json.dumps(db.to_dict(obj), default=_serializer)

def dump(obj):
    return json.dumps(obj, default=_serializer)


class QueueListHandler(webapp2.RequestHandler):
    def get(self):
        ctx = {
            "queues": map(db.to_dict, QueueState.all())
        }

        self.response.content_type = "application/json"
        self.response.write(dump(ctx))


class QueueHandler(webapp2.RequestHandler):
    def get(self, queue_name):
        queue_state = QueueState.get_by_key_name(queue_name)

        if not queue_state:
            self.response.set_status(404)
            return

        tasks = (
            TaskState.all()
            .ancestor(queue_state)
            .order("-deferred_at")
            .with_cursor(start_cursor=self.request.GET.get('cursor'))
        )

        ctx = db.to_dict(queue_state)

        stats = queue_state.get_queue_statistics()
        ctx['stats'] = {k: getattr(stats, k) for k in ("tasks", "executed_last_minute", "in_flight", "enforced_rate",)}
        if stats.oldest_eta_usec:
            ctx['stats']['oldest_eta'] = datetime.datetime.utcfromtimestamp(stats.oldest_eta_usec / 1e6)

        ctx['tasks'] = map(db.to_dict, tasks[:int(self.request.GET.get('limit', 1000))])
        ctx['cursor'] = tasks.cursor()

        self.response.content_type = "application/json"
        self.response.write(dump(ctx))

    def delete(self, queue_name):
        # DELETE == purge in this case
        queue_state = QueueState.get_by_key_name(queue_name)

        if not queue_state:
            self.response.set_status(404)
            return

        queue_state.get_queue_statistics().queue.purge()

        rpcs = []

        for task in TaskState.all().ancestor(queue_state).filter('is_complete', False).filter('is_running', False).run():
            task.is_complete = task.is_permanently_failed = True
            task.was_purged = True
            rpcs.append(db.put_async(task))

        for rpc in rpcs:
            rpc.get_result()

        self.response.content_type = "application/json"
        self.response.write(dump({
            "message": "Purging " + queue_name
        }))

class TaskInfoHandler(webapp2.RequestHandler):
    def get(self, queue_name, task_name):
        queue_state = QueueState.get_by_key_name(queue_name)
        task_state = TaskState.get_by_key_name(task_name, parent=queue_state)

        if not (queue_state and task_state):
            self.response.set_status(404)
            return

        ctx = {
            'task': db.to_dict(task_state),
        }
        if task_state.request_log_ids:
            ctx['logs'] = sorted(get_logs(task_state.request_log_ids, logservice.LOG_LEVEL_INFO), key=itemgetter('start_time'), reverse=True)

        self.response.content_type = "application/json"
        self.response.write(dump(ctx))


class LogHandler(webapp2.RequestHandler):
    def get(self, log_id):
        log_level = int(self.request.GET.get('level', logservice.LOG_LEVEL_INFO))
        ctx = {
            'log': next(get_logs([log_id], log_level), None)
        }

        self.response.content_type = "application/json"
        self.response.write(dump(ctx))


def get_logs(log_ids, log_level):
    for request_log in logservice.fetch(minimum_log_level=log_level,
                                        include_incomplete=True,
                                        include_app_logs=True,
                                        request_ids=log_ids):

        d = {name: getattr(request_log, name)
            for name, val in request_log.__class__.__dict__.iteritems()
            if isinstance(val, property) and not name.startswith('_')
        }
        d['start_time'] = datetime.datetime.fromtimestamp(request_log.start_time)
        if request_log.end_time:
            d['end_time'] = datetime.datetime.fromtimestamp(request_log.end_time)
            d['duration'] = (d['end_time'] - d['start_time']).total_seconds()

        d['app_logs'] = [{
                'time': datetime.datetime.fromtimestamp(app_log.time),
                'level': app_log.level,
                'message': app_log.message
            }
            for app_log in d['app_logs']
            if app_log.level >= log_level
        ]
        yield d

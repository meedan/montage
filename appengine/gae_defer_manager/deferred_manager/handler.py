import datetime
import logging
import os
import webapp2

from google.appengine.ext import deferred

from .models import TaskState, QueueState


class GAEDeferAdminTaskHandler(deferred.TaskHandler):
    """A webapp handler class that processes deferred invocations."""

    def post(self):
        if self.request_forbidden():
            self.response.set_status(403)
            return

        queue_name = self.request.headers['X-AppEngine-QueueName']
        task_name = self.request.headers['X-AppEngine-TaskName']

        queue_state = QueueState.get_by_key_name(queue_name)
        task_state = TaskState.get_by_key_name(task_name, parent=queue_state)

        if not task_state:
            return super(GAEDeferAdminTaskHandler, self).post()

        task_state.is_running = True
        task_state.retry_count = int(self.request.headers['X-AppEngine-TaskExecutionCount'])
        task_state.request_log_ids.append(os.environ['REQUEST_LOG_ID'])

        if task_state.first_run is None:
            task_state.first_run = datetime.datetime.utcnow()

        task_state.put()

        try:
            self.run_from_request()

        except deferred.SingularTaskFailure as e:
            if not self.should_retry(queue_state, task_state):
                task_state.is_complete = task_state.is_permanently_failed = True
            else:
                logging.debug("Failure executing task, task retry forced")
                self.response.set_status(408)

        except deferred.PermanentTaskFailure as e:
            logging.exception("Permanent failure attempting to execute task")
            task_state.is_complete = task_state.is_permanently_failed = True

        except Exception as e:
            logging.exception(e)

            self.response.set_status(500)
            if not self.should_retry(queue_state, task_state):
                task_state.is_complete = task_state.is_permanently_failed = True
                logging.warning("Task has failed {0} times and is {1}s old. It will not be retried.".format(task_state.retry_count, task_state.age))

        else:
            task_state.is_complete = True

        finally:
            task_state.is_running = False

        task_state.put()

    def should_retry(self, queue_state, task_state):
        # TODO: handle default retry params and task-specific retry params
        if queue_state.retry_limit is not None and queue_state.age_limit is not None:
            return (
                queue_state.retry_limit > task_state.retry_count or 
                queue_state.age_limit >= task_state.age
            )

        elif queue_state.retry_limit is not None:
            return queue_state.retry_limit > task_state.retry_count

        elif queue_state.age_limit is not None:
            return queue_state.age_limit >= task_state.age

        return True

    def request_forbidden(self):
        if 'X-AppEngine-TaskName' not in self.request.headers:
            logging.critical('Detected an attempted XSRF attack. The header '
                           '"X-AppEngine-Taskname" was not set.')
            return True

        in_prod = (not os.environ.get("SERVER_SOFTWARE").startswith("Devel"))
        if in_prod and os.environ.get("REMOTE_ADDR") != "0.1.0.2":
            logging.critical('Detected an attempted XSRF attack. This request did '
                           'not originate from Task Queue.')
            return True


application = webapp2.WSGIApplication([(".*", GAEDeferAdminTaskHandler)])

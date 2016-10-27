import datetime
import logging
import types

from google.appengine.ext import deferred

from .models import TaskState, QueueState


def defer(obj, *args, **kwargs):
    task_reference = kwargs.pop('task_reference', None)
    unique_until = kwargs.pop('unique_until', False)
    queue_name = kwargs.get("_queue", deferred.deferred._DEFAULT_QUEUE)

    if unique_until:
        assert task_reference, "task_reference must be passed if unique"

    queuestate = _get_or_create_queuestate(queue_name)

    if unique_until:
        existing_tasks = (TaskState.all(keys_only=True)
            .filter("task_reference =", task_reference)
            .filter("is_complete =", False)
            .filter("unique_until >", datetime.datetime.utcnow())
            .ancestor(queuestate)
        )
        if existing_tasks.count(limit=1):
            logging.warning("Did not defer task with reference {0} - task already present".format(task_reference))
            return

    task = deferred.defer(obj, *args, **kwargs)

    taskstate = TaskState(
        parent=queuestate,
        task_name=task.name,
        task_reference=task_reference,
        unique_until=unique_until
    )
    try:
        taskstate.deferred_args = unicode(args)
        taskstate.deferred_kwargs = unicode(_strip_defer_kwargs(kwargs))
        taskstate.deferred_function = _get_func_repr(obj)
    except:
        pass
    taskstate.put()

    return taskstate

def _get_or_create_queuestate(queue_name):
    queuestate = QueueState.get_by_key_name(queue_name)

    if not queuestate:
        queuestate = QueueState(name=queue_name)
        queuestate.put()

    return queuestate

def _strip_defer_kwargs(kwargs):
    return {k:v for k,v in kwargs.items() if not k.startswith('_')}

def _get_func_repr(func):
    if isinstance(func, types.MethodType):
        return "{cls}.{func}".format(
            cls=func.im_self.__class__,
            func=func.im_func.__name__
        )
    elif isinstance(func, types.BuiltinMethodType):
        if not func.__self__:
            return "{func}".format(
                func=func.__name__
            )
        else:
            return "{type}.{func}".format(
                type=func.__self__,
                func=func.__name__
            )
    elif (isinstance(func, types.ObjectType) and hasattr(func, "__call__")) or\
        isinstance(func, (types.FunctionType, types.BuiltinFunctionType,
                        types.ClassType, types.UnboundMethodType)):
        return "{module}.{func}".format(
            module=func.__module__,
            func=func.__name__
        )
    else:
        raise ValueError("func must be callable")

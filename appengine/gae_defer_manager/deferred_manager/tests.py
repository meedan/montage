# -*- coding: utf8 -*-

import datetime
import mock
import os
import unittest
import webapp2

from google.appengine.ext import testbed, deferred
from google.appengine.api import queueinfo

from . import models
from .handler import application
from .wrapper import defer

TESTCONFIG_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "testconfig")


def noop(*args, **kwargs):
    pass

def noop_fail(*args, **kwargs):
    raise Exception

def noop_permanent_fail(*args, **kwargs):
    raise deferred.PermanentTaskFailure

class Foo(object):
    def bar(self): pass
    def __call__(self): pass

class BaseTest(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()

        self.testbed.activate()

        self.testbed.init_datastore_v3_stub()
        self.testbed.init_taskqueue_stub(root_path=TESTCONFIG_DIR)
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        super(BaseTest, self).setUp()

    def reload(self, obj):
        return obj.get(obj.key())


class DeferTaskTests(BaseTest):

    def test_creates_state(self):
        task_state = defer(noop)
        queue_state = models.QueueState.get_by_key_name("default")

        self.assertTrue(queue_state)
        self.assertEqual(task_state.parent().key(), queue_state.key())

    def test_unique_task_ref(self):
        unique_until = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        self.assertRaises(AssertionError, defer, noop, unique_until=unique_until)
        self.assertTrue(defer(noop, task_reference="project1", unique_until=unique_until))
        self.assertFalse(defer(noop, task_reference="project1", unique_until=unique_until))

    def test_args_repr(self):
        task_state = defer(noop, 2, u"bår")
        self.assertEqual(task_state.deferred_args, u"(2, u'b\\xe5r')")

    def test_kwargs_repr(self):
        task_state = defer(noop, foo="bår", _bar="foo")
        self.assertEqual(task_state.deferred_kwargs, u"{'foo': 'b\\xc3\\xa5r'}")

    def test_class_method_repr(self):
        task_state = defer(Foo().bar)
        self.assertEqual(task_state.deferred_function, u"<class 'deferred_manager.tests.Foo'>.bar")

    def test_module_func_repr(self):
        task_state = defer(noop)
        self.assertEqual(task_state.deferred_function, u"deferred_manager.tests.noop")

    def test_builtin_func_repr(self):
        task_state = defer(map)
        self.assertEqual(task_state.deferred_function, u"map")

    def test_callable_obj_func_repr(self):
        task_state = defer(Foo)
        self.assertEqual(task_state.deferred_function, u"deferred_manager.tests.Foo")

    def test_builtin_method_repr(self):
        task_state = defer(datetime.datetime.utcnow)
        self.assertEqual(task_state.deferred_function, u"<type 'datetime.datetime'>.utcnow")


class ModelTaskTests(unittest.TestCase):
    def test_queue_state(self):
        queue_state = models.QueueState(name="default")

        self.assertEqual(queue_state.retry_limit, 7)
        self.assertEqual(queue_state.age_limit, 2*24*3600) # 2 days


class HandlerTests(BaseTest):
    def make_request(self, path, task_name, queue_name, headers=None, environ=None, **kwargs):
        request_headers = {
            "X-AppEngine-TaskName": task_name,
            "X-AppEngine-QueueName": queue_name,
            'X-AppEngine-TaskExecutionCount': kwargs.pop('retries', 0)
        }
        if headers:
            request_headers.update(headers)

        request_environ = {
            "SERVER_SOFTWARE": "Development"
        }
        if environ:
            request_environ.update(environ)

        return webapp2.Request.blank('/', environ=request_environ, headers=request_headers, **kwargs)

    def test_success(self):
        task_state = defer(noop)
        noop_pickle = deferred.serialize(noop)

        request = self.make_request("/", task_state.task_name, 'default', POST=noop_pickle)
        response = request.get_response(application)

        self.assertEqual(response.status_int, 200)

        task_state = self.reload(task_state)
        self.assertTrue(task_state.task_name)
        self.assertTrue(task_state.is_complete)
        self.assertFalse(task_state.is_running)
        self.assertFalse(task_state.is_permanently_failed)

    def test_failure(self):
        task_state = defer(noop_fail)
        noop_pickle = deferred.serialize(noop_fail)

        request = self.make_request("/", task_state.task_name, 'default', POST=noop_pickle)
        response = request.get_response(application)

        self.assertEqual(response.status_int, 500)

        task_state = self.reload(task_state)
        self.assertFalse(task_state.is_complete)
        self.assertFalse(task_state.is_running)
        self.assertFalse(task_state.is_permanently_failed)

    def test_retry_success(self):
        task_state = defer(noop)
        noop_pickle = deferred.serialize(noop)

        request = self.make_request("/", task_state.task_name, 'default', POST=noop_pickle, retries=2)
        response = request.get_response(application)

        self.assertEqual(response.status_int, 200)

        task_state = self.reload(task_state)
        self.assertEqual(task_state.retry_count, 2)
        self.assertTrue(task_state.is_complete)
        self.assertFalse(task_state.is_running)
        self.assertFalse(task_state.is_permanently_failed)

    def test_retry_max_retries(self):
        task_state = defer(noop_fail)

        # give the task an old age. tasks must fail both the retry and age conditions (if specified)
        task_state.first_run = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        task_state.put()

        noop_pickle = deferred.serialize(noop_fail)

        request = self.make_request("/", task_state.task_name, 'default', POST=noop_pickle, retries=8)
        response = request.get_response(application)

        self.assertEqual(response.status_int, 500)

        task_state = self.reload(task_state)
        self.assertEqual(task_state.retry_count, 8)
        self.assertTrue(task_state.is_complete)
        self.assertFalse(task_state.is_running)
        self.assertTrue(task_state.is_permanently_failed)

    def test_permanent_failure(self):
        task_state = defer(noop_permanent_fail)
        noop_pickle = deferred.serialize(noop_permanent_fail)

        request = self.make_request("/", task_state.task_name, 'default', POST=noop_pickle)
        response = request.get_response(application)

        self.assertEqual(response.status_int, 200)

        task_state = self.reload(task_state)
        self.assertEqual(task_state.retry_count, 0)
        self.assertTrue(task_state.is_complete)
        self.assertFalse(task_state.is_running)
        self.assertTrue(task_state.is_permanently_failed)

    def test_no_task_state(self):
        noop_pickle = deferred.serialize(noop)

        request = self.make_request("/", 'task1', 'default', POST=noop_pickle)
        response = request.get_response(application)

        self.assertEqual(response.status_int, 200)


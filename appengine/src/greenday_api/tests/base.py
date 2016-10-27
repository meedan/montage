"""
    Generic test functionality for the unit tests
"""
import os

# FRAMEWORK
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone

# LIBRARIES
from milkman.dairy import milkman

# GREENDAY
from greenday_core.models import Event
from greenday_core.tests.base import AppengineTestBed


class ApiTestCase(AppengineTestBed):
    """
        Base class for API tests
    """
    api_type = None
    _signed_in_user = None

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.api = self.api_type() if self.api_type else None
        self.create_test_users()

    @classmethod
    def setUpClass(cls):
        """
            Tries to ensures that all auto IDs are unique across all tables by
            starting each tables's sequence at +20 from the previous table
        """
        super(ApiTestCase, cls).setUpClass()

        cursor = connection.cursor()

        # run the below to start the auto ID for each table at a different
        # so that we don't get false positives in tests
        for i, model in enumerate(apps.get_models()):
            cursor.execute("ALTER TABLE {0} AUTO_INCREMENT = {1}".format(
                model._meta.db_table, i*20))

    def create_test_users(self):
        """
            Creates test users
        """
        User = get_user_model()
        self.admin = milkman.deliver(
            User,
            email="admin@example.com",
            is_superuser=True,
            first_name="Polar",
            last_name="Bear",
            is_whitelisted=True)
        self.admin2 = milkman.deliver(
            User,
            email="admin2@example.com",
            is_staff=True,
            first_name="Manx",
            last_name="Shearwater",
            is_whitelisted=True)
        self.user = milkman.deliver(
            User,
            email="user@example.com",
            first_name="Razor",
            last_name="Bill")
        self.user2 = milkman.deliver(
            User,
            email="user2@example.com",
            first_name="Storm",
            last_name="Petrel")

    def _sign_in(self, user, domain="example.com"):
        """
            Sets env variables to set a user as signed in for the API
        """
        os.environ['ENDPOINTS_AUTH_EMAIL'] = user.email
        os.environ['ENDPOINTS_AUTH_DOMAIN'] = domain

        self._signed_in_user = user

        if hasattr(self.api, "_user"):
            del self.api._user

    def _sign_out(self):
        """
            Clears all variables set to sign a user into the API
        """
        for k in (k for k in ('ENDPOINTS_AUTH_EMAIL', 'ENDPOINTS_AUTH_DOMAIN',)
                  if k in os.environ):
            del os.environ[k]

        self._signed_in_user = None

        if hasattr(self.api, "_user"):
            del self.api._user


class TestEventBusMixin(object):
    """
        Mixin to provide `assertEventRecorded` context manager
    """
    def assertEventRecorded(
            self,
            kind_or_kwargs_list,
            **kwargs):
        """
            Returns a context manager to ensure that a set of given application
            events were recorded
        """
        try:
            iter(kind_or_kwargs_list)
        except TypeError:
            user = kwargs.pop('user', self._signed_in_user)
            recorder = EventRecorder(
                self,
                kind_or_kwargs_list,
                user=user,
                **kwargs)
            return EventRecorderWrapper(recorder)

        recorders = []
        for kwargs_item in kind_or_kwargs_list:
            kind = kwargs_item.pop('kind')
            user = kwargs_item.pop('user', self._signed_in_user)
            recorder = EventRecorder(
                self,
                kind,
                user=user,
                **kwargs_item)
            recorders.append(recorder)
        return EventRecorderWrapper(recorders)

class EventRecorderWrapper(object):
    """
        Context manager to wrap multiple event recorders to assert a number of
        events were recorded within the context
    """
    def __init__(self, event_recorders):
        """
            Creates the context manager
        """
        try:
            iter(event_recorders)
        except TypeError:
            event_recorders = (event_recorders,)

        self.event_recorders = event_recorders

    def __enter__(self):
        """
            Handles the starts of the context
        """
        self.start()

    def __exit__(self, err_type, err_value, err_traceback):
        """
            Handles the end of the context
        """
        if not err_value:
            self.do_assert()

    def start(self):
        """
            Starts each event recorder
        """
        for recorder in self.event_recorders:
            recorder.start()

    def do_assert(self):
        """
            Asserts the event for each event recorder
        """
        for recorder in self.event_recorders:
            recorder.do_assert()


class EventRecorder(object):
    """
        Asserts that a given event was recorded

        Assumes that other events are not already in the database
    """
    def __init__(self,
                 testcase,
                 kind,
                 object_id=None,
                 project_id=None,
                 video_id=None,
                 meta=None,
                 user=None):
        """
            Creates the recorder
        """
        self.testcase = testcase
        self.kind = kind
        self.object_id = object_id
        self.project_id = project_id
        self.video_id = video_id
        self.meta = meta
        self.user = user

    def start(self):
        """
            Sets the start time of the recorder
        """
        # remove microseconds as datetimefield doesn't have this accuracy
        self.timestamp = timezone.now().replace(microsecond=0)

    def do_assert(self):
        """
            Asserts that the given event was recorded since `self.timestamp`
        """
        qry = Event.objects.filter(
            kind=self.kind)

        if self.object_id and type(self.object_id) in (int, long, float,):
            qry = qry.filter(object_id=self.object_id)

        if self.project_id and type(self.project_id) in (int, long, float,):
            qry = qry.filter(project_id=self.project_id)

        if self.video_id and type(self.video_id) in (int, long, float,):
            qry = qry.filter(video_id=self.video_id)

        if self.user:
            qry = qry.filter(user=self.user)

        # # manually filter on timestamp (doing in the DB isn't
        # # accurate enough for unit tests)
        events = [e for e in qry if e.timestamp >= self.timestamp]

        self.testcase.assertTrue(len(events) > 0, "No events recorded")
        self.testcase.assertTrue(len(events) < 2, "Too many events recorded")

        event = events[0]
        if self.object_id is True:
            self.testcase.assertTrue(event.object_id)

        if self.project_id is True:
            self.testcase.assertTrue(event.project_id)

        if self.video_id is True:
            self.testcase.assertTrue(event.video_id)

        if self.meta is True:
            self.testcase.assertTrue(event.meta)

        if self.meta:
            self.testcase.assertEqual(self.meta, event.meta)

        # wipe event so this doesn't bleed into other checks
        events[0].delete()

"""
    Tests for :mod:`greenday_core.eventbus <greenday_core.eventbus>`
"""
import datetime
import unittest
import mock
from milkman.dairy import milkman

# FRAMEWORK
from django.contrib.auth import get_user_model

# GREENDAY
from ..constants import EventKind, EventCommonCodes, EventModel
from ..eventbus import (
    appevent,
    publish_appevent,
    get_events,
    get_events_with_objects
)
from ..models import Event, Project
from .base import AppengineTestBed

DEFAULT_KIND = next(e for e in EventKind)


class DecoratorTests(unittest.TestCase):
    """
        Tests for :class:`greenday_core.eventbus.EventDecorator <greenday_core.eventbus.EventDecorator>`
    """
    @mock.patch("greenday_core.eventbus.publish_appevent")
    def test_decorated(self, publish_appevent_mock):
        """
            Decorate a function with args evaluated before the function has executed
        """
        mockobj = mock.Mock()
        mockobj.__name__ = "foo"
        mockfn = appevent(
            kind=DEFAULT_KIND,
            id_getter=lambda id, id2: int(id),
            project_id_getter=lambda id, id2: int(id2),
            video_id_getter=lambda id, id2: int(id),
            meta_getter=lambda id, id2: "The answer is {0}".format(id),
            user_getter=lambda id, id2: 99
        )(mockobj)

        mockfn("42", "84")

        mockobj.assert_called_once_with("42", "84")

        publish_appevent_mock.assert_called_once_with(
            DEFAULT_KIND,
            object_id=42,
            project_id=84,
            video_id=42,
            meta="The answer is 42",
            user=99
        )

    @mock.patch("greenday_core.eventbus.publish_appevent")
    def test_decorated_post_args(self, publish_appevent_mock):
        """
            Decorate a function with args evaluated after the function has executed
        """
        mockobj = mock.Mock()
        mockobj.__name__ = "foo"

        # just an arbirary multiplier to change the values
        # for the _post expressions
        multiplier = 4

        mockobj.return_value = multiplier

        mockfn = appevent(
            kind=DEFAULT_KIND,
            id_getter_post=lambda id, id2, ret: int(id)*ret,
            project_id_getter_post=lambda id, id2, ret: int(id2)*ret,
            video_id_getter_post=lambda id, id2, ret: int(id)*ret,
            meta_getter_post=(
                lambda id, id2, ret: "The answer is {0}".format(ret)),
            user_getter_post=lambda id, id2, ret: 99*ret
        )(mockobj)

        mockfn("42", "84")

        mockobj.assert_called_once_with("42", "84")

        publish_appevent_mock.assert_called_once_with(
            DEFAULT_KIND,
            object_id=42*multiplier,
            project_id=84*multiplier,
            video_id=42*multiplier,
            meta="The answer is {0}".format(multiplier),
            user=99*multiplier
        )

    @mock.patch("greenday_core.eventbus.publish_appevent")
    def test_decorated_iterable(self, publish_appevent_mock):
        """
            Decorate a function with object_ids evaluated as iterable

            Creates an event for each object_id
        """
        # mock api endpoint.
        mockobj = mock.Mock()
        mockobj.__name__ = "foo"

        # mock request - iterable objects would most likely be a batch
        # insert request e.g /foo/bar/add/batch?objects=1,3,4,5,6 and
        # would most likely be a comma seperated querystring arg which
        # would be split on the decorator.
        # However we dont care about implementation at this level only
        # that the decorator id_getter gets an iterable rather than a
        # standard object id. So to achieve this we simply create a
        # ids attribute on our mock request and then pass that to the
        # id_getter lambda function as a generator.
        req = mock.Mock()
        req.ids = [55, 78, 105]

        # mock decorator passing in the iterable request id_getter
        mockfn = appevent(
            kind=DEFAULT_KIND,
            id_getter=lambda id, id2, req: [obj_id for obj_id in req.ids],
            project_id_getter=lambda id, id2, req: int(id2)
        )(mockobj)

        # check the decorator is called with the ids and mock request.
        mockfn("42", "84", req)

        # check that the mock api end point is then called with the
        # ids and mock request object.
        mockobj.assert_called_once_with("42", "84", req)

        # now check that the objects were all published as app events.
        # We assert that the order is correct and that the data they
        # are called with is correct.
        publish_appevent_mock.assert_has_calls([
            mock.call(
                DEFAULT_KIND,
                object_id=55,
                project_id=84,
                video_id=None,
                meta=None,
                user=None,
            ),
            mock.call(
                DEFAULT_KIND,
                object_id=78,
                project_id=84,
                video_id=None,
                meta=None,
                user=None,
            ),
            mock.call(
                DEFAULT_KIND,
                object_id=105,
                project_id=84,
                video_id=None,
                meta=None,
                user=None,
            )
        ], any_order=False)

    @mock.patch("greenday_core.eventbus.publish_appevent")
    def test_decorated_post_args_iterable(self, publish_appevent_mock):
        """
            Decorate a function with object_ids evaluated as iterable after the
            function has executed

            Creates an event for each object_id
        """
        # mock api endpoint
        mockobj = mock.Mock()
        mockobj.__name__ = "foo"

        # mock response - This test makes the assumption that the
        # response would be an api endpoints message class and so the
        # response is mocked to look like one.
        obj1 = mock.Mock()
        obj1.id = 55
        obj2 = mock.Mock()
        obj2.id = 78
        obj3 = mock.Mock()
        obj3.id = 105
        resp = mock.Mock()
        resp.items = [obj1, obj2, obj3]
        mockobj.return_value = resp

        # mock decorator passing it our mocked response
        mockfn = appevent(
            kind=DEFAULT_KIND,
            id_getter_post=lambda id, id2, ret: [
                obj.id for obj in ret.items],
            project_id_getter=lambda id, id2: int(id2)
        )(mockobj)

        # check the decorator was called with the ids
        mockfn("42", "84")

        # check that the mock endpoint is called with the relevant ids
        mockobj.assert_called_once_with("42", "84")

        # now check that the objects were all published as app events.
        # We assert that the order is correct and that the data they
        # are called with is also correct.
        publish_appevent_mock.assert_has_calls([
            mock.call(
                DEFAULT_KIND,
                object_id=55,
                project_id=84,
                video_id=None,
                meta=None,
                user=None,
            ),
            mock.call(
                DEFAULT_KIND,
                object_id=78,
                project_id=84,
                video_id=None,
                meta=None,
                user=None,
            ),
            mock.call(
                DEFAULT_KIND,
                object_id=105,
                project_id=84,
                video_id=None,
                meta=None,
                user=None,
            )
        ], any_order=False)


class PublishTests(AppengineTestBed):
    """
        Tests for :func:`greenday_core.eventbus.publish_appevent <greenday_core.eventbus.publish_appevent>`
    """
    def test_publish(self):
        """
            Publish an event
        """
        user = milkman.deliver(get_user_model())
        publish_appevent(
            DEFAULT_KIND,
            object_id=42,
            project_id=84,
            video_id=42,
            meta="baz",
            user=user)

        event = Event.objects.get()

        self.assertEqual(event.kind, DEFAULT_KIND)
        self.assertEqual(event.object_id, 42)
        self.assertEqual(event.project_id, 84)
        self.assertEqual(event.video_id, 42)
        self.assertEqual(event.meta, "baz")
        self.assertEqual(event.user, user)


class EventRetrievalTests(AppengineTestBed):
    """
        Tests for :func:`greenday_core.eventbus.get_events <greenday_core.eventbus.get_events>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(EventRetrievalTests, self).setUp()

        self.now = datetime.datetime.utcnow()

        self.event_1 = Event.objects.create(
            timestamp=self.now - datetime.timedelta(minutes=10),
            kind=EventKind.PROJECTCREATED
        )

        self.event_2 = Event.objects.create(
            timestamp=self.now - datetime.timedelta(minutes=4),
            kind=EventKind.PROJECTCREATED
        )

        self.event_3 = Event.objects.create(
            timestamp=self.now - datetime.timedelta(minutes=11),
            kind=EventKind.PROJECTUPDATED
        )

        self.event_4 = Event.objects.create(
            timestamp=self.now - datetime.timedelta(minutes=5),
            kind=EventKind.PROJECTUPDATED
        )

    def test_get_events_all(self):
        """
            Get all events boostrapped
        """
        events = get_events(self.now - datetime.timedelta(minutes=15))
        self.assertEqual(4, len(events))

    def test_get_events_all_recent(self):
        """
            Get all events in the last few minutes
        """
        events = get_events(self.now - datetime.timedelta(minutes=6))
        self.assertEqual(2, len(events))

    def test_get_events_object_id(self):
        """
            Get all events for the given object ID
        """
        event = Event.objects.create(
            timestamp=self.now - datetime.timedelta(minutes=5),
            kind=EventKind.PROJECTUPDATED,
            object_id=42
        )
        events = get_events(self.now - datetime.timedelta(
            minutes=15), object_id=42)

        self.assertEqual(1, len(events))
        self.assertEqual(event, events[0])

    def test_get_events_single_kind(self):
        """
            Get all events of a given compound event kind
        """
        events = get_events(self.now - datetime.timedelta(
            minutes=15), kind=EventKind.PROJECTCREATED)

        self.assertEqual(2, len(events))
        self.assertIn(self.event_1, events)
        self.assertIn(self.event_2, events)

    def test_get_events_event_kind(self):
        """
            Get all events of a given event code
        """
        events = get_events(self.now - datetime.timedelta(
            minutes=15), event_kind=EventCommonCodes.CREATED)

        self.assertEqual(2, len(events))
        self.assertIn(self.event_1, events)
        self.assertIn(self.event_2, events)

    def test_get_events_object_kind(self):
        """
            Get all events of a given object kind
        """
        events = get_events(self.now - datetime.timedelta(
            minutes=15), object_kind=EventModel.PROJECT)

        self.assertEqual(4, len(events))
        self.assertIn(self.event_1, events)
        self.assertIn(self.event_2, events)
        self.assertIn(self.event_3, events)
        self.assertIn(self.event_4, events)

    def test_ordering(self):
        """
            Events should be ordered by timestamp
        """
        events = get_events(self.now - datetime.timedelta(minutes=15))

        self.assertEqual(events[0].pk, self.event_2.pk)
        self.assertEqual(events[1].pk, self.event_4.pk)
        self.assertEqual(events[2].pk, self.event_1.pk)
        self.assertEqual(events[3].pk, self.event_3.pk)


class EventRetrievalWithObjectsTests(AppengineTestBed):
    """
        Tests for :func:`greenday_core.eventbus.get_events_with_objects <greenday_core.eventbus.get_events_with_objects>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(EventRetrievalWithObjectsTests, self).setUp()

        self.now = datetime.datetime.utcnow()

    def test_get_event_groups(self):
        """
            Get project and video events
        """
        project = milkman.deliver(Project)
        project_event = Event.objects.create(
            timestamp=self.now - datetime.timedelta(minutes=10),
            kind=EventKind.PROJECTCREATED,
            object_id=project.pk
        )

        video = self.create_video()
        video_event = Event.objects.create(
            timestamp=self.now - datetime.timedelta(minutes=11),
            kind=EventKind.VIDEOCREATED,
            object_id=video.pk,
            video_id=video.pk
        )

        events, objects = get_events_with_objects(
            self.now - datetime.timedelta(minutes=15))

        self.assertIn('project', objects)
        self.assertIn('video', objects)

        self.assertEqual(events[0].pk, project_event.pk)
        self.assertEqual(objects['project'][0].pk, project.pk)

        self.assertEqual(events[1].pk, video_event.pk)
        self.assertEqual(objects['video'][0].pk, video.pk)

    def test_get_missing_object(self):
        """
            Get event referencing an object which doesn't exist
        """
        project_event = Event.objects.create(
            timestamp=self.now - datetime.timedelta(minutes=10),
            kind=EventKind.PROJECTCREATED,
            object_id=999
        )

        events, objects = get_events_with_objects(
            self.now - datetime.timedelta(minutes=15))

        self.assertIn('project', objects)

        self.assertEqual(events[0].id, project_event.pk)
        self.assertEqual(len(objects['project']), 0)

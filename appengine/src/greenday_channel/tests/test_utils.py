"""
    Tests for :mod:`greenday_channel.utils <greenday_channel.utils>`
"""
import json
import mock
from milkman.dairy import milkman
import StringIO

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from greenday_core.models import Project
from greenday_core.tests.base import AppengineTestBed

from ..utils import retry_until_truthy, clean_channels


class RetryUntilTruthyTestCase(AppengineTestBed):
    """
        Tests for :func:`greenday_channel.utils.retry_until_truthy <greenday_channel.utils.retry_until_truthy>`
    """
    def test_ok(self):
        """
            Test the method
        """
        test_args = (1, 2, 3,)
        test_kwargs = {"a": 1}

        state = {
            "count": 0
        }

        def method(*args, **kwargs):
            self.assertEqual(test_args, args)
            self.assertEqual(test_kwargs, kwargs)
            state['count'] += 1

            return state['count'] == 5

        retry_until_truthy(
            method,
            max_retries=10,
            sleep=None,
            args=test_args,
            kwargs=test_kwargs)

        self.assertEqual(state['count'], 5)


class CleanChannelsTestCase(AppengineTestBed):
    """
        Tests for :func:`greenday_channel.utils.clean_channels <greenday_channel.utils.clean_channels>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(CleanChannelsTestCase, self).setUp()

        User = get_user_model()
        self.user = milkman.deliver(User, email="user@example.com")
        self.project = milkman.deliver(Project)
        self.video = self.create_video(project=self.project)

    def test_ok(self):
        """
            User has access to two valid channels
        """
        self.project.add_assigned(self.user, pending=False)
        channels = [
            "projectid-{0}".format(self.project.pk),
            "videoid-{0}".format(self.video.pk)
        ]
        cleaned_channels = clean_channels(self.user, channels)

        self.assertEqual(channels, cleaned_channels)

    def test_missing(self):
        """
            User has access to one valid channel and one non-existant
            channel
        """
        self.project.add_assigned(self.user, pending=False)
        channels = [
            "projectid-{0}".format(self.project.pk),
            "videoid-99999"
        ]
        cleaned_channels = clean_channels(self.user, channels)

        self.assertEqual(channels[:1], cleaned_channels)

    def test_not_assigned_project(self):
        """
            User does not have access to get updates for the given project
        """
        channels = [
            "projectid-{0}".format(self.project.pk)
        ]
        self.assertRaises(PermissionDenied, clean_channels, self.user, channels)

    def test_not_assigned_video(self):
        """
            User does not have access to get updates for the given video
        """
        channels = [
            "videoid-{0}".format(self.video.pk)
        ]
        self.assertRaises(PermissionDenied, clean_channels, self.user, channels)

    def test_super_user_not_assigned(self):
        """
            Super users can use any channel
        """
        self.user.is_superuser = True
        channels = [
            "projectid-{0}".format(self.project.pk),
            "videoid-{0}".format(self.video.pk)
        ]
        cleaned_channels = clean_channels(self.user, channels)

        self.assertEqual(channels, cleaned_channels)

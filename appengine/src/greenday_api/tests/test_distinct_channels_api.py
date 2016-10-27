"""
    Tests for :mod:`greenday_api.misc.distinct_channels_api <greenday_api.misc.distinct_channels_api>`
"""
from protorpc import message_types

from .base import ApiTestCase

from ..misc.distinct_channels_api import DistinctChannelsAPI


class DistinctChannelsAPITests(ApiTestCase):
    """
        Test case for
        :func:`greenday_api.misc.distinct_channels_api <greenday_api.misc.distinct_channels_api>`
    """
    api_type = DistinctChannelsAPI

    def setUp(self):
        """
            Bootstrap test case
        """
        super(DistinctChannelsAPITests, self).setUp()

        self.video_1 = self.create_video(
            channel_id="123", channel_name="foo")

        self.video_2 = self.create_video(
            channel_id="123", channel_name="fez")

        self.video_3 = self.create_video(
            channel_id="456", channel_name="bar")

    def test_get_distinct_channels(self):
        """
            Gets all distinct channels across all videos in Montage
        """
        self._sign_in(self.admin)

        request = message_types.VoidMessage()
        response = self.api.get_distinct_channels(request)

        self.assertEqual(2, len(response.items))

        channel_123_resp = next(r for r in response.items if r.id == "123")
        self.assertEqual("fez", channel_123_resp.name)

        channel_456_resp = next(r for r in response.items if r.id == "456")
        self.assertEqual("bar", channel_456_resp.name)

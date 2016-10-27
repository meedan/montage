"""
    Tests endpoints API config
"""
# FRAMEWORK
from endpoints.api_config import ApiConfigGenerator

# GREENDAY
from .base import ApiTestCase

from ..api import greenday_api


class TestApiConfigTestCase(ApiTestCase):
    """
        Test case for endpoints API config
    """
    def test_get_config(self):
        """
            Tests that no errors occur when endpoints config is created
            from the configured classes
        """
        ApiConfigGenerator().pretty_print_config_to_json(
            greenday_api.get_api_classes()
        )

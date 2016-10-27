"""
    Tests for :mod:`greenday_api.utils <greenday_api.utils>`
"""
# LIBRARIES
import os

# FRAMEWORK
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models.fields import FieldDoesNotExist

# GREENDAY
from greenday_core.api_exceptions import (
    ForbiddenException, UnauthorizedException)

from .base import ApiTestCase
from ..utils import (
    get_current_user,
    is_field_nullable,
)


class GetCurrentUserTests(ApiTestCase):
    """
        Test case for
        :func:`greenday_api.utils.get_current_user <greenday_api.utils.get_current_user>`
    """
    def test_gets_user(self):
        """
            Signed in user should be returned
        """
        self._sign_in(self.user)
        user = get_current_user()

        self.assertEqual(self.user, user)

    def test_no_db_user(self):
        """
            Signed in user isn't in the database but is created
        """
        os.environ['ENDPOINTS_AUTH_EMAIL'] = "foobar@example.com"
        os.environ['ENDPOINTS_AUTH_DOMAIN'] = 'example.com'

        self.assertTrue(get_current_user(silent=True))

    def test_no_user(self):
        """
            No signed in user
        """
        # environ variables need to be present or
        # endpoints.get_current_user throws
        os.environ['ENDPOINTS_AUTH_EMAIL'] =\
            os.environ['ENDPOINTS_AUTH_DOMAIN'] = ""
        self.assertRaises(UnauthorizedException, get_current_user)


class IsFieldNullableTests(ApiTestCase):
    """
        Test case for
        :func:`greenday_api.utils.is_field_nullable <greenday_api.utils.is_field_nullable>`
    """
    def test_invalid_field(self):
        """
            Field does not exist
        """
        self.assertRaises(
            FieldDoesNotExist, is_field_nullable, get_user_model(), "foo")

    def test_normal_fields(self):
        """
            Returns False as User.email is not nullable
        """
        self.assertFalse(is_field_nullable(get_user_model(), "email"))

    def test_foreign_key(self):
        """
            Returns False as Permission.content_type_id is not nullable
        """
        self.assertFalse(is_field_nullable(Permission, "content_type_id"))

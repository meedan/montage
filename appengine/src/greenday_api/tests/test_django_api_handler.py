"""
    Tests for :mod:`greenday_api.django_api <greenday_api.django_api>`
"""
import datetime
import json
import mock
import unittest
from milkman.dairy import milkman

from django.core.urlresolvers import reverse
from django.utils import timezone

from greenday_core.models import Project, VideoCollection

from .base import ApiTestCase


@unittest.skip("Skipping Django-served API tests")
class TestDjangoApiWrapperTestCase(ApiTestCase):
    """
        Test case for
        :class:`greenday_api.django_api.GreendayDjangoApi <greenday_api.django_api.GreendayDjangoApi>`
    """
    def setUp(self):
        """
            Patches get_current_user. Not testing auth here.
        """
        super(TestDjangoApiWrapperTestCase, self).setUp()

        self.get_current_user_patcher = mock.patch(
            "greenday_api.api.get_current_user", new=self._get_current_user)
        self.get_current_user_patcher.start()

    def tearDown(self):
        """
            Unpatches get_current_user
        """
        self.get_current_user_patcher.stop()
        super(TestDjangoApiWrapperTestCase, self).tearDown()

    def _get_current_user(self, silent=False, process_from_request=None):
        return self._signed_in_user

    def test_get(self):
        """
            Basic GET with no args
        """
        self._sign_in(self.admin)

        resp = self.client.get(
            reverse('api', kwargs={'path': 'users/me'}))

        self.assertEqual(200, resp.status_code)
        data = json.loads(resp.content)

        self.assertEqual(self.admin.email, data['email'])

    def test_get_with_args(self):
        """
            GET with args in path
        """
        self._sign_in(self.admin)

        project = milkman.deliver(Project)
        project.set_owner(self.admin)

        collection = milkman.deliver(VideoCollection, project=project)

        resp = self.client.get(
            "{0}?archived=true".format(reverse(
                'api',
                kwargs={'path': 'project/{0}/collection/{1}/video'.format(
                    project.pk, collection.pk)}))
        )

        self.assertEqual(200, resp.status_code)

    def test_get_with_qs(self):
        """
            GET with args in query string
        """
        self._sign_in(self.admin)

        resp = self.client.get(
            '{0}?q={1}'.format(
            reverse(
                'api',
                kwargs={
                    'path': 'users/autocomplete'
                }),
            self.admin.first_name)
        )

        self.assertEqual(200, resp.status_code)

        data = json.loads(resp.content)
        self.assertEqual(self.admin.email, data['items'][0]['email'])

    def test_post(self):
        """
            Basic POST with body payload
        """
        self._sign_in(self.admin)

        project = milkman.deliver(Project)
        project.set_owner(self.admin)

        resp = self.client.post(
            reverse('api', kwargs={'path': 'project'}),
            json.dumps({
                "name": "Test Project",
                "description": "Test Description",
                "image_url": "//img",
                "privacy_project": 1,
                "privacy_tags": "1"  # testing type casting
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, resp.status_code)
        data = json.loads(resp.content)

        project = Project.objects.get(pk=data['id'])
        self.assertEqual(project.name, data['name'])
        self.assertEqual(project.privacy_project, Project.PRIVATE)
        self.assertEqual(project.privacy_tags, Project.PRIVATE)

    def test_put_with_date(self):
        """
            Basic PUT with payload
        """
        self._sign_in(self.admin)

        resp = self.client.put(
            reverse('api', kwargs={'path': 'users/me'}),
            json.dumps({
                "email": self.admin.email,
                "last_login": "2015-04-07T13:41:08+00:00",
                "is_active": True,
                "gaia_id": "123456789123456789",
                "google_plus_profile": "https://plus.google.com/12345",
                "last_name": self.admin.last_name,
                "first_name": self.admin.first_name,
                "accepted_nda": True
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, resp.status_code)

        self.assertEqual(
            datetime.datetime(2015, 4, 7, 13, 41, 8, tzinfo=timezone.utc),
            self.reload(self.admin).last_login)

    def test_exception(self):
        """
            Raises exception in correct format
        """
        resp = self.client.get(
            reverse('api', kwargs={'path': 'users/me'}))

        self.assertEqual(401, resp.status_code)
        data = json.loads(resp.content)

        self.assertEqual({
            'error': {
                'message': '401|None',
                'code': 401,
                'errors': [{
                    'domain': 'global',
                    'message': '401|None'
                }]
            }
        }, data)

    def test_empty_list(self):
        """
            Check custom serialiser returns keys with empty list values
        """
        self._sign_in(self.admin)

        project = milkman.deliver(Project)
        project.set_owner(self.admin)

        resp = self.client.get(
            reverse(
                'api',
                kwargs={'path': 'project/{0}/video'.format(
                    project.pk)})
        )

        self.assertEqual(200, resp.status_code)
        data = json.loads(resp.content)

        self.assertEqual(0, len(data['items']))

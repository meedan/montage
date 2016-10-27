"""
    Tests for :mod:`greenday_public.views <greenday_public.views>`
"""
# import python deps
import os
import mock
import cloudstorage as gcs

from google.appengine.api.urlfetch_stub import URLFetchServiceStub
from google.appengine.ext import blobstore

# import django deps
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.conf import settings

from greenday_core.tests.base import AppengineTestBed
from greenday_core.models import PendingUser, Project

# import library deps
from milkman.dairy import milkman


# test views
class PublicBaseViewTestCase(AppengineTestBed):
    """
        Tests the public base view.
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(PublicBaseViewTestCase, self).setUp()

        self.admin = milkman.deliver(
            get_user_model(), email="admin@example.com", is_superuser=True,
            username='123456_gaia_id')

    def _sign_in(self, user):
        # allows us to spoof a logged in user for middleware.
        os.environ['USER_EMAIL'] = user.email
        os.environ['USER_IS_ADMIN'] = str(int(user.is_superuser))
        os.environ['USER_ID'] = user.username

    def test_200_ok(self):
        """
            Authorised user can load app
        """
        self._sign_in(self.admin)
        resp = self.client.get(reverse('index'))
        self.assertEqual(200, resp.status_code)

    def test_403_bad_user(self):
        """
            Unauthorised user
        """
        os.environ['USER_EMAIL'] = "baduser@example.com"
        os.environ['USER_IS_ADMIN'] = "0"
        os.environ['USER_ID'] = "baduser"
        resp = self.client.get(reverse('index'))
        self.assertEqual(403, resp.status_code)

    def test_whitelisted_user(self):
        """
            User on hardcoded whitelist
        """
        os.environ['USER_EMAIL'] = settings.WHITELIST[0]
        os.environ['USER_IS_ADMIN'] = "0"
        os.environ['USER_ID'] = "whitelisteduser"

        resp = self.client.get(reverse('index'))
        self.assertEqual(200, resp.status_code)

        created_user = get_user_model().objects.get(
            email=settings.WHITELIST[0])
        # explicitly whitelisted users are always superusers
        self.assertTrue(created_user.is_superuser)

    def test_pending_user(self):
        """
            User has been invited (is a pending user)
        """
        # create a pending user and assign to a project
        pending_user = PendingUser.objects.create(email="hansolo@example.com")
        project = milkman.deliver(Project)
        project.add_assigned(pending_user)

        os.environ['USER_EMAIL'] = pending_user.email
        os.environ['USER_ID'] = "a_gaia_id"

        with self.assertNumQueries(8):
            resp = self.client.get(reverse('index'))

        self.assertFalse(
            PendingUser.objects.filter(pk=pending_user.pk).exists())

        new_user = get_user_model().objects.get(email=pending_user.email)
        self.assertFalse(new_user.is_whitelisted)

        projectuser = project.get_user_relation(new_user)
        self.assertTrue(projectuser.is_pending)

    def test_pending_whitelisted_user(self):
        """
            User has been invited and is also on the hard coded whitelist
        """
        pending_user = PendingUser.objects.create(
            email="hansolo@example.com",
            is_whitelisted=True
        )

        os.environ['USER_EMAIL'] = pending_user.email
        os.environ['USER_ID'] = "a_gaia_id"

        with self.assertNumQueries(7):
            resp = self.client.get(reverse('index'))

        self.assertFalse(
            PendingUser.objects.filter(pk=pending_user.pk).exists())

        new_user = get_user_model().objects.get(email=pending_user.email)
        self.assertTrue(new_user.is_whitelisted)

    def test_new_admin(self):
        """
            User is app engine admin
        """
        user = milkman.deliver(
            get_user_model(),
            email="user@example.com",
            is_superuser=False)

        self._sign_in(user)
        os.environ['USER_IS_ADMIN'] = '1'

        resp = self.client.get(reverse('index'))
        self.assertEqual(200, resp.status_code)

        user = self.reload(user)

        self.assertTrue(user.is_superuser)

    def test_revoked_admin(self):
        """
            User used to be an app engine admin
        """
        self._sign_in(self.admin)
        os.environ['USER_IS_ADMIN'] = '0'

        resp = self.client.get(reverse('index'))
        self.assertEqual(200, resp.status_code)

        self.admin = self.reload(self.admin)

        self.assertFalse(self.admin.is_superuser)


def get_mock_retrieve_url(content='dummy-content', status_code=200):
    """
        Returns method to mock _mock_retrieve_url in urlfetch
    """
    def _mock_retrieve_url(
            url, payload, method, headers, request, response, *args, **kwargs):
        response.set_content(content)
        response.set_statuscode(status_code)

    return _mock_retrieve_url


class YTThumbnailViewTestCase(AppengineTestBed):
    """
        Tests the view to retrieve YouTube video thumbnail views
    """
    yt_id = 'test-yt-id'
    at_milliseconds = 42

    @mock.patch.object(
            URLFetchServiceStub,
            "_RetrieveURL",
            wraps=get_mock_retrieve_url())
    def test_get_thumbnail_fresh(self, _RetrieveURL):
        """
            Get a YT thumbnail that is not yet cached
        """
        resp = self.client.get(reverse('yt_thumbnail') + "?id={0}&ats={1}".format(
            self.yt_id, self.at_milliseconds))

        self.assertEqual(
            'http://img.youtube.com/vd?id={0}&ats={1}'.format(
                self.yt_id, self.at_milliseconds),
            _RetrieveURL.call_args[0][0])

        self.assertEqual(200, resp.status_code)
        self.assertEqual('dummy-content', resp.content)

        self.assertTrue(self.img_in_cache())

    @mock.patch.object(
            URLFetchServiceStub,
            "_RetrieveURL",
            wraps=get_mock_retrieve_url())
    def test_get_thumbnail_cached(self, _RetrieveURL):
        """
            Get a YT thumbnail get is already cached
        """
        self.add_img_to_cache()

        resp = self.client.get(
            reverse('yt_thumbnail') + "?id={0}&ats={1}".format(
                self.yt_id, self.at_milliseconds))

        self.assertFalse(_RetrieveURL.called)

        self.assertEqual(200, resp.status_code)
        self.assertEqual('dummy-content', resp.content)

        self.assertTrue(self.img_in_cache())

    @mock.patch.object(
            URLFetchServiceStub,
            "_RetrieveURL",
            wraps=get_mock_retrieve_url(status_code=404))
    def test_get_thumbnail_404(self, _RetrieveURL):
        """
            Get a YT thumbnail that returns 404
        """
        resp = self.client.get(
            reverse('yt_thumbnail') + "?id={0}&ats={1}".format(
                self.yt_id, self.at_milliseconds))

        self.assertEqual(404, resp.status_code)
        self.assertEqual('dummy-content', resp.content)

        self.assertFalse(self.img_in_cache())

    def add_img_to_cache(self):
        """
            Helper method to add a thumbnail img to the cache
        """
        with gcs.open(
            "/greenday-project-v02-local.appspot.com/gd-yt-thumbs/{yt_id}/ytthumb-{yt_id}-{ms}".format(
                yt_id=self.yt_id, ms=self.at_milliseconds), 'w') as f:
            f.write('dummy-content')

    def img_in_cache(self):
        """
            Returns True if the thumbnail image is in the cache
        """
        return blobstore.get(
            blobstore.create_gs_key(
                "/gs/greenday-project-v02-local.appspot.com/gd-yt-thumbs/{yt_id}/ytthumb-{yt_id}-{ms}".format(
                    yt_id=self.yt_id, ms=self.at_milliseconds)
            )
        )

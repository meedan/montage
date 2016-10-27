"""
    Tests for :mod:`greenday_core.user_deletion <greenday_core.user_deletion>`
"""
import datetime
import mock
from milkman.dairy import milkman

from django.contrib.auth import get_user_model

from .base import AppengineTestBed

from ..constants import EventKind
from ..models import get_sentinel_user
from ..user_deletion import delete_user, defer_delete_user
from ..email_templates import USER_DELETED


class UserDeletionTestCase(AppengineTestBed):
    """
        User deletion tests
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(UserDeletionTestCase, self).setUp()
        User = get_user_model()

        # override
        self.admin = milkman.deliver(
            User, email="admin@foobar.com", is_superuser=True)
        self.user = milkman.deliver(User, email="user@example.com")

    @mock.patch("deferred_manager.defer")
    @mock.patch("django.utils.timezone.now")
    def test_defer_delete_user(self, mock_now, mock_defer):
        """
            Tests :func:`greenday_core.user_deletion.defer_delete_user <greenday_core.user_deletion.defer_delete_user>`
            defers a call to :func:`greenday_core.user_deletion.delete_user <greenday_core.user_deletion.delete_user>`
        """
        now = datetime.datetime(2014, 1, 1)
        mock_now.return_value = now

        defer_delete_user(self.user, deleted_by_user=self.admin)

        mock_defer.assert_called_once_with(
            delete_user,
            self.user.pk,
            deleted_by_user_id=self.admin.pk,
            email_user=True,
            task_reference="user-{0:d}".format(self.user.pk),
            unique_until=now + datetime.timedelta(hours=2),
            _queue="user-deletion"
        )

    @mock.patch("deferred_manager.defer")
    @mock.patch("django.utils.timezone.now")
    def test_defer_delete_user_no_email(self, mock_now, mock_defer):
        """
            Tests :func:`greenday_core.user_deletion.defer_delete_user <greenday_core.user_deletion.defer_delete_user>`
            defers a call to :func:`greenday_core.user_deletion.delete_user <greenday_core.user_deletion.delete_user>`
            and ensures that if the flag is passed to not email user, that an email is not raised.
        """
        now = datetime.datetime(2014, 1, 1)
        mock_now.return_value = now

        defer_delete_user(self.user, deleted_by_user=self.admin, email_user=False)

        mock_defer.assert_called_once_with(
            delete_user,
            self.user.pk,
            deleted_by_user_id=self.admin.pk,
            email_user=False,
            task_reference="user-{0:d}".format(self.user.pk),
            unique_until=now + datetime.timedelta(hours=2),
            _queue="user-deletion"
        )

    @mock.patch("greenday_core.user_deletion.publish_appevent")
    @mock.patch("greenday_core.user_deletion.send_email")
    def test_delete_user_no_email(self, mock_send_mail, mock_publish_appevent):
        """
            Tests :func:`greenday_core.user_deletion.delete_user <greenday_core.user_deletion.delete_user>`
            where a notification email is not sent to the the deleted user.
        """
        delete_user(self.user.pk, email_user=False)

        self.assertObjectAbsent(self.user)

        # check no email sent.
        self.assertFalse(mock_send_mail.called)

        mock_publish_appevent.assert_called_once_with(
            EventKind.USERDELETED,
            object_id=self.user.pk,
            user=get_sentinel_user())

    @mock.patch("greenday_core.user_deletion.publish_appevent")
    @mock.patch("greenday_core.user_deletion.send_email")
    def test_delete_user(self, mock_send_mail, mock_publish_appevent):
        """
            Tests :func:`greenday_core.user_deletion.delete_user <greenday_core.user_deletion.delete_user>`
        """
        delete_user(self.user.pk)

        self.assertObjectAbsent(self.user)

        mock_send_mail.assert_called_with(
            "Your Montage account has been deleted",
            USER_DELETED,
            self.user.email
        )

        mock_publish_appevent.assert_called_once_with(
            EventKind.USERDELETED,
            object_id=self.user.pk,
            user=get_sentinel_user())

    @mock.patch("greenday_core.user_deletion.publish_appevent")
    @mock.patch("greenday_core.user_deletion.send_email")
    def test_delete_user_by_admin(self, mock_send_mail, mock_publish_appevent):
        """
            Tests :func:`greenday_core.user_deletion.delete_user <greenday_core.user_deletion.delete_user>`
            where a user is deleted by an admin rather than deleting themself
        """
        delete_user(self.user.pk, deleted_by_user_id=self.admin.pk)

        self.assertObjectAbsent(self.user)

        mock_send_mail.assert_called_with(
            "Your Montage account has been deleted",
            USER_DELETED,
            self.user.email
        )

        mock_publish_appevent.assert_called_once_with(
            EventKind.USERDELETED,
            object_id=self.user.pk,
            user=self.admin)

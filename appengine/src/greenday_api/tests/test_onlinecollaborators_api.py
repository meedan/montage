"""
    Tests for :mod:`greenday_api.misc.onlinecollaborators_api <greenday_api.misc.onlinecollaborators_api>`
"""
from milkman.dairy import milkman

from greenday_core.api_exceptions import ForbiddenException, NotFoundException

from greenday_core.models import Project
from greenday_channel.onlinecollaborators import OnlineCollaboratorsManager

from .base import ApiTestCase

from ..common.containers import IDContainer
from ..misc.onlinecollaborators_api import OnlineCollaboratorsAPI


class OnlineProjectCollaboratorsAPITests(ApiTestCase):
    """
        Test case for
        :class:`greenday_api.misc.onlinecollaborators_api.OnlineCollaboratorsAPI <greenday_api.misc.onlinecollaborators_api.OnlineCollaboratorsAPI>`
    """
    api_type = OnlineCollaboratorsAPI

    def setUp(self):
        """
            Set up test case with a project and an online user
        """
        super(OnlineProjectCollaboratorsAPITests, self).setUp()

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)

        manager = OnlineCollaboratorsManager(self.project.pk)
        manager.add_collaborator(self.user, 'dummy-token')

    def test_ok(self):
        """
            One user online
        """
        self._sign_in(self.admin)

        request = IDContainer.combined_message_class(id=self.project.pk)
        response = self.api.get_online_project_collaborators(request)

        self.assertEqual(1, len(response.items))

        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'profile_img_url',
            'google_plus_profile',
        )

        for field in fields:
            expected = getattr(self.user, field)
            actual = getattr(response.items[0], field)
            self.assertEqual(
                expected,
                actual)

        self.assertTrue(response.items[0].timestamp)
        self.assertEqual(self.project.pk, response.items[0].project_id)

    def test_404(self):
        """
            Project doesn't exist
        """
        self._sign_in(self.admin)

        request = IDContainer.combined_message_class(id=999)
        self.assertRaises(
            NotFoundException,
            self.api.get_online_project_collaborators,
            request)

    def test_not_assigned(self):
        """
            Signed in user not assigned to project
        """
        self._sign_in(self.user)

        request = IDContainer.combined_message_class(id=self.project.pk)
        self.assertRaises(
            ForbiddenException,
            self.api.get_online_project_collaborators,
            request)

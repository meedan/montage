"""
    Defines Online Collaborators API
"""
# FRAMEWORK
import endpoints

from greenday_channel.onlinecollaborators import OnlineCollaboratorsManager

from ..api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required
)
from ..project.mixins import ProjectAPIMixin
from ..mapper import GeneralMapper
from ..common.containers import IDContainer

from .messages import OnlineCollaboratorsList, OnlineCollaboratorMessage

@greenday_api.api_class(
    resource_name='online_collaborators',
    auth_level=endpoints.AUTH_LEVEL.REQUIRED)
class OnlineCollaboratorsAPI(BaseAPI, ProjectAPIMixin):
    """
        API to get a list of online collaborators for a resource

        Object disposed after request is completed.
    """
    def __init__(self, *args, **kwargs):
        super(OnlineCollaboratorsAPI, self).__init__(*args, **kwargs)
        self.mapper = GeneralMapper(None, OnlineCollaboratorMessage)

    @greenday_method(
        IDContainer,
        OnlineCollaboratorsList,
        path='project/{id}/collaborators',
        http_method='GET',
        name='online_collaborators_for_project',
        pre_middlewares=[auth_required])
    def get_online_project_collaborators(self, request):
        """
            Gets a list of online collaborators for the given project
        """
        # auth & confirm valid project ID
        self.get_project(
            request.id,
            assigned_only=True
        )

        manager = OnlineCollaboratorsManager(request.id)
        collaborators = manager.get_collaborators()

        return OnlineCollaboratorsList(
            items=[
                self.mapper.map(c, project_id=request.id)
                for c in collaborators.values()
            ],
            is_list=True
        )

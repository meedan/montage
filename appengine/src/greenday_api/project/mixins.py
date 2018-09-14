"""
    Defines API mixins related to projects
"""
from greenday_core.api_exceptions import ForbiddenException
from greenday_core.models import Project

from ..utils import get_obj_or_api_404


class ProjectAPIMixin(object):
    """
        Provides commonly used API helper methods related to projects

        TODO: move this to greenday_api.common
    """
    def get_project(
            self,
            project_id,
            assigned_only=False,
            check_fn=None,
            queryset=None):
        """
            Gets a project entity and enforces permissions

            assigned_only: True if the current_user must be assigned to
            the project
            check_fn: Allows an arbitrary function to be passed in to check
            permissions. I.e. check_fn=lambda p: p.is_owner(self.current_user)
        """
        assert not (assigned_only and check_fn), "Cannot use assigned_only with check_fn"

        if assigned_only:
            check_fn = lambda p: p.is_assigned(self.current_user)

        project = get_obj_or_api_404(
            (queryset or Project.objects)
            .with_videos(),
            pk=project_id)

        if check_fn and not check_fn(project):
            raise ForbiddenException

        return project

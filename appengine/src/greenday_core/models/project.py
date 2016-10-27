"""
    Defines models related to Projects
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ..utils import CONDITIONAL_CASCADE

from .base import BaseModel, TrashableMixin
from .managers import ProjectManager, ProjectQuerySet
from .user import User, PendingUser


class Project(BaseModel, TrashableMixin):
    """
        Project model.
        Extends from TrashableMixin to gives us soft delete
        functionality.
    """
    # Went for a privacy code system rather than boolean for
    # privacy. This is future proofing in case the client decides
    # to add extra privacy types at some point down the line.
    PRIVATE = 1
    PUBLIC = 2
    PRIVACY_CODES = (
        (PRIVATE, _('Private')),
        (PUBLIC, _('Public'))
    )

    name = models.CharField(max_length=200)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProjectUser",
        related_name="projects")

    description = models.TextField(null=True, blank=True)

    image_gcs_filename = models.CharField(
        max_length=500, null=True, blank=True)
    image_url = models.TextField(blank=True, null=True)

    # TODO: We need to actually implement these
    # permissions at endpoints level e.g project search etc should only
    # return non-private projects. This code is a basic start so that CanY
    # and I can get these things set in the front end.
    privacy_project = models.IntegerField(
        choices=PRIVACY_CODES, default=PRIVATE,
        verbose_name=_('Project privacy'))
    privacy_tags = models.IntegerField(
        choices=PRIVACY_CODES, default=PUBLIC,
        verbose_name=_('Tag privacy'))

    # denormalised
    video_tag_instance_count = models.PositiveIntegerField(default=0)

    objects = ProjectManager()
    all_objects = ProjectQuerySet.as_manager()

    @property
    def tags_is_private(self):
        """
            Are tags created within this project accessible from other projects?
        """
        return self.privacy_tags == self.PRIVATE

    @property
    def is_private(self):
        """
            Is this project private to assignees only?
        """
        return self.privacy_project == self.PRIVATE

    @property
    def assigned_users(self):
        """
            Gets all users assigned to this project
        """
        return (
            self.users.filter(projectusers__is_pending=False)
                .filter(projectusers__is_assigned=True)
            )

    @property
    def admins(self):
        """
            Gets all users who are admins on this project?
        """
        return (
            self.users.filter(projectusers__is_pending=False)
                .filter(projectusers__is_admin=True)
            )

    @property
    def owner(self):
        """
            Gets the project owner
        """
        if not hasattr(self, '_owner'):
            self._owner = next(
                self.users.filter(projectusers__is_owner=True).iterator(),
                None)
        return self._owner

    def get_user_relation(self, user, cached=False):
        """
            Takes a User or PendingUser object and gets the ProjectUser object
            that links that user to this project.

            Caches the result to the project object
        """
        if not hasattr(self, "_user_relation"):
            self._user_relation = {}

        if not cached or user.email not in self._user_relation:
            try:
                self._user_relation[user.email] = self.projectusers.get(
                    **{
                        "pending_user"
                        if isinstance(user, PendingUser)
                        else "user": user
                    })
            except ProjectUser.DoesNotExist:
                return

        return self._user_relation.get(user.email)

    def get_user_relation_perm_attr(self, user, attr_fn):
        """
            Gets a user's permissions on a project and returns the results of
            an arbitrary function on that permission object
        """
        user_relation = self.get_user_relation(user, cached=True)
        if user_relation:
            return (not user_relation.is_pending) and attr_fn(user_relation)

        return False

    def is_owner_or_admin(self, user):
        """
            Is the user an owner or an admin on the project
        """
        return self.is_owner(user) or self.is_admin(user)

    def is_owner(self, user):
        """
            Is the user the project's owner
        """
        return self.get_user_relation_perm_attr(user, lambda ur: ur.is_owner)

    def is_admin(self, user):
        """
            Is the user an admin on the project?
        """
        return self.get_user_relation_perm_attr(user, lambda ur: ur.is_admin)

    def is_assigned(self, user):
        """
            Is the user assigned to the project?
        """
        return self.get_user_relation_perm_attr(
            user, lambda ur: ur.is_assigned)

    def set_owner(self, user):
        """
            Sets the user as the project owner.

            Raises AssertionError if the project already has an owner set.
        """
        assert isinstance(user, User)

        has_current_owner = (
            self.projectusers
            .filter(is_pending=False)
            .filter(is_owner=True)
        ).exists()
        assert not has_current_owner, "Owner already set"

        user_relation, created = ProjectUser.objects.get_or_create(
            user=user,
            project=self,
            defaults={'is_owner': True, 'is_assigned': True, 'is_admin': True})

        if not created:
            user_relation.is_assigned = user_relation.is_admin = True
            user_relation.is_owner = True

            user_relation.save()

        self._owner = user
        if (hasattr(self, '_user_relation') and
                user.email in self._user_relation):
            self._user_relation[user.email]

        return user_relation

    def set_updates_viewed(self, user, last_viewed_at=None):
        """
            Sets the last time that a user viewed events on the project
        """
        last_viewed_at = last_viewed_at or timezone.now()

        user_relation = self.get_user_relation(user)

        if user_relation:
            user_relation.last_updates_viewed = last_viewed_at
            user_relation.save()

    def add_admin(self, user, pending=True):
        """
            Adds the user as a project admin
        """
        defaults = {
            'is_admin': True,
            'is_assigned': True,
            'is_pending': pending
        }

        project_user_get_args = {
            "project": self,
            "pending_user"
            if isinstance(user, PendingUser)
            else "user": user
        }
        user_relation, created = ProjectUser.objects.get_or_create(
            defaults=defaults,
            **project_user_get_args)

        if not created or not user_relation.is_admin:
            for k, v in defaults.items():
                setattr(user_relation, k, v)
            user_relation.save()

        if (hasattr(self, '_user_relation') and
                user.email in self._user_relation):
            self._user_relation[user.email]

        return user_relation

    def add_assigned(self, user, pending=True):
        """
            Adds the user to the project as an assigned user
        """
        defaults = {
            'is_assigned': True,
            'is_pending': pending
        }

        project_user_get_args = {
            "project": self,
            "pending_user"
            if isinstance(user, PendingUser)
            else "user": user
        }

        user_relation, created = ProjectUser.objects.get_or_create(
            defaults=defaults, **project_user_get_args)

        if not created or not user_relation.is_assigned:
            for k, v in defaults.items():
                setattr(user_relation, k, v)
            user_relation.save()

        if (hasattr(self, '_user_relation') and
                user.email in self._user_relation):
            self._user_relation[user.email]

        return user_relation

    def remove_user(self, user):
        """
            Removes the user from the project
        """
        user_relation = self.get_user_relation(user)
        if user_relation:
            user_relation.delete()

        if (hasattr(self, '_user_relation') and
                user.email in self._user_relation):
            self._user_relation[user.email]

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['-created']


def project_user_has_user_id(project_user_object):
    """
        Returns True if the ProjectUser has a user_id set on it

        Needs to be set as a module member as it's passed to CONDITIONAL_CASCADE
    """
    return not project_user_object.user_id


class ProjectUser(BaseModel):
    """
        Represents the relationship between a user and a project
    """
    class Meta:
        unique_together = ('project', 'user',)

    project = models.ForeignKey(Project, related_name="projectusers")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="projectusers",
        null=True,
        on_delete=models.CASCADE)
    pending_user = models.ForeignKey(
        PendingUser,
        related_name="projectusers",
        null=True,
        blank=True,
        on_delete=CONDITIONAL_CASCADE(project_user_has_user_id))

    is_pending = models.BooleanField(default=False)
    is_assigned = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)
    last_updates_viewed = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u"User {user_id} ({email}) on project "\
               "{project.pk} ({project.name})".format(
            user_id=self.user_id,
            email=self.user.email if self.user else '',
            project=self.project)

    def save(self, *args, **kwargs):
        """
            Override save() to set the is_pending field
        """
        if self.pending_user and not self.user:
            self.is_pending = True
        super(ProjectUser, self).save(*args, **kwargs)

"""
    Defines Django models for users
"""
from django.db import models
from django.contrib.auth.models import AbstractUser

from .base import BaseModel


class User(AbstractUser):
    """
        User model
    """
    accepted_nda = models.BooleanField(default=False)
    gaia_id = models.CharField(
        verbose_name=u'GAIA id',
        max_length=200,
        blank=True,
        null=True,
    )
    is_googler = models.BooleanField(
        verbose_name=u'Is Googler?',
        default=False,
    )
    profile_img_url = models.URLField(
        verbose_name=u"Profile image",
        max_length=300,
        blank=True,
        null=True,
    )
    google_plus_profile = models.URLField(
        verbose_name=u"Google+ profile",
        max_length=300,
        blank=True,
        null=True,
    )
    language = models.CharField(
        verbose_name=u'User Language',
        max_length=200,
        blank=True,
        null=True,
        default='en'
    )
    is_whitelisted = models.BooleanField(
        verbose_name=u"Is whitelisted?",
        default=True
    )

    @property
    def is_external(self):
        """
            Is not a googler
        """
        return not self.is_googler

    @property
    def ldap(self):
        """
            Gets part of email address before '@'
        """
        return self.email[:self.email.find('@')]

    @property
    def name(self):
        """
            Gets the user's full name
        """
        return "{0} {1}".format(self.first_name, self.last_name)

    def delete(self, *args, **kwargs):
        """
            Override delete to also delete all of a user's projects
        """
        owner_of_projects = list(
            self.projectusers.filter(is_owner=True)
            .values_list("project_id", flat=True)
        )

        super(User, self).delete(*args, **kwargs)

        from greenday_core.models.project import Project
        Project.all_objects.filter(pk__in=owner_of_projects).delete()

    def __unicode__(self):
        return self.email


class PendingUser(BaseModel):
    """
        Model to hold details of a user who has been invited to the system but
        has not yet accessed it
    """
    email = models.EmailField(blank=True, unique=True)
    user = models.OneToOneField(
        User, null=True,
        related_name="pending_user",
        on_delete=models.CASCADE)
    is_whitelisted = models.BooleanField(default=False)

    def __unicode__(self):
        return self.email


def get_sentinel_user():
    """
        Gets a single user used to indicate a deleted user.

        Allows us to update references to a single deleted entity
        if we don't cascade the delete to them
    """
    return User.objects.get_or_create(
        username='deleted',
        defaults={"first_name": "Deleted"})[0]

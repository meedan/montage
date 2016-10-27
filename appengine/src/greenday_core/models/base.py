"""
    Defines mixin classes and the base model for all models
"""
from django.contrib.contenttypes import generic
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .managers import (
    UnarchivedManager,
    ArchivedManager,
    NonTrashedManager,
    TrashedManager,
)


class TrashableMixin(models.Model):
    """
        Adds soft delete behaviour to a model
    """
    trashed_at = models.DateTimeField(
        _('Trashed'), editable=False, blank=True, null=True)

    objects = NonTrashedManager()
    trash = TrashedManager()

    def delete(self, trash=True, *args, **kwargs):
        """
            Override delete to set trashed_at

            If trashed_at is not null then the object is deleted
        """
        if not self.trashed_at and trash:
            self.trashed_at = timezone.now()
            self.save()
        else:
            super(TrashableMixin, self).delete(*args, **kwargs)

    def restore(self, commit=True):
        """
            Restores the trashed object
        """
        self.trashed_at = None
        if commit:
            self.save()

    class Meta:
        abstract = True


class BaseModel(models.Model):
    """
        Base abstract base class to give creation and modified times
    """
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
            Override save() to update modified field
        """
        self.modified = timezone.now()
        return super(BaseModel, self).save(*args, **kwargs)

    def fill_prefetch_cache(self, field, queryset):
        """
            Manually fills the prefetch cache with a queryset.

            Use this sparingly and only if you know what you're doing or
            things may go wrong.
        """
        if hasattr(self, "_prefetched_objects_cache"):
            assert field not in self._prefetched_objects_cache, \
                "field already cached"
        else:
            self._prefetched_objects_cache = {}

        self._prefetched_objects_cache[field] = queryset


class TaggableMixin(models.Model):
    """
        Taggable Mixin class for generic attributes across
        various tag models.
    """
    tags = generic.GenericRelation(
        "TagInstance",
        object_id_field="tagged_object_id",
        content_type_field="tagged_content_type")

    class Meta:
        abstract = True


class ArchivableMixin(models.Model):
    """
        Mixin to allow an entity to be archived
    """
    class Meta:
        abstract = True

    archived_at = models.DateTimeField(null=True)

    all_objects = models.Manager()
    unarchived_objects = UnarchivedManager()
    archived_objects = ArchivedManager()

    def archive(self, save=True):
        """
            Set the object as archived
        """
        self.archived_at = timezone.now()
        if save:
            self.save()

    def unarchive(self, save=True):
        """
            Set the object as unarchived
        """
        self.archived_at = None
        if save:
            self.save()

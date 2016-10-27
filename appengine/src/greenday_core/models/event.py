"""
    Defines the model to hold application events
"""
from django.conf import settings
from django.db import models
from django.forms.models import model_to_dict

from ..constants import EventKind, EventModel, EventCommonCodes, CODES_PER_MODEL

from .user import get_sentinel_user


class Event(models.Model):
    """
        Represents an application event
    """
    class Meta:
        ordering = ['-timestamp', '-pk']

    timestamp = models.DateTimeField()
    kind = models.IntegerField(EventKind.choices)
    object_kind = models.IntegerField()
    event_kind = models.IntegerField()
    object_id = models.IntegerField(null=True)
    project_id = models.IntegerField(null=True)
    video_id = models.IntegerField(null=True)
    meta = models.TextField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="actions",
        on_delete=models.SET(get_sentinel_user),
        db_constraint=False)

    @property
    def object_type(self):
        """
            Gets the :class:`greenday_core.constants.EventModel <greenday_core.constants.EventModel>`
            enum type of this object
        """
        return EventModel(self.kind/CODES_PER_MODEL).name

    @property
    def event_type(self):
        """
            Gets the :class:`greenday_core.constants.EventKind <greenday_core.constants.EventKind>`
            enum type of this object
        """
        code = self.kind % CODES_PER_MODEL

        try:
            common_code = EventCommonCodes(code)
        except ValueError:
            return EventKind(self.kind).name
        else:
            return common_code.name

    def to_dict(self):
        """
            Return dict of the object's field data
        """
        d = model_to_dict(self)
        d.update({
            "object_type": self.object_type,
            "event_type": self.event_type
        })
        return d

    def save(self, *args, **kwargs):
        """
            Override save to get the `object_kind` and `event_kind` from the compound `kind` field
        """
        self.object_kind, self.event_kind = divmod(self.kind, CODES_PER_MODEL)
        return super(Event, self).save(*args, **kwargs)

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return "{kind}(id={id}, project_id={project_id}, \
by {email} at {timestamp}".format(
            kind=EventKind(self.kind).name,
            id=self.object_id,
            project_id=self.project_id,
            email=self.user.email if self.user else "<none>",
            timestamp=self.timestamp
        )

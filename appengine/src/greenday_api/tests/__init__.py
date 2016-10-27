"""
    Unit tests for the Montage API
"""

from django.db import models


# here because the nose runner doesn't find models in the
# other modules within this package
class DummyModel(models.Model):
    """
        A dummy Django model
    """
    foo = models.CharField(null=True, blank=True, max_length=100)
    bar = models.ForeignKey("DummyRelatedModel", null=True)
    whizz_id = models.IntegerField(null=True)


class DummyRelatedModel(models.Model):
    """
        A dummy Django model with an FK to DummyModel
    """
    foobar = models.ForeignKey("DummyModel", null=True, related_name="foobars")

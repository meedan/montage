"""
    Tests for :mod:`greenday_api.mapper <greenday_api.mapper>`
"""
from protorpc import messages

# FRAMEWORK
from django.test import TestCase

# GREENDAY
from ..mapper import GeneralMapper

from . import DummyModel, DummyRelatedModel


class DummyMessage(messages.Message):
    """
        Dummy protorpc message
    """
    foo = messages.StringField(1, required=False)
    bar_id = messages.IntegerField(2, required=False)
    foobar_ids = messages.IntegerField(3, required=False, repeated=True)
    whizz_id = messages.IntegerField(4, required=False)


class TestBaseMapper(TestCase):
    """
        Test case for
        :class:`greenday_api.mapper.GeneralMapper <greenday_api.mapper.GeneralMapper>`
    """
    def setUp(self):
        """
            Create mapper
        """
        super(TestBaseMapper, self).setUp()

        self.mapper = GeneralMapper(DummyModel, DummyMessage)

    def test_basic_mapping(self):
        """
            Basic field mapping
        """
        dummy_model = DummyModel.objects.create(foo="foobar")

        message = self.mapper.map(dummy_model)

    def test_foreign_key_mapping(self):
        """
            Mapping of foreign key fields by convention
        """
        related_model = DummyRelatedModel.objects.create()
        dummy_model = DummyModel.objects.create(bar=related_model)

        message = self.mapper.map(dummy_model)

        self.assertEqual(related_model.id, message.bar_id)

    def test_one_to_many_mapping(self):
        """
            One to many mapping (I.e. Django model set fields)
        """
        dummy_model = DummyModel.objects.create()
        related_model = DummyRelatedModel.objects.create(foobar=dummy_model)
        related_model_2 = DummyRelatedModel.objects.create(foobar=dummy_model)

        message = self.mapper.map(dummy_model)

        self.assertEqual(
            [related_model.id, related_model_2.id], message.foobar_ids)

    def test_field_ending_in_id(self):
        """
            Field defined ending in _id.

            Makes sure that FK mapping doesn't break this.
        """
        dummy_model = DummyModel.objects.create(whizz_id=42)

        message = self.mapper.map(dummy_model)

        self.assertEqual(message.whizz_id, 42)

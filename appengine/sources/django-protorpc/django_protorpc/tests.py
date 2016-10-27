from protorpc import message_types, messages
from django.db import models
from django.test import TestCase

from .messages import DjangoProtoRPCMessage, nest_message


class DummyModel(models.Model):
    foo = models.CharField(null=False, blank=False, max_length=100)
    bar = models.ForeignKey("DummyRelatedModel", null=True)
    whizz_id = models.IntegerField(null=True)
    default = models.BooleanField(default=False)


class DummyNumberModel(models.Model):
    f1 = models.ForeignKey("DummyRelatedModel", null=True)
    f2 = models.IntegerField(null=True)
    f3 = models.PositiveIntegerField(null=True)
    f4 = models.SmallIntegerField(null=True)
    f5 = models.PositiveSmallIntegerField(null=True)
    f6 = models.BigIntegerField(null=True)
    f7 = models.FloatField(null=True)
    f8 = models.DecimalField(null=True, decimal_places=2, max_digits=2)


class DummyRelatedModel(models.Model):
    foobar = models.ForeignKey("DummyModel", null=True, related_name="foobars")


class DjangoProtoRPCMessagesTests(TestCase):
    def assertIsSubclass(self, child, parent):
        self.assertTrue(issubclass(child, parent),
                        "{0} is not a subclass of {1}".format(child, parent))

    def test_make_basic_message(self):
        class MockMessage(DjangoProtoRPCMessage):
            foo = messages.StringField(1)
            bar = message_types.DateTimeField(2)

        self.assertIsSubclass(MockMessage, messages.Message)
        self.assertEqual(MockMessage.foo.number, 1)
        self.assertEqual(MockMessage.bar.number, 2)

    def test_nested_message(self):
        class NestedMessage(DjangoProtoRPCMessage):
            foo = messages.StringField(1)
            foobar = messages.StringField(2)
            conflict = messages.StringField(3)
            a_date = message_types.DateTimeField(4)

        class MockMessage(DjangoProtoRPCMessage):
            bar = messages.StringField(1)
            nested = nest_message(NestedMessage, 2)
            conflict = messages.IntegerField(3)
            a_list = messages.MessageField(NestedMessage, 4, repeated=True)

        self.assertIsSubclass(MockMessage, messages.Message)
        self.assertEqual(MockMessage.bar.number, 1)

        self.assertEqual(MockMessage.foo.number, 2)
        self.assertEqual(MockMessage.foobar.number, 3)

        # ordinal 4 will be missing. this would have been
        # NestedMessage.conflict but this would be replaced

        self.assertEqual(MockMessage.a_date.number, 5)

        # master field shown take precendence over nested
        self.assertEqual(MockMessage.conflict.number, 6)
        self.assertIsInstance(MockMessage.conflict, messages.IntegerField)

        self.assertEqual(MockMessage.a_list.number, 7)
        self.assertTrue(MockMessage.a_list.repeated)

    def test_basic_model_message(self):
        class MockMessage(DjangoProtoRPCMessage):
            class Meta:
                model = DummyModel

        self.assertIsSubclass(MockMessage, messages.Message)
        self.assertIsInstance(MockMessage.foo, messages.StringField)
        self.assertIsInstance(MockMessage.whizz_id, messages.IntegerField)
        self.assertIsInstance(MockMessage.bar_id, messages.IntegerField)
        self.assertIsInstance(MockMessage.default, messages.BooleanField)

        self.assertTrue(MockMessage.foo.required)
        self.assertFalse(MockMessage.default.required)

        self.assertFalse(hasattr(MockMessage, 'bar'))
        self.assertFalse(hasattr(MockMessage, 'foobars'))
        self.assertFalse(hasattr(MockMessage, 'foobar_ids'))

    def test_basic_model_message_with_fields(self):
        class MockMessage(DjangoProtoRPCMessage):
            class Meta:
                model = DummyModel
                fields = ('foo',)

        self.assertIsSubclass(MockMessage, messages.Message)
        self.assertIsInstance(MockMessage.foo, messages.StringField)
        self.assertFalse(hasattr(MockMessage, 'whizz_id'))
        self.assertFalse(hasattr(MockMessage, 'bar_id'))
        self.assertFalse(hasattr(MockMessage, 'bar'))
        self.assertFalse(hasattr(MockMessage, 'foobar_ids'))
        self.assertFalse(hasattr(MockMessage, 'foobars'))

        self.assertTrue(MockMessage.foo.required)

    def test_basic_model_message_with_excludes(self):
        class MockMessage(DjangoProtoRPCMessage):
            class Meta:
                model = DummyModel
                exclude = ('bar',)

        self.assertIsSubclass(MockMessage, messages.Message)
        self.assertIsInstance(MockMessage.foo, messages.StringField)
        self.assertIsInstance(MockMessage.whizz_id, messages.IntegerField)

        self.assertTrue(MockMessage.foo.required)

        self.assertFalse(hasattr(MockMessage, 'bar_id'))
        self.assertFalse(hasattr(MockMessage, 'bar'))
        self.assertFalse(hasattr(MockMessage, 'foobars'))
        self.assertFalse(hasattr(MockMessage, 'foobar_ids'))

    def test_basic_model_include_related(self):
        class MockMessage(DjangoProtoRPCMessage):
            class Meta:
                model = DummyModel
                include_related_ids = True

        self.assertIsSubclass(MockMessage, messages.Message)
        self.assertIsInstance(MockMessage.foo, messages.StringField)
        self.assertIsInstance(MockMessage.whizz_id, messages.IntegerField)
        self.assertIsInstance(MockMessage.bar_id, messages.IntegerField)
        self.assertIsInstance(MockMessage.foobar_ids, messages.IntegerField)

        self.assertTrue(MockMessage.foobar_ids.repeated)
        self.assertTrue(MockMessage.foo.required)

        self.assertFalse(hasattr(MockMessage, 'bar'))
        self.assertFalse(hasattr(MockMessage, 'foobars'))

    def test_basic_model_no_required(self):
        class MockMessage(DjangoProtoRPCMessage):
            class Meta:
                model = DummyModel
                never_required = True

        self.assertIsSubclass(MockMessage, messages.Message)
        self.assertIsInstance(MockMessage.foo, messages.StringField)
        self.assertIsInstance(MockMessage.whizz_id, messages.IntegerField)
        self.assertIsInstance(MockMessage.bar_id, messages.IntegerField)
        self.assertIsInstance(MockMessage.default, messages.BooleanField)

        self.assertFalse(MockMessage.foo.required)
        self.assertFalse(MockMessage.default.required)

        self.assertFalse(hasattr(MockMessage, 'bar'))
        self.assertFalse(hasattr(MockMessage, 'foobars'))
        self.assertFalse(hasattr(MockMessage, 'foobar_ids'))

    def test_number_types_mapping(self):
        class MockMessage(DjangoProtoRPCMessage):
            class Meta:
                model = DummyNumberModel

        self.assertIsSubclass(MockMessage, messages.Message)

        self.assertIsInstance(MockMessage.id, messages.IntegerField)
        self.assertEqual(MockMessage.id.variant, messages.Variant.INT32)

        self.assertIsInstance(MockMessage.f1_id, messages.IntegerField)
        self.assertEqual(MockMessage.f1_id.variant, messages.Variant.INT32)

        self.assertIsInstance(MockMessage.f2, messages.IntegerField)
        self.assertEqual(MockMessage.f2.variant, messages.Variant.INT32)

        self.assertIsInstance(MockMessage.f3, messages.IntegerField)
        self.assertEqual(MockMessage.f3.variant, messages.Variant.UINT32)

        self.assertIsInstance(MockMessage.f4, messages.IntegerField)
        self.assertEqual(MockMessage.f4.variant, messages.Variant.INT32)

        self.assertIsInstance(MockMessage.f5, messages.IntegerField)
        self.assertEqual(MockMessage.f5.variant, messages.Variant.UINT32)

        self.assertIsInstance(MockMessage.f6, messages.IntegerField)
        self.assertEqual(MockMessage.f6.variant, messages.Variant.INT64)

        self.assertIsInstance(MockMessage.f7, messages.FloatField)
        self.assertEqual(MockMessage.f7.variant, messages.Variant.FLOAT)

        self.assertIsInstance(MockMessage.f8, messages.FloatField)
        self.assertEqual(MockMessage.f8.variant, messages.Variant.DOUBLE)

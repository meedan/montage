import os
import logging
from protorpc import message_types, messages

from django.db import models


MODEL_FIELD_MAP = {
    models.AutoField: (
        messages.IntegerField, messages.Variant.INT32, ),
    models.CharField:
        (messages.StringField, None, ),
    models.TextField:
        (messages.StringField, None, ),
    models.IntegerField:
        (messages.IntegerField, messages.Variant.INT32, ),
    models.PositiveIntegerField:
        (messages.IntegerField, messages.Variant.UINT32, ),
    models.SmallIntegerField:
        (messages.IntegerField, messages.Variant.INT32, ),
    models.PositiveSmallIntegerField:
        (messages.IntegerField, messages.Variant.UINT32, ),
    models.BigIntegerField:
        (messages.IntegerField, messages.Variant.INT64, ),
    models.FloatField:
        (messages.FloatField, messages.Variant.FLOAT, ),
    models.DecimalField:
        (messages.FloatField, messages.Variant.DOUBLE, ),
    models.DateTimeField:
        (message_types.DateTimeField, None, ),
    models.URLField:
        (messages.StringField, None, ),
    models.BooleanField:
        (messages.BooleanField, None, ),
    models.EmailField:
        (messages.StringField, None, ),

    models.ForeignKey:
        (messages.IntegerField, messages.Variant.INT32,)
}


class Registry(object):
    """
        A registry to keep track of the messages created by this library
    """

    def __init__(self):
        self.all_messages = {}

    def register_message(self, message_type, django_model=None):
        """
            Adds a messages to the message registry
        """
        self.all_messages[message_type] = {
            "django_model": django_model
        }

registry = Registry()


class DjangoProtoRPCMessageType(type):
    """
        Metaclass to build a protorpc message
    """

    def __new__(cls, clsname, bases, dct):
        if len(bases) and bases[0].__name__ == "DjangoProtoRPCMessage":

            django_model = None
            meta = dct.get('Meta')

            if meta and hasattr(meta, 'model'):
                dct.update(cls.get_model_fields(meta))
                django_model = meta.model

            attrs = dict(cls.get_fields(dct))
            message_type = type(
                clsname, (messages.Message,), attrs)

            registry.register_message(message_type, django_model=django_model)
            return message_type

        return super(DjangoProtoRPCMessageType, cls).__new__(
            cls, clsname, bases, dct)

    @classmethod
    def get_fields(cls, attrs, state=None, level=0):
        """
            Recursively loops through members and returns new fields
            with unique ordinal numbers for the new message type
        """
        if state is None:
            class State(object):
                field_keys = {}
                ordinal = 0
            state = State()

        filtered_attrs = [
            (key, field) for key, field in attrs.items()
            if (isinstance(field, type) and
                issubclass(field, messages.Message)) or
            isinstance(field, messages.Field) or
            isinstance(field, DjangoProtoRPCMessageNested)
        ]

        for key, field in sorted(
                filtered_attrs, key=lambda v: getattr(v[1], "number", 999)):

            if isinstance(field, messages.Field):
                if (
                    # existing conflicting field is more nested than
                    # current field
                    key in state.field_keys and
                        state.field_keys[key] > level or
                    # new field
                    key not in state.field_keys
                ):

                    state.field_keys[key] = level
                    state.ordinal += 1
                    yield key, cls.copyfield(field, state.ordinal)

            elif isinstance(field, type) and issubclass(field,
                                                        messages.Message):
                for key, inner_field in cls.get_fields(
                        vars(field), state, level+1):
                    yield key, inner_field

            elif isinstance(field, DjangoProtoRPCMessageNested):
                for key, inner_field in cls.get_fields(
                        vars(field.message_type), state, level+1):
                    yield key, inner_field

    @classmethod
    def get_model_fields(cls, meta_class):
        if not hasattr(meta_class, "model"):
            raise StopIteration

        model_meta = meta_class.model._meta
        exclude_fields = set(getattr(meta_class, 'exclude', ()))
        fields = set(getattr(meta_class, 'fields', ())) - exclude_fields
        include_related_ids = getattr(meta_class, 'include_related_ids', False)
        never_required = getattr(meta_class, 'never_required', False)

        def should_add_field(model_field_name):
            return ((fields and model_field.name in fields) or
                    (not fields and model_field.name not in exclude_fields))

        for model_field in model_meta.fields:
            if should_add_field(model_field.name):

                field_map = MODEL_FIELD_MAP.get(type(model_field))

                if not field_map:
                    logging.warning(
                        "{0} is not a supported field type - "
                        "not adding to message"
                        .format(type(model_field)))
                    continue

                required = False
                if not never_required:
                    required = not (
                        model_field.null or model_field.has_default())

                message_field = field_map[0](
                    1,
                    required=required,
                    variant=field_map[1])

                name = model_field.name
                if isinstance(model_field, models.ForeignKey):
                    name += "_id"

                yield name, message_field

        if include_related_ids:
            for related_field in model_meta.get_all_related_objects():
                name = related_field.get_accessor_name()

                if (should_add_field(name) and
                   related_field.field.rel.multiple):
                        yield (
                            cls.get_multiple_fk_field_name(name),
                            messages.IntegerField(1, repeated=True)
                        )

            for m2m_field in model_meta.many_to_many:
                if should_add_field(m2m_field.name):
                    yield (
                        cls.get_multiple_fk_field_name(m2m_field.name),
                        messages.IntegerField(1, repeated=True)
                    )

    @classmethod
    def get_multiple_fk_field_name(cls, name):
        if name.endswith('_set'):
            name = name[:-4]

        if name.endswith('s'):
            name = name[:-1]

        return name + "_ids"

    @classmethod
    def copyfield(cls, field, number):
        kwargs = {
            'required': field.required,
            'variant': field.variant,
            'repeated': field.repeated
        }
        if type(field) == messages.MessageField:
            return field.__class__(
                field.message_type,
                number,
                **kwargs
            )

        if not field.repeated and not isinstance(field, messages.MessageField):
            kwargs['default'] = field.default

        return field.__class__(
            number,
            **kwargs
        )


class DjangoProtoRPCMessage(object):
    """
        Defines a ProtoRPC message.

        Used as a base class for ProtoRPC messages in order to derive fields
        from Django models.

        class MockMessageOne(DjangoProtoRPCMessage):
            class Meta:
                model = MyModel
                fields = ('foo', 'bar',)


        class MockMessageTwo(DjangoProtoRPCMessage):
            class Meta:
                model = MyModel
                exclude = ('baz',)

        It also allows you to compose a message using a nested
        hierarchy of message objects. These will be flattened out
        into a protorpc message.

        These types can be nested using the nest_message function:

        class NestedMessage(DjangoProtoRPCMessage):
            foo = messages.StringField(1)
            foobar = messages.StringField(2)
            conflict = messages.StringField(3)

        class MockMessage(DjangoProtoRPCMessage):
            bar = messages.StringField(1)
            nested = nest_message(NestedMessage, 2)
            conflict = messages.IntegerField(3) # overrides the nested field

        Results in the equivalent of...

        class MockMessage(messages.Message):
            bar = messages.StringField(1)
            foo = messages.StringField(2)
            foobar = messages.StringField(3)
            conflict = messages.IntegerField(4)

        In the case of conflicting field names the least nested field will
        be used
    """
    __metaclass__ = DjangoProtoRPCMessageType


class DjangoProtoRPCMessageNested(object):
    """
        Wraps a protorpc message type so that it can be nested
        within an DjangoProtoRPCMessage
    """
    def __init__(self, message_type, number, *args, **kwargs):
        self.message_type = message_type
        self.number = number
        super(DjangoProtoRPCMessageNested, self).__init__(*args, **kwargs)


def nest_message(message_type, number):
    """
        Helper function to nest a protorpc message type within an
        DjangoProtoRPCMessage
    """
    return DjangoProtoRPCMessageNested(message_type, number)

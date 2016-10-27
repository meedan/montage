"""
    Generic mapper implementation
"""
from django.db import models
from django.db.models.fields import related


class GeneralMapper(object):
    """
        Default implementation of a mapper to map Django Models to ProtoRPC
        messages

        Standard field name conventions:
            - FKs are `x_id` and refer to the field `x`
            - M2M are `x_ids` and refer to the field `xs` (plural)
            - If the message field and the model field names match then
                they should also be mapped
    """
    def __init__(self, model_kind, message_kind):
        """
            Creates a mapper

            model_kind: the Django model type to be mapped
            message_kind: the ProtoRPC message type to map to
        """
        self.model_kind = model_kind
        self.message_kind = message_kind

    def map(self, obj, **extra):
        """
            Maps the given object to a protorpc message
        """
        return self.message_kind(**dict(self.get_values(obj, extra)))

    def get_message_field_value_model(self, obj, message_field_name):
        try:
            model_field = self.model_kind._meta.get_field(
                message_field_name)

            if isinstance(model_field, models.ForeignKey):
                return (
                    message_field_name,
                    get_foreign_key(obj, model_field.name)
                )

            if isinstance(model_field, related.ManyToManyField):
                return message_field_name, get_m2m(obj, model_field.name)

            return message_field_name, getattr(
                obj, message_field_name, None)

        except models.FieldDoesNotExist:
            pass

        # maybe it's an FK
        if message_field_name.endswith('_id'):
            try:
                fk_model_field = self.model_kind._meta.get_field(
                    message_field_name[:-3])

                if isinstance(fk_model_field, models.ForeignKey):
                    return (
                        message_field_name,
                        get_foreign_key(obj, fk_model_field.name)
                    )

            except models.FieldDoesNotExist:
                pass

        # or an m2m
        if message_field_name.endswith('_ids'):
            try:
                m2m_model_field = self.model_kind._meta.get_field(
                    message_field_name[:-4] + "s")

                if isinstance(m2m_model_field, related.ManyToManyField):
                    return (
                        message_field_name,
                        get_m2m(obj, m2m_model_field.name)
                    )
            except models.FieldDoesNotExist:
                pass

        # try a few conventions to find an inverse relation
        for name in (
                message_field_name,
                message_field_name + "_set",
                message_field_name[:-4] + "s",
                message_field_name[:-4] + "_set"):

            value = get_m2m(obj, name)

            if value:
                break

        return (
            message_field_name,
            value
        )

    def get_message_field_value(self, obj, message_field_name, **extra):
        """
            Gets the value for a given field on the message type

            The default implementation uses a number of conventions to map
            a Django model to the message field

            This is intended to be overriden for more specific behaviour
        """
        value = None
        if self.model_kind:
            message_field_name, value = self.get_message_field_value_model(
                obj, message_field_name)
        elif isinstance(obj, dict):
            # if we aren't mapping a django model then just try to
            # naively get the attr
            value = obj.get(message_field_name)

        if value is None:
            value = getattr(obj, message_field_name, extra.get(message_field_name))

        # we specifically check for not None now as False Boolean fields
        # were not being returned with the standard ``if value:`` due to
        # the way python's trueness engine works
        if value is not None:
            return message_field_name, value

    def get_values(self, obj, extra):
        """
            Gets all message values as name, value tuples
        """
        for field in self.message_kind.all_fields():
            value = self.get_message_field_value(obj, field.name, **extra)

            if value is not None:
                if not isinstance(value, tuple):
                    value = field.name, value

                yield value


def get_foreign_key(obj, model_field_name):
    """
        Gets the ID of an object named `model_field_name`
        related to `obj` by a foreign key

        Returns None if no relation exists
    """
    return getattr(obj, '{0}_id'.format(model_field_name), None)


def get_m2m(obj, model_field_name):
    """
        Gets list of IDs for objects named `model_field_name`
        holding a foreign key to `obj`

        Returns None if no relation exists.
    """
    related_set = getattr(obj, model_field_name, None)
    if related_set and hasattr(related_set, "get_query_set"):
        return map(int, related_set.values_list("pk", flat=True))

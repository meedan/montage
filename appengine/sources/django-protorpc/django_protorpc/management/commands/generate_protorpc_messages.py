import re
from optparse import make_option

from django.core.management.base import BaseCommand

from django_protorpc.messages import registry

SIGNATURE_TEMPLATE = "class {message_name}(messages.Message):"
FIELD_ATTRIBUTE_TEMPLATE = "    {field_name} = {field_type}({attrs})"


def from_csv(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))


class Command(BaseCommand):
    """
        Prints out a list of message classes
    """

    option_list = BaseCommand.option_list + (
        make_option(
            '--modules',
            '-m',
            dest='modules',
            default=None,
            help='CSV list of modules to recursively load messages from',
            type="string",
            action='callback',
            callback=from_csv),

        make_option(
            '--filter',
            '-f',
            dest='filter_regex',
            default=None,
            help='Regex to filter message class names by',
            type="string",
            action='store'),
    )

    def handle(self, modules=None, filter_regex=None, **kwargs):
        for module_path in modules:
            try:
                module = __import__(module_path)
            except ImportError as e:
                self.stderr.write(str(e))

        re_filter = re.compile(filter_regex) if filter_regex else None

        for message in registry.all_messages.keys():
            if re_filter and not re_filter.match(message.__name__):
                continue

            self.stdout.write(SIGNATURE_TEMPLATE.format(
                message_name=message.__name__))

            for message_field in sorted(
                    message.all_fields(), key=lambda m: m.number):

                field_type = message_field.__class__.__name__

                if field_type == "MessageField":
                    attrs = "{0}, {1:d}".format(
                        message_field.message_type.__name__,
                        message_field.number)
                else:
                    attrs = "{0:d}".format(message_field.number)

                if message_field.required:
                    attrs += ", required=True"

                if message_field.repeated:
                    attrs += ", repeated=True"

                if field_type == "DateTimeField":
                    field_type = "message_types." + field_type
                else:
                    field_type = "messages." + field_type

                self.stdout.write(FIELD_ATTRIBUTE_TEMPLATE.format(
                    field_name=message_field.name,
                    field_type=field_type,
                    attrs=attrs))

            self.stdout.write("\n\n")

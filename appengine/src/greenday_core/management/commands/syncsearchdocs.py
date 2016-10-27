"""
    Management command to index search API documents
"""
import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.models.loading import get_model

from greenday_core.indexers import index_all
from greenday_core.utils import redirect_logging


class Command(BaseCommand):
    """
        Syncs indexes for all models with associated documents in
        the Search API
    """

    option_list = BaseCommand.option_list + (
        make_option(
            '--model_type', '-m', action='store', dest='model_type',
            default=None, help='The type of model to re-index', type="string"),
        make_option(
            '--object_ids', '-o', action='store', dest='object_ids',
            help='Comma-delimited list of IDs to re-index', type="string"),
    )

    def handle(self, model_type=None, object_ids=None, **kwargs):
        if object_ids:
            object_ids = map(int, object_ids.split(','))

        if model_type:
            try:
                model_type = get_model("greenday_core", model_type)
            except LookupError:
                raise CommandError(
                    '{0} is not a valid model'.format(model_type))

        self.stdout.write("Starting indexing...")

        with redirect_logging(self.stdout, log_level=logging.INFO):
            index_all(model_type, object_ids)
        self.stdout.write("Finished indexing")

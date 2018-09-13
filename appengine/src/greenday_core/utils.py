"""
    Provides utility methods used across Montage
"""
# import standard lib deps
import os
import sys
import logging
import csv
import codecs
import cStringIO
from io import BytesIO
from time import time

# import appengine deps
from google.appengine.api.app_identity import get_application_id
from google.appengine.api.modules import get_current_version_name
from google.appengine.ext import blobstore
from google.appengine.ext.appstats import datamodel_pb, recording
from google.appengine.api import images, mail

# import django deps
from django.conf import settings
from django.db import connections
from django.db.backends.utils import CursorDebugWrapper


def choices(cls):
    """
        Adds choices to an enum

        @choices
        class MyEnum(Enum):
            thing = 1
    """
    cls.choices = tuple((e.value, e.name) for e in cls)
    return cls


def get_settings_name():
    """
        Gets the correct module to define Django's settings
    """
    # application_id -> settings file
    version = get_current_version_name()
    logging.info("Using version: {0}".format(version))

    settings_module = 'greenday_core.settings.local'
    if version is not None:
        if version == 'qa':
            settings_module = 'greenday_core.settings.qa'
        else:
            settings_module = 'greenday_core.settings.live'

    logging.info("Using settings: {0}".format(settings_module))

    return settings_module


def send_email(subject, message, to):
    """
        Sends an email
    """
    logging.info(
        "Sending email with subject {subject} to {to}: {message}"
        .format(subject=subject, to=to, message=message))
    if settings.EMAIL_SENDING:
        from_addr = "montage@meedan.com".format(
            appid=settings.APP_ID)

        mail.send_mail(
            sender=from_addr,
            to=to,
            subject=subject,
            body=message)


def get_gcs_image_serving_url(filename):
    """
        Gets a serving URL from the images API for a file in GCS.

        This does not work locally
    """
    gskey = blobstore.create_gs_key("/gs/" + filename)
    return images.get_serving_url(gskey, secure_url=True)


def log_sql_queries_to_console(path):
    """
        Logs SQL queries to terminal if in debug mode.
        We need to import connection at runtime as this is
        used in the wsgi handlers for the API endpoints and
        django settings are not available at import time there.
    """
    from django.db import connection
    if settings.DEBUG and len(connection.queries) > 0:
        total_time = 0
        output = "\033[1;31m[Request Started: %s]\033[0m\n" % (path)
        for query in connection.queries:
            total_time += float(query.get('time'))
            output = output + "\033[1;31m[%s]\033[0m \033[1m%s\033[0m\n" % (
                query.get('time'), " ".join(query['sql'].split()))
        output = output + "\033[1;31m[Request Finished: %s queries in %s seconds] \
        \033[0m" % (len(connection.queries), total_time)
        print output.encode('utf-8')


def compose_new_type(new_type_name, first_base, *chained_bases):
    """
        Returns a new type with a contrived inheritance hierarchy.

        Careful here.

        new_type_name: The name of the created type
        first_base: The type that the new type should inherit from. Only
            the base types from this type will be included.
        chained_bases: Other types to include in the hierarchy.
            ** THESE TYPES WILL LOSE THEIR BASES AND THEREFORE WILL HAVE NO
            INHERITED BEHAVIOUR **
    """
    return type(
        new_type_name,
        (first_base,) + tuple(chained_bases) + first_base.__bases__,
        {},
    )


class RedirectLogging(object):
    """
        Redirects logging to a stream
    """
    def __init__(self, stream=sys.stdout, log_level=None):
        """
            Creates the context manager
        """
        self.log_level = log_level
        self.stream = stream
        self.sh = logging.StreamHandler(self.stream)
        self.logger = logging.getLogger()

    def __enter__(self):
        self.logger.addHandler(self.sh)

        if self.log_level:
            self.old_level = self.logger.getEffectiveLevel()
            self.logger.setLevel(self.log_level)

        return self

    def __exit__(self, *args):
        self.flush()
        self.logger.removeHandler(self.sh)
        self.sh.close()

        if self.log_level:
            self.logger.setLevel(self.old_level)

    def flush(self):
        """
            Flushes the stream
        """
        self.sh.flush()

redirect_logging = RedirectLogging


def CONDITIONAL_CASCADE(fn):
    """
        Custom Django ORM deletion cascade behaviour.

        Allows a function to be passed which needs to evaluate to True
        for the cascade to continue
    """
    def _inner_conditional_cascade(collector, field, sub_objs, using):
        delete_sub_objs = filter(fn, sub_objs)
        if delete_sub_objs:
            collector.collect(sub_objs, source=field.rel.to,
                              source_attr=field.name, nullable=field.null)

        if (
                field.null and
                not connections[using].features.can_defer_constraint_checks):
            collector.add_field_update(field, None, sub_objs)
    _inner_conditional_cascade.deconstruct = lambda: (
        'greenday_core.utils.CONDITIONAL_CASCADE', (fn,), {})
    return _inner_conditional_cascade


# From Python's documentation:
# https://docs.python.org/2/library/csv.html
class UnicodeWriter:  # pragma: no cover
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, encoding="utf-16", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        #self.queue.write(u'\ufeff'.encode('utf8'))
        self.writer = csv.writer(self.queue, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def read_csv_to_dict(source, encoding='utf-8', dialect=csv.excel_tab):
    """
        Reads a CSV to a list of dicts

        CSV must have header row
    """
    reader = csv.reader(
        BytesIO(source.decode(encoding).encode('utf-8')),
        dialect=dialect
    )

    # get header
    header = reader.next()
    while not header and header is not None:
        header = reader.next()

    for row in reader:
        yield dict(zip(header, row))


class AppstatsCursorDebugWrapper(CursorDebugWrapper):
    """
        Custom Django DB cursor to output SQL queries to appstats
    """
    def execute(self, sql, params=None):
        self.start_appstats_recording()
        try:
            return super(CursorDebugWrapper, self).execute(sql, params)
        finally:
            sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            self.end_appstats_recording(sql)

    def start_appstats_recording(self):
        """
            Starts appstats recorder
        """
        recorder = recording.recorder_proxy
        if recorder.has_recorder_for_current_request():
            start = time()
            self.trace = datamodel_pb.IndividualRpcStatsProto()
            delta = int(1000 * (start - recorder.start_timestamp))
            self.trace.set_start_offset_milliseconds(delta)

    def end_appstats_recording(self, sql):
        """
            Outputs SQL to an appstats trace
        """
        recorder = recording.recorder_proxy

        if recorder.has_recorder_for_current_request():
            now = time()
            delta = int(1000 * (now - recorder.start_timestamp))

            with recorder._lock:
                recorder.get_call_stack(self.trace)
                self.trace.set_service_call_name('custom.SQL')
                self.trace.set_request_data_summary(sql)

                duration = delta - self.trace.start_offset_milliseconds()
                self.trace.set_duration_milliseconds(duration)
                recorder.traces.append(self.trace)

            self.trace = None

    def executemany(self, sql, param_list):
        """
            Outputs a batch of SQL queries to an appstats trace
        """
        self.start_appstats_recording()
        try:
            return super(CursorDebugWrapper, self).executemany(sql, param_list)
        finally:
            try:
                times = len(param_list)
            except TypeError:           # param_list could be an iterator
                times = '?'

            sql = '{0} times: {1}'.format(times, sql)
            self.end_appstats_recording(sql)

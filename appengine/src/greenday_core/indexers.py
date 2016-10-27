"""
    Defines functions to sync data from the database with
    the search API
"""
import logging
from search.indexes import Index

from google.appengine.api import search as search_api
from django.contrib.auth import get_user_model
from django.db.models.loading import get_model

from .documents.project import ProjectDocument
from .documents.tag import AutoCompleteTagDocument
from .documents.user import AutoCompleteUserDocument
from .documents.video import VideoDocument

from .models import Project, GlobalTag, PendingUser, Video

from .task_helpers import auto_view


def index_project_document(project_id):
    """
        Sync a Project in the search index
    """
    index_or_delete_model(project_id, Project)


def index_global_tag_document(global_tag_id):
    """
        Sync a Tag in the search index
    """
    index_or_delete_model(global_tag_id, GlobalTag)


def delete_video_document(video_id):
    """
        Delete a Video from the search index
    """
    delete_document(video_id, 'videos')


def index_video_document(video_id):
    """
        Sync a Video in the search index
    """
    index_or_delete_model(video_id, Video, Video.non_trashed_objects)


def index_auto_complete_user(user_email):
    """
        Indexes a user by their email address. User may be one or both of
        a User or PendingUser
    """
    instance = None

    for model_type in (get_user_model(), PendingUser):
        try:
            instance = model_type.objects.get(email=user_email)
        except model_type.DoesNotExist:
            pass
        else:
            break

    if not instance:
        logging.info(
            "User {0} is not a user or a pending user. "
            "Removing from search index".format(user_email))
        delete_document(user_email, "autocomplete_users")
    else:
        document = AutoCompleteUserDocument.from_instance(instance)
        put_document(document, "autocomplete_users")


def index_or_delete_model(object_id, model_type, queryset=None):
    """
        Creates / Updates a search document for the saved
        model instance or tries to delete the index if the
        object cannot be found. Also allows you to pass in your own
        queryset to override the default should you need to make
        optimisations etc.
    """
    config = get_search_config(model_type)
    if queryset:
        assert queryset.model == model_type

    try:
        instance = (queryset or model_type.objects).get(pk=object_id)
    except model_type.DoesNotExist:
        logging.info(
            ("{0} {1} not found. Not indexing - will try to remove any "
             "existing index").format(
                model_type.__name__.title(), object_id))

        delete_document(object_id, config[1])
    else:
        document = config[0].from_instance(instance)
        put_document(document, config[1])


def get_search_config(model_type):
    """
        Gets the search document type and the index name
        for a model type
    """
    config = {
        Project: (ProjectDocument, "projects",),
        GlobalTag: (AutoCompleteTagDocument, "tags",),
        get_user_model(): (AutoCompleteUserDocument, "autocomplete_users",),
        PendingUser: (AutoCompleteUserDocument, "autocomplete_users",),
        Video: (VideoDocument, "videos")
    }
    return config[model_type]


def put_document(document, index_name):
    """
        Puts the given index document.

        Raises:
            PutError: If document failed to put.
    """
    try:
        Index(name=index_name).put(document)
    except (TypeError, ValueError) as e:
        logging.exception(e)


def delete_document(doc_id, index_name):
    """
        Tries to delete the given doc_id from the index
    """
    try:
        Index(name=index_name).delete(str(doc_id))
    except ValueError as e:
        logging.exception(e)
    except search_api.DeleteError as e:
        logging.exception(e)
        # only passing single docs here - so only a single result
        result = e.results[0]

        # if we aren't simply trying to delete a non-existant doc then raise
        if result.message != u'Not found':
            raise


@auto_view
def index_all(model_type=None, object_ids=None):
    """
        Utility method to index objects
    """
    if object_ids:
        assert model_type, "Must pass model_type if passing object_ids"

        try:
            iter(object_ids)
        except TypeError:
            object_ids = [object_ids]

    if model_type and isinstance(model_type, basestring):
        model_type = get_model("greenday_core", model_type)

    model_indexer_map = {
        Project: index_project_document,
        GlobalTag: index_global_tag_document,
        get_user_model(): index_auto_complete_user,
        PendingUser: index_auto_complete_user,
        Video: index_video_document
    }

    for django_model_type, index_fn in model_indexer_map.items():
        if model_type and django_model_type != model_type:
            continue

        document_type, index_name = get_search_config(django_model_type)

        document_ids = set()
        if django_model_type in (get_user_model(), PendingUser):
            if not object_ids:
                document_ids.update(get_all_document_ids(index_name))

            qs = django_model_type.objects.all()
            if object_ids:
                qs = django_model_type.objects.filter(pk__in=object_ids)
            # use email as ID
            document_ids.update(qs.values_list("email", flat=True))
        else:
            document_ids.update(
                map(str, object_ids or ()) or
                get_all_document_ids(index_name))

            model_ids = django_model_type.objects.all()

            if object_ids:
                model_ids = model_ids.filter(pk__in=object_ids)

            document_ids.update(map(str, model_ids.values_list("pk", flat=True)))

        indexed_count = 0
        for object_id in document_ids:
            try:
                index_fn(object_id)
                indexed_count += 1
            except Exception as e:
                logging.exception(e)

        logging.info("Re-indexed {0} {1} models".format(
            indexed_count, django_model_type.__name__))


def get_all_document_ids(index_name):
    """
        Gets all document IDs within a search index
    """
    index = search_api.Index(name=index_name)

    last_index = None
    document_ids = set()
    while True:
        doc_ids = [doc.doc_id for doc in index.get_range(
            start_id=last_index,
            ids_only=True,
            limit=1000,
            include_start_object=False).results]

        if doc_ids:
            last_index = doc_ids[-1]
            document_ids.update(doc_ids)
        else:
            break

    return document_ids

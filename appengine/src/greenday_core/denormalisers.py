"""
    Defines methods to denormalise data onto objects in Montage
"""
import logging
from django.db.models.loading import get_model
from django.db import transaction, DatabaseError

from .models import Video, Project, VideoTagInstance
from .signal_utils import inhibit_signals
from .task_helpers import auto_view


@transaction.atomic
def denormalise_video(video_id):
    """
        Denormalise data onto a video and save
    """
    video = _get_obj_silent_fail(
        Video.all_objects
        .only("pk", "recorded_date_overridden", "location_overridden")
        .with_watch_count_real()
        .with_tag_count_real()
        .with_tag_instance_count_real()
        .with_duplicate_count_real(),
        pk=video_id)

    if not video:
        return

    video.watch_count = video.watch_count_real
    video.tag_count = video.video_tag_count_real
    video.tag_instance_count = video.video_tag_instance_count_real
    video.duplicate_count = video.duplicate_count_real

    with inhibit_signals(Video):
        try:
            video.save(update_fields=[
                "watch_count",
                "tag_count",
                "tag_instance_count",
                "duplicate_count"])
        except DatabaseError:
            pass


@transaction.atomic
def denormalise_project(project_id):
    """
        Denormalise data onto a project and save
    """
    project = _get_obj_silent_fail(
        Project.all_objects, pk=project_id
    )

    if not project:
        return

    project.video_tag_instance_count = (
        VideoTagInstance.objects
        .filter(video_tag__project_id=project_id)
        .count()
    )

    with inhibit_signals(Project):
        try:
            project.save(update_fields=["video_tag_instance_count"])
        except DatabaseError:
            pass


def _get_obj_silent_fail(qs, **lookup):
    """
        Gets an object and returns None if it does not exist
    """
    try:
        return qs.get(**lookup)
    except qs.model.DoesNotExist:
        logging.info(
            "Could not find object %s from queryset %s", lookup, qs.__class__)


@auto_view
def denormalise_all(model_type=None, object_ids=None):
    """
        Utility method to denormalise objects
    """
    if object_ids:
        assert model_type, "Must pass model_type if passing object_ids"

        try:
            iter(object_ids)
        except TypeError:
            object_ids = [object_ids]


    if model_type and isinstance(model_type, basestring):
        model_type = get_model("greenday_core", model_type)

    model_denormaliser_map = {
        Video: denormalise_video,
        Project: denormalise_project
    }

    for django_model_type, denormalise_fn in model_denormaliser_map.items():
        if model_type and django_model_type != model_type:
            continue

        model_ids = django_model_type.objects.all()

        if object_ids:
            model_ids = model_ids.filter(pk__in=object_ids)

        model_ids = model_ids.values_list("pk", flat=True)

        indexed_count = 0
        for object_id in model_ids:
            try:
                denormalise_fn(object_id)
                indexed_count += 1
            except Exception as e:
                logging.exception(e)

        logging.info("Denormalised %s %s models",
            indexed_count, django_model_type.__name__)

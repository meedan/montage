"""
    Defines all of the signal handlers in Montage
"""
import datetime

# import django deps
from django.conf import settings
from django.db.models.signals import post_save, post_delete

# import lib deps
import deferred_manager

from .denormalisers import denormalise_video, denormalise_project
from .models import (
    Project,
    ProjectUser,
    Video,
    UserVideoDetail,
    VideoCollectionVideo,
    GlobalTag,
    ProjectTag,
    VideoTagInstance,
    PendingUser,
    YouTubeVideo,
    TimedVideoComment
)
from .indexers import (
    index_project_document,
    index_global_tag_document,
    index_video_document,
    index_auto_complete_user,
)
from .image_manager import ImageManager


def project_saved(sender, instance, created, raw, **kwargs):
    """
        Triggers a task to index the Project
    """
    if not raw:
        if settings.SEARCH_INDEXING:
            deferred_manager.defer(
                index_project_document, instance.pk,
                task_reference="project-{0}".format(instance.pk),
                unique_until=x_minutes(10),
                _queue='search-indexing',
                _countdown=2)

        manager = ImageManager('project')
        manager.update_linked_image_for_model(
            instance.image_url, instance.pk)


def project_deleted(sender, instance, **kwargs):
    """
        Triggers a task to delete the Project document
    """
    if settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_project_document, instance.pk,
            task_reference="project-{0}".format(instance.pk),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2)

    manager = ImageManager('project')
    manager.delete_linked_image_for_model(instance.pk)


def project_user_reprocess_project_search_document(
        sender, instance, *args, **kwargs):
    """
        Triggers re-processing of project index when ProjectUser
        instances are created, updated or deleted.
    """
    raw = kwargs.pop('raw', None)
    if not raw and settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_project_document, instance.project_id,
            task_reference="project-{0}".format(instance.project_id),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2)


def user_video_detail_saved(sender, instance, *args, **kwargs):
    """
        Triggers a task to denormalise data onto the video object
    """
    deferred_manager.defer(
        denormalise_video,
        instance.video_id,
        task_reference="video-denorm-{0}".format(instance.video_id),
        unique_until=x_minutes(2),
        _queue='denormalising',
        _countdown=2)


def user_video_detail_deleted(sender, instance, **kwargs):
    """
        Triggers a task to denormalise data onto the video object
    """
    deferred_manager.defer(
        denormalise_video,
        instance.video_id,
        task_reference="video-denorm-{0}".format(instance.video_id),
        unique_until=x_minutes(2),
        _queue='denormalising',
        _countdown=2)


def video_collection_video_reprocess_video_search_document(
        sender, instance, *args, **kwargs):
    """
        Triggers re-processing of video index when VideoCollectionVideo
        instances are created, updated or deleted.
    """
    raw = kwargs.pop('raw', None)
    if not raw and settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_video_document, instance.video_id,
            task_reference="video-{0}".format(instance.video_id),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2)


def timed_video_comment_reprocess_video_search_document(
        sender, instance, *args, **kwargs):
    """
        Triggers re-processing of video index when TimedVideoComment
        instances are created, updated or deleted.
    """
    raw = kwargs.pop('raw', None)
    if not raw and settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_video_document, instance.video_id,
            task_reference="video-{0}".format(instance.video_id),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2)


def global_tag_saved(
        sender, instance, created, raw, **kwargs):
    """
        Triggers a task to index the GlobalTag
    """
    if not raw:
        if settings.SEARCH_INDEXING:
            deferred_manager.defer(
                index_global_tag_document,
                instance.pk,
                task_reference="globaltag-{0}".format(instance.pk),
                unique_until=x_minutes(10),
                _queue='search-indexing',
                _countdown=2)

        manager = ImageManager('tag')
        manager.update_linked_image_for_model(
            instance.image_url, instance.pk)


def global_tag_deleted(sender, instance, **kwargs):
    """
        Triggers a task to delete the GlobaTag document
    """
    if settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_global_tag_document,
            instance.pk,
            task_reference="globaltag-{0}".format(instance.pk),
            _queue='search-indexing',
            _countdown=2)

    manager = ImageManager('tag')
    manager.delete_linked_image_for_model(instance.pk)


def process_project_tag_search_document(
        sender, instance, created, raw, **kwargs):
    """
        Triggers a task to index the related GlobalTag
    """
    if not raw and settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_global_tag_document,
            instance.global_tag_id,
            task_reference="globaltag-{0}".format(instance.global_tag_id),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2)


def delete_project_tag(sender, instance, **kwargs):
    """
        Triggers a task to index the related GlobalTag
    """
    if settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_global_tag_document,
            instance.global_tag_id,
            task_reference="globaltag-{0}".format(instance.global_tag_id),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2)

        if (instance.global_tag.created_from_project == instance.project
            and instance.project.tags_is_private
                ):
            instance.global_tag.delete()


def process_video_search_document(sender, instance, created, raw, **kwargs):
    """
        Triggers a task to index the Video
    """
    if not raw and settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_video_document,
            instance.pk,
            task_reference="video-{0}".format(instance.pk),
            unique_until=x_minutes(10),
            _queue='search-indexing')


def delete_video(sender, instance, **kwargs):
    """
        If the video's YouTubeVideo is no longer related to any other
        videos then delete it
    """
    if settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_video_document,
            instance.pk,
            task_reference="video-{0}".format(instance.pk),
            unique_until=x_minutes(10),
            _queue='search-indexing')

    if not instance.youtube_video.projectvideos.count():
        instance.youtube_video.delete()


def delete_youtube_video(sender, instance, **kwargs):
    """
        Delete cached thumbnails related to the YouTubeVideo
    """
    instance.delete_cached_thumbs()


def process_user_search_document(sender, instance, created, raw, **kwargs):
    """
        Triggers a task to index the user
    """
    if not raw and settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_auto_complete_user,
            instance.email,
            _queue='search-indexing',
            _countdown=2)


def delete_user_search_document(sender, instance, **kwargs):
    """
        Triggers a task to delete the User document
    """
    if settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_auto_complete_user,
            instance.email,
            _queue='search-indexing',
            _countdown=5)


def process_pending_user_search_document(
        sender, instance, created, raw, **kwargs):
    """
        Triggers a task to index the PendingUser
    """
    if not raw and settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_auto_complete_user,
            instance.email,
            _queue='search-indexing',
            _countdown=2)


def delete_pending_user_search_document(sender, instance, **kwargs):
    """
        Re-index the autocomplete object here because when a PendingUser is
        deleted there should be a User object with the same email
    """
    if settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_auto_complete_user,
            instance.email,
            _queue='search-indexing',
            _countdown=2)


def video_tag_instance_saved(sender, instance, **kwargs):
    """
        Triggers a task to index the Video related to the VideoTagInstance
    """
    if settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_video_document,
            instance.video_tag.video_id,
            task_reference="video-{0}".format(instance.video_tag.video_id),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2
        )

        global_tag_id = instance.video_tag.project_tag.global_tag_id
        deferred_manager.defer(
            index_global_tag_document,
            global_tag_id,
            task_reference="globaltag-{0}".format(global_tag_id),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2)

    deferred_manager.defer(
        denormalise_project,
        instance.video_tag.project_id,
        task_reference="project-denorm-{0}".format(
            instance.video_tag.project_id),
        unique_until=x_minutes(2),
        _queue='denormalising',
        _countdown=2
    )


    deferred_manager.defer(
        denormalise_video,
        instance.video_tag.video_id,
        task_reference="video-denorm-{0}".format(
            instance.video_tag.video_id),
        unique_until=x_minutes(2),
        _queue='denormalising',
        _countdown=2
    )


def video_tag_instance_deleted(sender, instance, **kwargs):
    """
        Triggers a task to index the Video related to the VideoTagInstance
    """
    if settings.SEARCH_INDEXING:
        deferred_manager.defer(
            index_video_document,
            instance.video_tag.video_id,
            task_reference="video-{0}".format(instance.video_tag.video_id),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2
        )

        global_tag_id = instance.video_tag.project_tag.global_tag_id
        deferred_manager.defer(
            index_global_tag_document,
            global_tag_id,
            task_reference="globaltag-{0}".format(global_tag_id),
            unique_until=x_minutes(10),
            _queue='search-indexing',
            _countdown=2)

    deferred_manager.defer(
        denormalise_project,
        instance.video_tag.project_id,
        task_reference="project-denorm-{0}".format(
            instance.video_tag.project_id),
        unique_until=x_minutes(2),
        _queue='denormalising',
        _countdown=2
    )

    deferred_manager.defer(
        denormalise_video,
        instance.video_tag.video_id,
        task_reference="video-denorm-{0}".format(
            instance.video_tag.video_id),
        unique_until=x_minutes(2),
        _queue='denormalising',
        _countdown=2
    )


def x_minutes(x):
    """
        Returns datetime object at `x` minutes from now
    """
    return datetime.datetime.utcnow() + datetime.timedelta(minutes=x)


def connect_all():
    """
        Connects all signal handlers
    """
    post_save.connect(
        project_saved, sender=Project,
        dispatch_uid='project_saved')

    post_delete.connect(
        project_deleted, sender=Project,
        dispatch_uid='project_deleted')

    post_save.connect(
        global_tag_saved, sender=GlobalTag,
        dispatch_uid='global_tag_saved')

    post_delete.connect(
        global_tag_deleted, sender=GlobalTag,
        dispatch_uid='global_tag_deleted')

    post_save.connect(
        process_project_tag_search_document, sender=ProjectTag,
        dispatch_uid='process_project_tag_search_document')

    post_delete.connect(
        delete_project_tag, sender=ProjectTag,
        dispatch_uid='delete_project_tag')

    post_save.connect(
        process_video_search_document, sender=Video,
        dispatch_uid='process_video_search_document')

    post_delete.connect(
        delete_video, sender=Video,
        dispatch_uid='delete_video')

    post_delete.connect(
        delete_youtube_video, sender=YouTubeVideo,
        dispatch_uid='delete_youtube_video')

    post_save.connect(
        user_video_detail_saved, sender=UserVideoDetail,
        dispatch_uid='user_video_detail_saved')

    post_delete.connect(
        user_video_detail_deleted, sender=UserVideoDetail,
        dispatch_uid='user_video_detail_deleted')

    post_save.connect(
        project_user_reprocess_project_search_document, sender=ProjectUser,
        dispatch_uid='project_user_reprocess_project_search_document')

    post_delete.connect(
        project_user_reprocess_project_search_document, sender=ProjectUser,
        dispatch_uid='project_user_reprocess_project_search_document')

    post_save.connect(
        process_pending_user_search_document, sender=PendingUser,
        dispatch_uid='process_pending_user_search_document')

    post_delete.connect(
        delete_pending_user_search_document, sender=PendingUser,
        dispatch_uid='delete_pending_user_search_document')

    post_save.connect(
        process_user_search_document, sender=settings.AUTH_USER_MODEL,
        dispatch_uid='process_user_search_document')

    post_delete.connect(
        delete_user_search_document, sender=settings.AUTH_USER_MODEL,
        dispatch_uid='delete_user_search_document')

    post_save.connect(
        video_tag_instance_saved, sender=VideoTagInstance,
        dispatch_uid='video_tag_instance_saved')

    post_delete.connect(
        video_tag_instance_deleted, sender=VideoTagInstance,
        dispatch_uid='video_tag_instance_deleted')

    post_save.connect(
        video_collection_video_reprocess_video_search_document,
        sender=VideoCollectionVideo,
        dispatch_uid='post_save_reprocess_video_search_document')

    post_delete.connect(
        video_collection_video_reprocess_video_search_document,
        sender=VideoCollectionVideo,
        dispatch_uid='post_delete_reprocess_video_search_document')

    post_save.connect(
        timed_video_comment_reprocess_video_search_document,
        sender=TimedVideoComment,
        dispatch_uid='post_save_reprocess_video_search_document')

    post_delete.connect(
        timed_video_comment_reprocess_video_search_document,
        sender=TimedVideoComment,
        dispatch_uid='post_delete_reprocess_video_search_document')



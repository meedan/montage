"""
    Mappers for the video API
"""
import collections
from django.db.models import Count

from greenday_core.models import (
    VideoCollection,
    Video,
    VideoTag,
    ProjectTag
)
from ..mapper import GeneralMapper
from .utils import format_date, format_duration

from .messages import (
    CollectionResponseMessage,
    VideoResponseMessage,
    VideoTagResponseMessage,
    VideoTagInstanceMessage,
    VideoTagListResponse,
    VideoResponseMessageSlim
)


class VideoMapper(GeneralMapper):
    """
        Mapper class to map any
        :class:`Video <greenday_core.models.video.Video>` entity
    """
    def __init__(self, model=Video, message_cls=VideoResponseMessage):
        """
            Creates mapper

            message_type: The response message to be returned
        """
        super(VideoMapper, self).__init__(model, message_cls)

    def get_message_field_value(self, obj, message_field_name, watched=False):
        """
            Custom mapping behaviour
        """
        if message_field_name == "watched":
            return watched

        # only return in_collections if they have been prefetched
        if (
                message_field_name in "in_collections" and
                hasattr(obj, "_prefetched_objects_cache") and
                obj._prefetched_objects_cache.get('videocollectionvideos')):
            return [
                vcv.collection_id for vcv in obj.videocollectionvideos.all()
            ]

        if message_field_name in (
                "youtube_id",
                "name",
                "channel_id",
                "channel_name",
                "playlist_id",
                "playlist_name",
                "duration",
                "notes",
                "publish_date",
                "missing_from_youtube",):
            return getattr(obj.youtube_video, message_field_name)

        if message_field_name == 'pretty_duration':
            return format_duration(
                getattr(obj.youtube_video, 'duration'))

        if message_field_name == 'pretty_publish_date':
            return format_date(getattr(obj.youtube_video, 'publish_date'))

        if message_field_name == 'pretty_created':
            return format_date(getattr(obj, 'created'))

        if (
                message_field_name in ("latitude", "longitude",) and
                not obj.location_overridden):
            return getattr(obj.youtube_video, message_field_name)

        if (
                message_field_name == "recorded_date" and
                not obj.recorded_date_overridden):
            return obj.youtube_video.recorded_date

        return super(VideoMapper, self).get_message_field_value(
            obj, message_field_name)


# video collection mapper class
class VideoCollectionMapper(GeneralMapper):
    """
        Mapper class to map any
        :class:`VideoCollection <greenday_core.models.video.VideoCollection>`
        entity
    """
    def __init__(self):
        """
            Creates mapper.
        """
        self.video_mapper = VideoMapper(message_cls=VideoResponseMessageSlim)

        super(VideoCollectionMapper, self).__init__(
            VideoCollection, CollectionResponseMessage)

    def get_video_collection_videos_qs(self, obj):
        """
            Caches the queryset response on the object
        """
        if not hasattr(obj, '_videocollectionvideos_mapper_response'):
            obj._videocollectionvideos_mapper_response = (
                obj.videocollectionvideos
                .select_related("video__youtube_video")
                .annotate(
                    tag_instance_count=Count(
                        "video__videotags__tag_instances"))
            )

        return obj._videocollectionvideos_mapper_response

    def get_message_field_value(self, obj, message_field_name):
        """
            Custom mapping behaviour
        """
        if message_field_name == 'videos':
            return (
                message_field_name,
                map(
                    self.video_mapper.map,
                    (vcv.video for vcv in
                        self.get_video_collection_videos_qs(obj))
                )
            )

        return super(VideoCollectionMapper, self).get_message_field_value(
            obj, message_field_name)


class VideoTagSearchMapper(object):
    """
        Mapper to take a list of videos and pivot them on any tags they have
        had applied to them
    """
    def map(self, video_map):
        """
            video_map: a dict of id: video obj
            Returns: VideoTagListResponse
        """
        videotags = list(
            VideoTag.objects
            .filter(video_id__in=video_map.keys())
            .prefetch_related('tag_instances'))

        # global tags to videotags
        videotag_map = collections.defaultdict(list)
        for vt in videotags:
            videotag_map[vt.project_tag_id].append(vt)

        mapped_project_tag_ids = set(videotag_map.keys())

        global_tag_map = {
            t.pk: t.global_tag for t in
            ProjectTag.objects
            .select_related("global_tag")
            .filter(pk__in=mapped_project_tag_ids)
        }

        tags = []
        for project_tag_id, global_tag in global_tag_map.items():
            instances = []
            for videotag in videotag_map.get(project_tag_id, ()):
                # get the video from the previous query
                video = video_map.get(videotag.video_id)

                for instance in videotag.tag_instances.all():
                    instances.append(VideoTagInstanceMessage(
                        start_seconds=instance.start_seconds,
                        end_seconds=instance.end_seconds,
                        user_id=instance.user_id,
                        video_id=video.pk,
                        video_name=video.youtube_video.name,
                        youtube_id=video.youtube_video.youtube_id
                    ))

            tags.append(VideoTagResponseMessage(
                global_tag_id=global_tag.pk,
                name=global_tag.name,
                description=global_tag.description,
                image_url=global_tag.image_url,
                instances=instances)
            )

        tags = sorted(tags, key=lambda t: t.name)
        return VideoTagListResponse(items=tags, is_list=True)

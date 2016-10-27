"""
    Django models for videos
"""
from operator import attrgetter

from django.conf import settings
from django.db import models

from treebeard.ns_tree import NS_Node

from ..youtube_thumbnails_cache import YTThumbnailsCache

from .base import BaseModel, TaggableMixin, TrashableMixin, ArchivableMixin
from .managers import (
    VideoManager,
    VideoNonTrashedManager,
    ArchivedVideoManager,
    VideoQuerySet
)
from .project import Project


class YouTubeVideo(BaseModel):
    """
        Encapsulates data about a YouTube video
    """
    YOUTUBE_META_FIELDS = (
        'channel_id',
        'channel_name',
        'playlist_id',
        'playlist_name',
        'latitude',
        'longitude',
        'notes',
        'publish_date',
        'recorded_date',
    )

    youtube_id = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    channel_id = models.CharField(max_length=255, null=True, blank=True)
    channel_name = models.CharField(max_length=255, null=True, blank=True)
    playlist_id = models.CharField(max_length=255, null=True, blank=True)
    playlist_name = models.CharField(max_length=255, null=True, blank=True)
    duration = models.PositiveIntegerField(default=0)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    notes = models.TextField(null=True, blank=True)
    publish_date = models.DateTimeField(null=True, blank=True)
    recorded_date = models.DateTimeField(null=True, blank=True)

    missing_from_youtube = models.BooleanField(default=False)

    def __unicode__(self):
        return u"{0} ({1})".format(self.youtube_id, self.name)

    def set_as_missing(self):
        """
            Clears the YouTube data we hold on this video and sets it as missing
        """
        self.missing_from_youtube = True
        self.name = '<Video removed>'
        self.duration = 0
        for k in self.YOUTUBE_META_FIELDS:
            setattr(self, k, None)

        self.delete_cached_thumbs()

    def delete_cached_thumbs(self):
        """
            Deletes the thumbnails we stored in GCS for this video
        """
        thumbnail_cache = YTThumbnailsCache(self.youtube_id)
        thumbnail_cache.remove_all_cached_thumbnail_images()


class Video(BaseModel, TaggableMixin, TrashableMixin, ArchivableMixin):
    """
        Video model supercedes the ``CorpusObject`` model from
        the prototype.

        This model relates a YouTubeVideo object (a canonical YT video)
        to a project
    """
    project = models.ForeignKey(Project, related_name="videos")
    youtube_video = models.ForeignKey(
        YouTubeVideo, related_name="projectvideos")
    # denormalise YT ID
    youtube_id = models.CharField(max_length=200, db_index=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="owner_of_videos",
        on_delete=models.CASCADE)

    # Fields to override YT data
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    recorded_date = models.DateTimeField(null=True, blank=True)

    # flags to indicate that YT meta has been overridden by a user
    location_overridden = models.BooleanField(default=False)
    recorded_date_overridden = models.BooleanField(default=False)

    favourited = models.BooleanField(default=False)
    precise_location = models.BooleanField(default=True)

    # denormalised
    watch_count = models.PositiveIntegerField(default=0)
    tag_count = models.PositiveIntegerField(default=0)
    tag_instance_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)

    objects = VideoManager()
    all_objects = VideoQuerySet.as_manager()
    non_trashed_objects = VideoNonTrashedManager()

    # override this manager so we don't get deleted archived videos
    archived_objects = ArchivedVideoManager()

    def __unicode__(self):
        return u"\"{0}\" on \"{1}\"".format(
            unicode(self.youtube_video),
            unicode(self.project))

    @property
    def name(self):
        """
            Video name
        """
        return self.youtube_video.name

    @property
    def youtube_url(self):
        """
            URL to watch the video on YouTube.
        """
        return 'https://www.youtube.com/watch?v={}'.format(self.youtube_id)

    @property
    def channel_url(self):
        """
            URL to videos channel on YouTube.
        """
        return 'https://www.youtube.com/channel/{}'.format(self.youtube_video.channel_id)

    def get_latitude(self):
        """
            Gets the videos location's latitude.

            Returns Montage-overridden value if it exists
        """
        if self.location_overridden:
            return self.latitude

        return self.youtube_video.latitude

    def get_longitude(self):
        """
            Gets the videos location's longitude.

            Returns Montage-overridden value if it exists
        """
        if self.location_overridden:
            return self.longitude

        return self.youtube_video.longitude

    def get_recorded_date(self):
        """
            Gets the videos recorded_date.

            Returns Montage-overridden value if it exists
        """
        if self.recorded_date_overridden:
            return self.recorded_date_overridden

        return self.youtube_video.recorded_date

    def get_duplicates(self, ids_only=False):
        """
            Gets videos which are marked as duplicates of this video
        """
        duplicate_markers = DuplicateVideoMarker.objects.filter(
            models.Q(video_1=self) | models.Q(video_2=self)
        )

        if not ids_only:
            duplicate_markers = duplicate_markers.select_related(
                "video_1__youtube_video", "video_2__youtube_video")

        dupe_videos = []
        for marker in duplicate_markers:
            if marker.video_1_id == self.pk:
                dupe_videos.append(
                    marker.video_2_id if ids_only else marker.video_2
                )
            else:
                dupe_videos.append(
                    marker.video_1_id if ids_only else marker.video_1
                )

        return dupe_videos

    def save(self, *args, **kwargs):
        """
            Override save() to wipe overridden values if they are not longer set
            as overridden
        """
        if not self.recorded_date_overridden:
            self.recorded_date = None

        if not self.location_overridden:
            self.latitude = self.longitude = None

        return super(Video, self).save(*args, **kwargs)


class DuplicateVideoMarker(BaseModel):
    """
        Marks a video as a duplicate of another

        NOTE: the ID of the source video must always be less than the
        ID of the target video. This allows us to check markers more easily.
    """
    class Meta:
        unique_together = ('video_1', 'video_2',)

    video_1 = models.ForeignKey(Video, related_name="+")
    video_2 = models.ForeignKey(Video, related_name="+")

    @classmethod
    def add_marker(cls, video_1, video_2):
        """
            Adds a duplicate marker for the given videos

            If a marker already exists this returns False
        """
        video_1, video_2 = sorted((video_1, video_2,), key=attrgetter("pk"))

        _, created = cls.objects.get_or_create(
                video_1=video_1, video_2=video_2)

        return created

    def __unicode__(self):
        return u"{0} and {1}".format(
            unicode(self.video_1),
            unicode(self.video_2))


class UserVideoDetail(BaseModel):
    """
        Describes the relationship between a user and a video
    """
    class Meta:
        unique_together = ('user', 'video',)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="related_videos",
        on_delete=models.CASCADE)
    video = models.ForeignKey(Video, related_name="related_users")

    favourite = models.BooleanField(default=False)
    watched = models.BooleanField(default=False)

    def __unicode__(self):
        return u"User {user.pk} ({user.email}) on video "\
               "{video})".format(
            user=self.user, video=unicode(self.video))


class VideoCollection(BaseModel):
    """
        A collection of videos within a project
    """
    class Meta:
        unique_together = ('project', 'name',)

    project = models.ForeignKey(Project, related_name="collections")
    videos = models.ManyToManyField(
        Video,
        through="VideoCollectionVideo",
        related_name="collections")
    name = models.CharField(max_length=200)

    @property
    def ordered_videos(self):
        """
            A property to get videos in the collection ordered by their
            position in their associated `VideoCollectionVideo` tree
        """
        return [
            vcv.video
            for vcv in self.videocollectionvideos.select_related("video")]

    def add_video(self, video):
        """
            Adds a video to the end of the collection

            Raises IntegrityError if video already exists
        """
        last_video = VideoCollectionVideo.get_last_root_node()

        if last_video:
            last_video.add_sibling(
                'last-sibling',
                collection=self,
                video=video)
        else:
            VideoCollectionVideo.add_root(
                collection=self,
                video=video
            )

    def remove_video(self, video_id):
        """
            Removes a video from the collection
        """
        VideoCollectionVideo.objects.filter(
            collection=self,
            video_id=video_id
        ).delete()

    def __unicode__(self):
        return u"\"{name}\" on \"{project}\"".format(
            name=self.name, project=unicode(self.project))


class VideoCollectionVideo(NS_Node):
    """
        Defines a relationship between a video and a collection
    """
    class Meta:
        unique_together = ('collection', 'video',)

    collection = models.ForeignKey(
        VideoCollection,
        related_name="videocollectionvideos")
    video = models.ForeignKey(
        Video,
        related_name="videocollectionvideos")

    def __unicode__(self):
        return u"{0}: {1}".format(
            unicode(self.collection),
            unicode(self.video))

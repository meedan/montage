"""
    Django models for tag functionality
"""
from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from treebeard.ns_tree import NS_Node

from ..api_exceptions import TagNameExistsException, BadRequestException

from .base import BaseModel
from .managers import ProjectTagManager
from .project import Project
from .video import Video


class GlobalTag(BaseModel):
    """
        Defines a tag which can be used across any project.
    """
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    created_from_project = models.ForeignKey(Project)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             related_name="owner_of_globaltags",
                             on_delete=models.CASCADE)

    def __unicode__(self):
        return u"ID: {0}, Name: {1}".format(self.pk, self.name)

    def save(self, *args, **kwargs):
        """
            Make sure we don't get duplicate public tags
        """
        qs = GlobalTag.objects.filter(name=self.name)

        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if self.created_from_project.tags_is_private:
            qs = qs.filter(
                created_from_project=self.created_from_project)
        else:
            qs = qs.filter(
                created_from_project__privacy_tags=Project.PUBLIC)

        tag_ids = qs.values_list('pk', flat=True)[:1]
        if tag_ids:
            raise TagNameExistsException(
                "Public tag {{{0}}} already exists with this name".format(tag_ids[0]))

        return super(GlobalTag, self).save(*args, **kwargs)


class ProjectTag(NS_Node, BaseModel):
    """
        Defines a GlobalTag which has been added to a Project.

        This model can reference itself as a parent in order to create
        a nested structure of tags within the context of the Project.
    """
    class Meta:
        unique_together = ('global_tag', 'project',)

    global_tag = models.ForeignKey(GlobalTag, related_name="projecttags")
    project = models.ForeignKey(Project, related_name="projecttags")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             related_name="owner_of_projecttags",
                             on_delete=models.CASCADE)

    objects = ProjectTagManager()

    def __unicode__(self):
        return (
            u"Global Tag ID: {0}, Tag name: {1}, Project Tag ID: {2}".format(
                self.global_tag_id, self.global_tag.name, self.pk)
        )


class VideoTag(BaseModel):
    """
        Defines a ProjectTag which has been added to a Video.

        This is not the same as a tag which has been *applied** to
        a video. In terms of UI this relationship means that this tag
        is visible on the Video timeline.

        The order field is used to define what order these tags appear in the
        video's timeline.

        Holds denormalised references to various entities to simplify queries.
    """
    class Meta:
        unique_together = ('project_tag', 'video',)

    project = models.ForeignKey(Project, related_name="videotags")
    project_tag = models.ForeignKey(ProjectTag, related_name="videotags")
    video = models.ForeignKey(Video, related_name="videotags")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             related_name="owner_of_videotags",
                             on_delete=models.CASCADE)

    def tag_video(self, start_seconds=None, end_seconds=None, user=None):
        """
            Applies the tag to the video
        """
        if start_seconds is not None or end_seconds is not None:
            assert start_seconds is not None and end_seconds is not None

        if start_seconds and end_seconds:
            if (self.tag_instances
                    .filter(end_seconds__gt=start_seconds)
                    .filter(start_seconds__lt=end_seconds)):
                raise BadRequestException(
                    "Tag intersects with an existing tag")

            if start_seconds > end_seconds:
                raise BadRequestException(
                    "Start seconds is greater than end seconds")

        return VideoTagInstance.objects.create(
            video_tag=self,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            user=user)

    def __unicode__(self):
        return (
            u"Global Tag ID: {0}, Tag name: {1}, Project Tag ID: {2}, "
            "Video Tag ID: {3}".format(
                self.project_tag.global_tag_id,
                self.project_tag.global_tag.name,
                self.project_tag.pk,
                self.pk)
        )

class TagInstance(BaseModel):
    """
        Model to define the most basic tag relationship between a tag
        and another object.

        This should be in a separate table and is designed to be inherited
        from.

        This model does not specify any information about the tag itself, it
        simply provides a generic structure within which child classes can
        apply tags.
    """
    tagged_object_type = None

    tagged_content_type = models.ForeignKey(ContentType)
    tagged_object_id = models.PositiveIntegerField()
    tagged_content_object = GenericForeignKey(
        'tagged_content_type', 'tagged_object_id')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             related_name="owner_of_tag_instances",
                             on_delete=models.CASCADE)

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls != TagInstance:
            # if this is a derived class
            assert cls.tagged_object_type

            # add .<taggableobject> and .<taggableobject>_id properties
            tagged_model_name = cls.tagged_object_type.__name__.lower()

            def obj_getter(self):
                return self.tagged_content_object

            def obj_setter(self, value):
                assert isinstance(value, self.tagged_object_type)
                self.tagged_object_id = value.pk
                self.tagged_content_object = value
            setattr(cls, tagged_model_name, property(obj_getter, obj_setter))

            def obj_id_getter(self):
                return self.tagged_object_id
            setattr(cls, tagged_model_name + "_id", property(obj_id_getter))

        return super(TagInstance, cls).__new__(cls)

    def save(self, *args, **kwargs):
        self.tagged_content_type = ContentType.objects.get_for_model(
            self.tagged_object_type)

        return super(TagInstance, self).save(*args, **kwargs)

class VideoTagInstance(TagInstance):
    """
        Represents a tag which has been applied to a Video.

        Typically these should always have a start and end time to indicate
        the span of time for which tag is relevant on the video.
    """
    tagged_object_type = Video

    video_tag = models.ForeignKey(VideoTag, related_name="tag_instances")
    start_seconds = models.FloatField(null=True)
    end_seconds = models.FloatField(null=True)

    @property
    def has_times(self):
        return self.start_seconds is not None and self.end_seconds is not None

    def validate(self):
        if (
                VideoTagInstance.objects
                .filter(video_tag=self.video_tag)
                .filter(end_seconds__gt=self.start_seconds)
                .filter(start_seconds__lt=self.end_seconds)
                .exclude(pk=self.pk)):
            raise BadRequestException(
                "Tag intersects with an existing tag")

        if self.start_seconds > self.end_seconds:
            raise BadRequestException(
                "Start seconds is greater than end seconds")

    def save(self, *args, **kwargs):
        """
            Don't set tagged_content_object directly on this model. It
            should be derived from the related VideoTag
        """
        self.tagged_content_object = self.video_tag.video
        return super(VideoTagInstance, self).save(*args, **kwargs)

    def __unicode__(self):
        s = u"Tag instance {0} on video {1}".format(
            self.pk, self.tagged_object_id)
        if self.has_times:
            s += u" from {0}s to {1}s".format(
                self.start_seconds, self.end_seconds)
        return s


class ProjectTagInstance(TagInstance):
    """
        Represents a tag applied to a Project

        *Currently not used*
    """
    tagged_object_type = Project

    project_tag = models.ForeignKey(ProjectTag)

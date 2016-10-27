"""
    Defines the classes used to build the Django admin site
"""
from django.contrib import admin

from .models import (
    User,
    PendingUser,
    Project,
    ProjectUser,
    Video,
    YouTubeVideo,
    DuplicateVideoMarker,
    UserVideoDetail,
    VideoCollection,
    VideoCollectionVideo,
    Event,
    GlobalTag,
    ProjectTag,
    VideoTag,
    VideoTagInstance,
    TimedVideoComment,
    ProjectComment
)


@admin.register(User, PendingUser)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Project, ProjectUser)
class ProjectAdmin(admin.ModelAdmin):
    pass


@admin.register(
    YouTubeVideo,
    Video,
    DuplicateVideoMarker,
    UserVideoDetail,
    VideoCollection,
    VideoCollectionVideo)
class VideoAdmin(admin.ModelAdmin):
    pass


@admin.register(GlobalTag, ProjectTag, VideoTag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(VideoTagInstance)
class TagInstanceAdmin(admin.ModelAdmin):
    pass


@admin.register(TimedVideoComment, ProjectComment)
class CommentAdmin(admin.ModelAdmin):
    pass


admin.register(Event)

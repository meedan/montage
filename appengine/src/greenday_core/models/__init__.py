"""
    Package defining all models in the Django ORM

    Connects all signal handlers on import
"""
from .user import User, PendingUser, get_sentinel_user
from .project import Project, ProjectUser
from .video import (
    YouTubeVideo,
    Video,
    DuplicateVideoMarker,
    UserVideoDetail,
    VideoCollection,
    VideoCollectionVideo
)
from .event import Event
from .tag import (
    GlobalTag,
    ProjectTag,
    VideoTag,
    VideoTagInstance,
    ProjectTagInstance
)
from .comment import Comment, TimedVideoComment, ProjectComment

from ..signals import connect_all
connect_all()

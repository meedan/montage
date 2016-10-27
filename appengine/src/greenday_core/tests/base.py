"""
    Defines generic test behaviour
"""
import mock
from milkman.dairy import milkman
# import django deps
from django.db import connection
from django.db.backends import utils
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

# import lib deps
from google.appengine.ext import testbed

from ..models import (
    GlobalTag,
    ProjectTag,
    VideoTag,
    VideoTagInstance,
    Project,
    Video,
    YouTubeVideo)


# appengine test bed with relevant stubs activated.
class AppengineTestBed(TestCase):
    """
        Test base for test suites that require appengine
        stubs to be available. This test bed also supports
        running deferred tasks immediately. This is handled
        by the defer_patcher.
    """
    def setUp(self):
        """
            Activate appengine test stubs

            Patch deferred task running to run methods immediately
        """
        super(AppengineTestBed, self).setUp()
        self.tb = testbed.Testbed()
        self.tb.activate()
        self.tb.init_search_stub()
        self.tb.init_memcache_stub()
        self.tb.init_user_stub()
        self.tb.init_urlfetch_stub()
        self.tb.init_datastore_v3_stub()
        self.tb.init_app_identity_stub()
        self.tb.init_blobstore_stub()
        self.tb.init_taskqueue_stub(root_path='appengine')
        defer_patcher.start()

    def tearDown(self):
        """
            Unpatch deferred task running

            Deactivate test stubs

            Clear Django content types cache to maintain consistent query counts
        """
        defer_patcher.stop()
        self.tb.deactivate()
        ContentType.objects.clear_cache()
        super(AppengineTestBed, self).tearDown()

    @staticmethod
    def reload(obj):
        """
            Helper method to reload an object from the DB
        """
        return obj.__class__.objects.get(pk=obj.pk)

    def assertObjectAbsent(self, obj, qs=None):
        """
            Asserts that the given object is no longer in the database
        """
        cls = obj.__class__
        qs = qs or getattr(cls, 'all_objects', cls.objects)
        self.assertFalse(
            qs.filter(pk=obj.pk).exists(),
            "{0} unexpectedly found".format(obj))

    def create_video(self, youtube_video=None, **kwargs):
        """
            Helper method to create a video
        """
        yt_field_names = [f.name for f in YouTubeVideo._meta.fields]
        video_field_names = [f.name for f in Video._meta.fields if not f.name == 'youtube_id']

        youtube_video = youtube_video or milkman.deliver(
            YouTubeVideo,
            **{k: v for k, v in kwargs.items() if k in yt_field_names})

        video = milkman.deliver(
            Video,
            youtube_video=youtube_video,
            youtube_id=youtube_video.youtube_id,
            **{k: v for k, v in kwargs.items() if k in video_field_names})

        return video

    # Uncomment the below method to bypass the assertNumQueries check
    # TODO: see if there's a nice way to run the tests with an arg to do this
    # def assertNumQueries(self, x):
    #     class Dummy():
    #         def __enter__(*args): pass
    #         def __exit__(*args): pass
    #     return Dummy()


class TestCaseTagHelpers(object):
    """
        Mixin to add tag creation methods
    """
    GLOBAL_TAG_KWARGS = (
        "name", "image_url", "description", "user", "project",)
    PROJECT_TAG_KWARGS = ("project", "global_tag", "user")
    VIDEO_TAG_KWARGS = ("project_tag", "video", "user")
    VIDEO_TAG_INSTANCE_KWARGS = ("start_seconds", "end_seconds", "user")

    def create_global_tag(self, project=None, **kwargs):
        """
            Creates a global tag
        """
        if not project:
            # GlobalTags must be created from a project - create one to
            # tie it to
            project = milkman.deliver(Project)

        return milkman.deliver(
            GlobalTag, created_from_project=project, **kwargs)

    def create_project_tag(self, global_tag=None, **kwargs):
        """
            Creates a project tag and also a global tag if not passed.

            Must pass 'project' in kwargs
            Returns global_tag, project_tag
        """
        assert "project" in kwargs

        if not global_tag:
            global_tag = self.create_global_tag(**{
                k: v for k, v in kwargs.items()
                if k in self.GLOBAL_TAG_KWARGS})

        project_tag = ProjectTag.add_root(global_tag=global_tag, **{
            k: v for k, v in kwargs.items()
            if k in self.PROJECT_TAG_KWARGS})

        return global_tag, project_tag

    def create_video_tag(self, project_tag=None, **kwargs):
        """
            Creates a video tag. Also project tag and global tags if not passed.

            Must pass 'video' kwarg

            Returns global_tag, project_tag, video_tag
        """
        assert "video" in kwargs

        if not project_tag:
            _, project_tag = self.create_project_tag(**{
                k: v for k, v in kwargs.items()
                if k in self.PROJECT_TAG_KWARGS + self.GLOBAL_TAG_KWARGS})

        video_tag = VideoTag.objects.create(
            project_tag=project_tag, project=project_tag.project, **{
                k: v for k, v in kwargs.items()
                if k in self.VIDEO_TAG_KWARGS})

        return (
            project_tag.global_tag,
            project_tag,
            video_tag,
        )

    def create_video_instance_tag(self, video_tag=None, **kwargs):
        """
            Creates an instance of a video tag

            Creates video tag, project tag and global tag if not passed

            Returns global_tag, project_tag, video_tag, video_tag_instance
        """
        if not video_tag:
            _, _, video_tag = self.create_video_tag(**{
                k: v for k, v in kwargs.items()
                if k in self.VIDEO_TAG_KWARGS +
                self.PROJECT_TAG_KWARGS +
                self.GLOBAL_TAG_KWARGS})

        instance = VideoTagInstance.objects.create(
            video_tag=video_tag, **{
                k: v for k, v in kwargs.items()
                if k in self.VIDEO_TAG_INSTANCE_KWARGS})

        return (
            video_tag.project_tag.global_tag,
            video_tag.project_tag,
            video_tag,
            instance
        )


def defer_replacement(kallable, *args, **kwargs):
    """
        Patch deferred_manager.defer to bypass and run immediately
    """
    gae_kwargs = [
        "_countdown",
        "_eta",
        "_name",
        "_target",
        "_url",
        "_transactional",
        "_headers",
        "_queue",
        "unique_until",
        "task_reference"
    ]
    for kwarg in gae_kwargs:
        kwargs.pop(kwarg, None)

    def non_logging_cursor(cursor):
        """
            Prevents any queries from being logged for the duration of
            the deferred task
        """
        return utils.CursorWrapper(cursor, connection)

    patcher = mock.patch.object(
        connection, "make_debug_cursor", new=non_logging_cursor)

    patcher.start()
    kallable(*args, **kwargs)
    try:
        patcher.stop()
    except AttributeError:
        # make_debug_cursor has already been removed
        pass

defer_patcher = mock.patch('deferred_manager.defer', new=defer_replacement)

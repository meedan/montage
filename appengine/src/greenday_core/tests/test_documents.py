"""
    Tests for :mod:`greenday_core.documents <greenday_core.documents>`
"""
# import python deps
from datetime import datetime

# import django deps
from django.contrib.auth import get_user_model
from django.utils import timezone

# import test deps
from milkman.dairy import milkman

# import project deps
from ..documents.project import ProjectDocument
from ..documents.tag import AutoCompleteTagDocument
from ..documents.user import AutoCompleteUserDocument
from ..documents.video import VideoDocument
from ..models import (
    Project,
    GlobalTag,
    ProjectTag,
    VideoTag,
    VideoTagInstance,
    PendingUser,
    VideoCollection,
    TimedVideoComment
)
from .base import AppengineTestBed, TestCaseTagHelpers


# test ProjectDocument
class ProjectDocumentTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.documents.ProjectDocument <greenday_core.documents.ProjectDocument>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(ProjectDocumentTestCase, self).setUp()
        self.user = milkman.deliver(
            get_user_model(), email="user@example.com", first_name='Robbo',
            last_name='Cop')
        self.project = milkman.deliver(
            Project,
            name="Rob's totally awesome project",
            created=timezone.now(),
            modified=timezone.now(),
            description='description 1',
            trashed_at=timezone.now())
        self.project.set_owner(self.user)

    def test_from_instance_classmethod(self):
        """
            Create a ProjectDocument from a Project object
        """
        expected_ngrams = "Rob's R Ro Rob Rob' totally t to tot tota total " \
            "totall awesome a aw awe awes aweso awesom project p pr pro " \
            "proj proje projec"
        doc = ProjectDocument.from_instance(self.project)
        self.assertEqual(doc.id, unicode(self.project.pk))
        self.assertEqual(doc.owner_id, unicode(self.project.owner.id))
        self.assertEqual(doc.owner_name, '%s %s' % (
            self.user.first_name, self.user.last_name))
        self.assertEqual(doc.name, self.project.name)
        self.assertEqual(doc.description, self.project.description)
        self.assertEqual(
            doc.created.strftime('%Y-%m-%d'), self.project.created.strftime(
                '%Y-%m-%d'))
        self.assertEqual(
            doc.modified.strftime('%Y-%m-%d'), self.project.modified.strftime(
                '%Y-%m-%d'))
        self.assertEqual(doc.n_grams, expected_ngrams)


# test AutoCompleteTagDocument
class AutoCompleteTagDocumentTestCase(TestCaseTagHelpers, AppengineTestBed):
    """
        Tests for :class:`greenday_core.documents.tag <greenday_core.documents.tag>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(AutoCompleteTagDocumentTestCase, self).setUp()
        self.user = milkman.deliver(
            get_user_model(), email="user@example.com", first_name='Robbo',
            last_name='Cop')
        self.project = milkman.deliver(Project)
        self.project_2 = milkman.deliver(Project, privacy_tags=1)
        self.project_3 = milkman.deliver(Project)

        self.tag, _ = self.create_project_tag(
            name="RobboCop",
            description='description 1',
            image_url='http://robbocop.com/foobar.jpg',
            project=self.project,
            user=self.user
        )

        self.tag_2, _ = self.create_project_tag(
            name="RobboCop Private",
            description='description 1 private',
            image_url='http://private.robbocop.com/foobar.jpg',
            project=self.project_2,
            user=self.user
        )

        self.create_project_tag(global_tag=self.tag, project=self.project_3)

    def test_from_instance_classmethod(self):
        """
            Create a AutoCompleteTagDocument from a tag object
        """
        doc = AutoCompleteTagDocument.from_instance(self.tag)
        self.assertEqual(doc.id, unicode(self.tag.pk))
        self.assertEqual(doc.name, self.tag.name)
        self.assertEqual(doc.description, self.tag.description)
        self.assertEqual(doc.private_to_project_id, None)
        self.assertEqual(
            doc.n_grams, 'RobboCop R Ro Rob Robb Robbo RobboC RobboCo')
        self.assertEqual(
            doc.project_ids, u'%s %s' % (self.project.pk, self.project_3.pk))

    def test_from_instance_classmethod_tag_privacy_changed(self):
        """
            Create a AutoCompleteTagDocument from a tag object which was
            created from a project with private tags
        """
        self.project.privacy_tags = 1
        self.project.save()
        self.tag.image_url = ''
        self.tag.save()
        doc = AutoCompleteTagDocument.from_instance(self.tag)
        self.assertEqual(doc.id, unicode(self.tag.pk))
        self.assertEqual(doc.name, self.tag.name)
        self.assertEqual(doc.description, self.tag.description)
        self.assertEqual(doc.private_to_project_id, str(self.project.pk))
        self.assertEqual(
            doc.n_grams, 'RobboCop R Ro Rob Robb Robbo RobboC RobboCo')
        self.assertEqual(
            doc.project_ids, u'%s' % (self.project.pk))

    def test_from_instance_classmethod_private_tags(self):
        """
            Create a AutoCompleteTagDocument from a tag object which was
            created from a project with private tags
        """
        doc = AutoCompleteTagDocument.from_instance(self.tag_2)
        self.assertEqual(doc.id, unicode(self.tag_2.pk))
        self.assertEqual(doc.name, self.tag_2.name)
        self.assertEqual(doc.description, self.tag_2.description)
        self.assertEqual(
            doc.private_to_project_id,
            str(self.tag_2.created_from_project_id))
        self.assertEqual(
            doc.n_grams, 'RobboCop R Ro Rob Robb Robbo RobboC RobboCo '
            'Private P Pr Pri Priv Priva Privat')
        self.assertEqual(doc.project_ids, str(self.project_2.pk))


# test VideoDocument
class VideoDocumentTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.documents.video <greenday_core.documents.video>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(VideoDocumentTestCase, self).setUp()
        self.user = milkman.deliver(
            get_user_model(), email="user@example.com", first_name='Robbo',
            last_name='Cop')

        self.project = milkman.deliver(Project, privacy_project=2)
        self.project.set_owner(self.user)
        self.video = self.create_video(
            project=self.project,
            name="Rob's totally awesome video",
            notes="Foo bar notes",
            channel_id=42,
            channel_name="bar",
            youtube_id="foobar",
            publish_date=datetime(2014, 4, 1, tzinfo=timezone.utc),
            recorded_date=datetime(2014, 4, 15, tzinfo=timezone.utc))

        self.globaltag = milkman.deliver(GlobalTag)
        self.projecttag = ProjectTag.add_root(
            global_tag=self.globaltag, project=self.project)
        self.videotag = VideoTag.objects.create(
            video=self.video,
            project_tag=self.projecttag,
            project=self.project
        )

        globaltag_2 = milkman.deliver(GlobalTag)
        projecttag_2 = ProjectTag.add_root(
            global_tag=globaltag_2, project=self.project)
        VideoTag.objects.create(
            video=self.video, project_tag=projecttag_2, project=self.project)

        VideoTagInstance.objects.create(
            video_tag=self.videotag)

        self.collection = milkman.deliver(
            VideoCollection, project=self.project)
        self.collection.add_video(self.video)
        self.collection_2 = milkman.deliver(
            VideoCollection, project=self.project)
        self.collection_2.add_video(self.video)

        self.root_comment = TimedVideoComment.add_root(
            video=self.video,
            user=self.user,
            text='foo',
            start_seconds=0
        )

        self.reply_comment = self.root_comment.add_reply(
            text='bar',
            user=self.user
        )

    def test_from_instance_classmethod(self):
        """
            Create a VideoDocument from a video object
        """
        expected_ngrams = "Rob's R Ro Rob Rob' totally t to tot tota total " \
            "totall awesome a aw awe awes aweso awesom video v vi vid vide"
        doc = VideoDocument.from_instance(self.video)
        self.assertEqual(doc.id, unicode(self.video.pk))
        self.assertEqual(doc.project_id, unicode(self.project.pk))
        self.assertEqual(doc.name, self.video.youtube_video.name)
        self.assertEqual(doc.notes, self.video.youtube_video.notes)
        self.assertEqual(
            doc.channel_id, unicode(self.video.youtube_video.channel_id))
        self.assertEqual(
            doc.youtube_id, unicode(self.video.youtube_video.youtube_id))
        self.assertEqual(
            doc.publish_date.strftime('%Y-%m-%d'),
            self.video.youtube_video.publish_date.strftime('%Y-%m-%d'))
        self.assertEqual(
            doc.recorded_date.strftime('%Y-%m-%d'),
            self.video.youtube_video.recorded_date.strftime('%Y-%m-%d'))
        self.assertEqual(doc.tag_ids, str(self.projecttag.pk))
        self.assertEqual(doc.location.latitude, 0)
        self.assertEqual(doc.location.longitude, 0)
        self.assertEqual(doc.n_grams, expected_ngrams)
        self.assertEqual(doc.collection_ids, '%s %s' % (
            self.collection.pk, self.collection_2.pk))
        self.assertEqual(doc.private_to_project_ids, None)
        self.assertEqual(
            doc.channel_name, self.video.youtube_video.channel_name)
        self.assertEqual(doc.duration, int(self.video.youtube_video.duration))
        self.assertEqual(doc.has_location, "0")
        self.assertEqual(
            doc.all_comment_text,
            "{0} {1}".format(self.root_comment.text, self.reply_comment.text)
        )

    def test_from_instance_class_method_with_location(self):
        """
            Create a VideoDocument from a video object with a location defined
        """
        expected_ngrams = "Rob's R Ro Rob Rob' totally t to tot tota total " \
            "totall awesome a aw awe awes aweso awesom video v vi vid vide"
        self.video.youtube_video.latitude = 3.14
        self.video.youtube_video.longitude = 1.2

        doc = VideoDocument.from_instance(self.video)
        self.assertEqual(doc.id, unicode(self.video.pk))
        self.assertEqual(doc.project_id, unicode(self.project.pk))
        self.assertEqual(doc.name, self.video.youtube_video.name)
        self.assertEqual(doc.notes, self.video.youtube_video.notes)
        self.assertEqual(
            doc.channel_id, unicode(self.video.youtube_video.channel_id))
        self.assertEqual(
            doc.youtube_id, unicode(self.video.youtube_video.youtube_id))
        self.assertEqual(
            doc.publish_date.strftime('%Y-%m-%d'),
            self.video.youtube_video.publish_date.strftime('%Y-%m-%d'))
        self.assertEqual(
            doc.recorded_date.strftime('%Y-%m-%d'),
            self.video.youtube_video.recorded_date.strftime('%Y-%m-%d'))
        self.assertEqual(doc.tag_ids, str(self.projecttag.pk))
        self.assertEqual(
            doc.location.latitude, self.video.youtube_video.latitude)
        self.assertEqual(
            doc.location.longitude, self.video.youtube_video.longitude)
        self.assertEqual(doc.n_grams, expected_ngrams)
        self.assertEqual(doc.collection_ids, '%s %s' % (
            self.collection_2.pk, self.collection.pk))
        self.assertEqual(doc.private_to_project_ids, None)
        self.assertEqual(
            doc.channel_name, self.video.youtube_video.channel_name)
        self.assertEqual(doc.duration, int(self.video.youtube_video.duration))
        self.assertEqual(doc.has_location, "1")

    def test_from_instance_classmethod_private(self):
        """
            Create a VideoDocument from a video object created on a private project
        """
        # checks that private project videos are marked thusly in the index
        self.project.privacy_project = 1
        self.project.save()
        expected_ngrams = "Rob's R Ro Rob Rob' totally t to tot tota total " \
            "totall awesome a aw awe awes aweso awesom video v vi vid vide"
        doc = VideoDocument.from_instance(self.video)
        self.assertEqual(doc.id, unicode(self.video.pk))
        self.assertEqual(doc.project_id, unicode(self.project.pk))
        self.assertEqual(doc.name, self.video.youtube_video.name)
        self.assertEqual(doc.notes, self.video.youtube_video.notes)
        self.assertEqual(
            doc.channel_id, unicode(self.video.youtube_video.channel_id))
        self.assertEqual(
            doc.youtube_id, unicode(self.video.youtube_video.youtube_id))
        self.assertEqual(
            doc.publish_date.strftime('%Y-%m-%d'),
            self.video.youtube_video.publish_date.strftime('%Y-%m-%d'))
        self.assertEqual(
            doc.recorded_date.strftime('%Y-%m-%d'),
            self.video.youtube_video.recorded_date.strftime('%Y-%m-%d'))
        self.assertEqual(doc.tag_ids, str(self.projecttag.pk))
        self.assertEqual(doc.n_grams, expected_ngrams)
        self.assertEqual(doc.collection_ids, '%s %s' % (
            self.collection.pk, self.collection_2.pk))
        self.assertEqual(doc.private_to_project_ids, '%s' % (self.project.pk))
        self.assertEqual(
            doc.channel_name, self.video.youtube_video.channel_name)
        self.assertEqual(doc.duration, int(self.video.youtube_video.duration))


# test AutoCompleteUserDocument
class AutoCompleteUserDocumentTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.documents.user <greenday_core.documents.user>`
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(AutoCompleteUserDocumentTestCase, self).setUp()
        self.user = milkman.deliver(
            get_user_model(), email="test@example.com",
            first_name='Test', last_name='Example')

        self.user2 = milkman.deliver(
            get_user_model(), email="test2@example.com",
            first_name='Test2', last_name='Example')

        self.puser = milkman.deliver(
            PendingUser,
            email="test@example.com")
        self.puser2 = milkman.deliver(
            PendingUser,
            email="test2@example.com")

    def test_from_instance_classmethod_user(self):
        """
            Create a AutoCompleteUserDocument from a user object
        """
        # check first user
        expected_ngrams = \
            'cha c ch co charlw robbo charlwoo rob cop charlwood robb char r ' \
            'charl ro charlwo'
        doc = AutoCompleteUserDocument.from_instance(self.user)
        self.assertEqual(doc.user_id, str(self.user.pk))
        self.assertEqual(doc.email, self.user.email)
        self.assertEqual(doc.n_grams, expected_ngrams)
        self.assertEqual(doc.full_name, self.user.get_full_name())

        # check second user
        expected_ngrams = \
            'rcha cha c ro charlw ch charlwoo rcharlwood charlwood charlwo ' \
            'rcharl rcharlw r rch char rcharlwoo rc rcharlwo rchar rob charl'
        doc = AutoCompleteUserDocument.from_instance(self.user2)
        self.assertEqual(doc.user_id, str(self.user2.pk))
        self.assertEqual(doc.email, self.user2.email)
        self.assertEqual(doc.n_grams, expected_ngrams)
        self.assertEqual(doc.full_name, self.user2.get_full_name())

    def test_from_instance_classmethod_pending_user(self):
        """
            Create a AutoCompleteUserDocument from a PendingUser object
        """
        # check first user
        expected_ngrams = \
            'cha c ch charlw charlwoo rob charlwood char r charl ro charlwo'
        doc = AutoCompleteUserDocument.from_instance(self.puser)
        self.assertEqual(doc.pending_user_id, str(self.puser.pk))
        self.assertEqual(doc.email, self.puser.email)
        self.assertEqual(doc.n_grams, expected_ngrams)

        # check second user
        expected_ngrams = \
            'rcha rcharlwood rcharl rcharlw r rch rcharlwoo rc rcharlwo rchar'
        doc = AutoCompleteUserDocument.from_instance(self.puser2)
        self.assertEqual(doc.pending_user_id, str(self.puser2.pk))
        self.assertEqual(doc.email, self.puser2.email)
        self.assertEqual(doc.n_grams, expected_ngrams)

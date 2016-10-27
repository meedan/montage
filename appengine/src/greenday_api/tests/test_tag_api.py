"""
    Tests for :mod:`greenday_api.tag.tag_api <greenday_api.tag.tag_api>`
"""
# import lib deps
from milkman.dairy import milkman
from protorpc import message_types

# import project deps
from greenday_core.api_exceptions import (
    ForbiddenException, UnauthorizedException, NotFoundException)
from greenday_core.models import GlobalTag, Project, ProjectTag, Video
from greenday_core.tests.base import TestCaseTagHelpers

from .base import ApiTestCase
from ..tag.messages import TagResponseMessage, MergeTagRequestMessage
from ..tag.tag_api import TagAPI
from ..tag.containers import TagEntityContainer, TagSearchEntityContainer


# test tag API.
class TagAPITestCase(TestCaseTagHelpers, ApiTestCase):
    """
        Test case for
        :class:`greenday_api.tag.tag_api.TagAPI <greenday_api.tag.tag_api.TagAPI>`
    """
    api_type = TagAPI

    def setUp(self):
        """
            Bootstrap data
        """
        super(TagAPITestCase, self).setUp()

        self.tag1 = milkman.deliver(GlobalTag, name='Han Solo')
        self.tag2 = milkman.deliver(
            GlobalTag, name='Chewbacca', description='Han shot first')
        self.tag3 = milkman.deliver(GlobalTag, name='Luke Skywalker')
        self.tag4 = milkman.deliver(
            GlobalTag, name='Leia', description='Kenobi helps Luke')

    def test_search_tags_unauthorised(self):
        """
            Search tags as a unauthenticated user
        """
        # unauthenticated users should be booted
        self.assertRaises(
            UnauthorizedException,
            self.api.search_tags,
            TagSearchEntityContainer.combined_message_class(
                q='Han')
        )

    # Test search tags API end point
    def test_search_tags(self):
        """
            Search public tags
        """
        # log in user
        self._sign_in(self.user)

        # logged in users are good.
        response = self.api.search_tags(
            TagSearchEntityContainer.combined_message_class(
                q='Han'))
        self.assertEqual(1, len(response.global_tags))
        self.assertEqual(self.tag1.pk, response.global_tags[0].id)

        response = self.api.search_tags(
            TagSearchEntityContainer.combined_message_class(
                q='Chewbacca'))
        self.assertEqual(1, len(response.global_tags))
        self.assertEqual(self.tag2.pk, response.global_tags[0].id)

    def test_search_tags_partial(self):
        """
            Partial search for public tags
        """
        self._sign_in(self.user)

        # logged in users are good.
        response = self.api.search_tags(
            TagSearchEntityContainer.combined_message_class(
                q='L'))
        self.assertEqual(2, len(response.global_tags))
        tag_ids = [t.id for t in response.global_tags]
        self.assertIn(self.tag3.pk, tag_ids)
        self.assertIn(self.tag4.pk, tag_ids)

    def test_empty_search(self):
        """
            Search public tags with no query term
        """
        # create some extra tags to go over the page limit
        for i in range(1, 10):
            milkman.deliver(GlobalTag, name="tag{0}".format(i))

        self._sign_in(self.user)
        response = self.api.search_tags(
            TagSearchEntityContainer.combined_message_class())

        self.assertEqual(0, len(response.project_tags))
        self.assertEqual(10, len(response.global_tags))

    def test_search_with_project_id(self):
        """
            Search tags by with project ID
        """
        self._sign_in(self.user)

        project = milkman.deliver(Project)
        ProjectTag.add_root(project=project, global_tag=self.tag1)
        ProjectTag.add_root(project=project, global_tag=self.tag2)

        response = self.api.search_tags(
            TagSearchEntityContainer.combined_message_class(
                project_id=project.pk))

        self.assertEqual(2, len(response.project_tags))
        self.assertEqual(2, len(response.global_tags))

        # check that tags matching the project_id are in the project_tag list
        # not checking the exact order because that is only accurate to
        # the nearest second in the search API
        self.assertEqual(
            {self.tag1.pk, self.tag2.pk},
            set(i.id for i in response.project_tags)
        )

        # check the other two tags are returned in the global results
        self.assertEqual(
            {self.tag3.pk, self.tag4.pk},
            set(i.id for i in response.global_tags)
        )

        # check that the project_id attribute is present on project results
        self.assertEqual(project.pk, response.project_tags[0].project_id)

        # run a more specific search
        response = self.api.search_tags(
            TagSearchEntityContainer.combined_message_class(
                project_id=project.pk, q="Han"))
        self.assertEqual(1, len(response.project_tags))
        self.assertEqual(0, len(response.global_tags))
        self.assertEqual(self.tag1.pk, response.project_tags[0].id)

    def test_search_even_spread(self):
        """
            Test that we return an even number of tags which are on the project
            and those which are not
        """
        self._sign_in(self.user)

        project = milkman.deliver(Project)

        project_tags, nonproject_tags = [], []
        for i in range(0, 10):
            tag_name = "A{0}".format(str(i))
            if i % 2 == 0:
                project_tags.append(
                    self.create_project_tag(
                        name=tag_name, project=project)[0])
            else:
                nonproject_tags.append(
                    self.create_global_tag(name=tag_name))

        response = self.api.search_tags(
            TagSearchEntityContainer.combined_message_class(
                project_id=project.pk, q='A'))

        self.assertEqual(5, len(response.project_tags))
        self.assertEqual(5, len(response.global_tags))
        self.assertFalse(
            set(i.id for i in response.project_tags) -
            set(t.pk for t in project_tags)
        )
        self.assertFalse(
            set(i.id for i in response.global_tags) -
            set(t.pk for t in nonproject_tags)
        )

    def test_search_few_global_tags(self):
        """
            Test that a full set of tags a return with fewer global tag results
        """
        self._sign_in(self.user)

        project = milkman.deliver(Project)

        project_tags, nonproject_tags = [], []
        for i in range(0, 5):
            project_tags.append(
                self.create_project_tag(
                    name="A{0}".format(str(i)), project=project)[0])

        for i in range(6, 9):
            nonproject_tags.append(
                self.create_global_tag(name="A{0}".format(str(i))))

        response = self.api.search_tags(
            TagSearchEntityContainer.combined_message_class(
                project_id=project.pk, q='A'))

        self.assertEqual(5, len(response.project_tags))
        self.assertEqual(3, len(response.global_tags))
        self.assertFalse(
            set(i.id for i in response.project_tags) -
            set(t.pk for t in project_tags)
        )
        self.assertFalse(
            set(i.id for i in response.global_tags) -
            set(t.pk for t in nonproject_tags)
        )

    def test_search_few_project_tags(self):
        """
            Test that a full set of tags a return with fewer project tag results
        """
        self._sign_in(self.user)

        project = milkman.deliver(Project)

        project_tags, nonproject_tags = [], []
        for i in range(0, 3):
            project_tags.append(
                self.create_project_tag(
                    name="A{0}".format(str(i)), project=project)[0])

        for i in range(4, 14):
            nonproject_tags.append(
                self.create_global_tag(name="A{0}".format(str(i))))

        response = self.api.search_tags(
            TagSearchEntityContainer.combined_message_class(
                project_id=project.pk, q='A'))

        self.assertEqual(3, len(response.project_tags))
        self.assertEqual(7, len(response.global_tags))
        self.assertFalse(
            set(i.id for i in response.project_tags) -
            set(t.pk for t in project_tags)
        )
        self.assertFalse(
            set(i.id for i in response.global_tags) -
            set(t.pk for t in nonproject_tags)
        )

    def test_tag_get(self):
        """
            Get a tag by ID
        """
        # unauthenticated users should be booted
        self.assertRaises(
            UnauthorizedException,
            self.api.tag_get, TagEntityContainer.combined_message_class(
                id=self.tag1.pk)
        )

        # logged in users are good.
        self._sign_in(self.admin)
        response = self.api.tag_get(
            TagEntityContainer.combined_message_class(
                id=self.tag1.pk))
        self.assertEqual(self.tag1.pk, response.id)
        self.assertEqual(self.tag1.name, response.name)
        self.assertEqual(self.tag1.description, response.description)
        self.assertEqual(self.tag1.image_url, response.image_url)
        self.assertIsInstance(response, TagResponseMessage)

    def test_404_is_raised(self):
        """
            Get a non-existant tag
        """
        self._sign_in(self.admin)
        self.assertRaises(
            NotFoundException,
            self.api.tag_get, TagEntityContainer.combined_message_class(
                id=9999)
        )

    def test_tag_list(self):
        """
            Get all tags
        """
        self.assertRaises(
            UnauthorizedException,
            self.api.tag_list,
            message_types.VoidMessage()
        )

        self._sign_in(self.admin)
        response = self.api.tag_list(message_types.VoidMessage())
        self.assertEqual(4, len(response.items))


class MergeTagAPITests(TestCaseTagHelpers, ApiTestCase):
    """
        Test case for
        :func:`greenday_api.tag.tag_api.TagAPI.tag_merge <greenday_api.tag.tag_api.TagAPI.tag_merge>`
    """
    api_type = TagAPI

    def setUp(self, *args, **kwargs):
        """
            Bootstrap data
        """
        super(MergeTagAPITests, self).setUp(*args, **kwargs)

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.user)
        self.other_project = milkman.deliver(Project)
        self.other_project.set_owner(self.user2)

        self.video = self.create_video(project=self.project)
        self.video2 = self.create_video(project=self.project)
        self.other_video = self.create_video(project=self.other_project)
        self.other_video2 = self.create_video(project=self.other_project)

        # Variable naming convention below:
        # {global tag}_{project_tag}_{video tag}_{tag_instance}

        self.tag1, self.projecttag1_1, self.videotag1_1_1, self.videotaginstance1_1_1_1 =\
            self.create_video_instance_tag(
                name="foo",
                project=self.project,
                video=self.video,
                start_seconds=20,
                end_seconds=29
            )

        self.tag2, self.projecttag2_1, self.videotag2_1_1, self.videotaginstance2_1_1_1 =\
            self.create_video_instance_tag(
                name="bar",
                project=self.project,
                video=self.video2
            )

        _, _, self.videotag2_1_2, self.videotaginstance2_1_2_1 = \
            self.create_video_instance_tag(
                project_tag=self.projecttag2_1,
                video=self.video,
                start_seconds=40,
                end_seconds=49
            )

    def test_permission_private_to_project(self):
        """
            Tags private to a project can only be merged by members of
            that project
        """
        private_project = milkman.deliver(
            Project, privacy_tags=Project.PRIVATE)
        private_project.set_owner(self.user)

        prv_tag1, prv_projecttag1_1 = self.create_project_tag(
            name=self.tag1.name,
            project=private_project
        )

        prv_tag2, prv_projecttag2_1 = self.create_project_tag(
            name=self.tag2.name,
            project=private_project
        )

        request = MergeTagRequestMessage(
            merging_from_tag_id=prv_tag2.pk,
            merging_into_tag_id=prv_tag1.pk
        )

        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException, self.api.tag_merge, request)

        self._sign_in(self.user)
        response = self.api.tag_merge(request)

    def test_permission_public(self):
        """
            Merging tags requires that both tags are assigned to one of the
            user's projects
        """
        request = MergeTagRequestMessage(
            merging_from_tag_id=self.tag2.pk,
            merging_into_tag_id=self.tag1.pk
        )

        self._sign_in(self.user2)
        self.assertRaises(
            ForbiddenException, self.api.tag_merge, request)

        self._sign_in(self.user)
        response = self.api.tag_merge(request)

    def test_permission_superuser(self):
        """
            A super user can merge any tags
        """
        self._sign_in(self.admin)

        request = MergeTagRequestMessage(
            merging_from_tag_id=self.tag2.pk,
            merging_into_tag_id=self.tag1.pk
        )

        response = self.api.tag_merge(request)

    def test_same_project(self):
        """
            Test that two tags which are applied to only one project can
            be merged
        """
        self._sign_in(self.admin)

        request = MergeTagRequestMessage(
            merging_from_tag_id=self.tag2.pk,
            merging_into_tag_id=self.tag1.pk
        )

        response = self.api.tag_merge(request)

        # tag should be removed
        self.assertObjectAbsent(self.tag2)
        self.assertObjectAbsent(self.projecttag2_1)

        # videotag pointing at old tag should point at master tag
        self.videotag2_1_1 = self.reload(self.videotag2_1_1)
        self.assertEqual(self.videotag2_1_1.project_tag, self.projecttag1_1)

        # video tagged with both tags should have redundant videotag removed
        self.assertObjectAbsent(self.videotag2_1_2)

    def test_across_projects(self):
        """
            Test that two tags which are applied to another project can be
            merged
        """
        # match above tag structure on a different project
        # prefix vars with o_ to show they're on another project
        _, o_projecttag1_1, o_videotag1_1_1, o_videotaginstance1_1_1_1 =\
            self.create_video_instance_tag(
                global_tag=self.tag1,
                project=self.other_project,
                video=self.other_video
            )

        _, o_projecttag2_1, o_videotag2_1_1, o_videotaginstance2_1_1_1 =\
            self.create_video_instance_tag(
                global_tag=self.tag2,
                project=self.other_project,
                video=self.other_video2
            )

        _, _, o_videotag2_1_2, o_videotaginstance2_1_2_1 = \
            self.create_video_instance_tag(
                project_tag=o_projecttag2_1,
                video=self.other_video
            )

        self._sign_in(self.admin)

        request = MergeTagRequestMessage(
            merging_from_tag_id=self.tag2.pk,
            merging_into_tag_id=self.tag1.pk
        )

        response = self.api.tag_merge(request)

        # tag should be removed
        self.assertObjectAbsent(o_projecttag2_1)

        # videotag pointing at old tag should point at master tag
        o_videotag2_1_1 = self.reload(o_videotag2_1_1)
        self.assertEqual(o_videotag2_1_1.project_tag, o_projecttag1_1)

        # video tagged with both tags should have redundant videotag removed
        self.assertObjectAbsent(o_videotag2_1_2)

    def test_across_projects_master_not_present(self):
        """
            Test that merging tags where another project does not have the
            master tag has the old project_tag pointed at the master tag
        """
        _, o_projecttag2_1, o_videotag2_1_1, o_videotaginstance2_1_1_1 =\
            self.create_video_instance_tag(
                global_tag=self.tag2,
                project=self.other_project,
                video=self.other_video2
            )

        self._sign_in(self.admin)

        request = MergeTagRequestMessage(
            merging_from_tag_id=self.tag2.pk,
            merging_into_tag_id=self.tag1.pk
        )

        response = self.api.tag_merge(request)

        # tag should be pointing at master tag
        o_projecttag2_1 = self.reload(o_projecttag2_1)
        self.assertEqual(self.tag1, o_projecttag2_1.global_tag)

        # videotag should still be pointing at the same project tag
        o_videotag2_1_1 = self.reload(o_videotag2_1_1)
        self.assertEqual(o_projecttag2_1, o_videotag2_1_1.project_tag)

    def test_across_projects_merge_tag_not_present(self):
        """
            Test that merging tags where another project does not have the
            merge tag takes no effect on the project
        """
        _, o_projecttag1_1, o_videotag1_1_1, o_videotaginstance1_1_1_1 =\
            self.create_video_instance_tag(
                global_tag=self.tag1,
                project=self.other_project,
                video=self.other_video
            )

        self._sign_in(self.admin)

        request = MergeTagRequestMessage(
            merging_from_tag_id=self.tag2.pk,
            merging_into_tag_id=self.tag1.pk
        )

        response = self.api.tag_merge(request)

        o_projecttag1_1 = self.reload(o_projecttag1_1)
        self.assertEqual(self.tag1, o_projecttag1_1.global_tag)

        o_videotag1_1_1 = self.reload(o_videotag1_1_1)
        self.assertEqual(o_projecttag1_1, o_videotag1_1_1.project_tag)

    def test_merge_private_project_tags_others_public(self):
        """
            Test that merging tags on a project with private tags does not
            affect public tags with the same name
        """
        self._sign_in(self.admin)

        private_project = milkman.deliver(
            Project, privacy_tags=Project.PRIVATE)

        prv_tag1, prv_projecttag1_1 = self.create_project_tag(
            name=self.tag1.name,
            project=private_project
        )

        prv_tag2, prv_projecttag2_1 = self.create_project_tag(
            name=self.tag2.name,
            project=private_project
        )

        request = MergeTagRequestMessage(
            merging_from_tag_id=prv_tag2.pk,
            merging_into_tag_id=prv_tag1.pk
        )

        response = self.api.tag_merge(request)

        # tag should be removed
        self.assertObjectAbsent(prv_tag2)
        self.assertObjectAbsent(prv_projecttag2_1)

        # other tags with same name should not be affected
        self.assertTrue(self.reload(self.tag1))
        self.assertTrue(self.reload(self.tag2))

    def test_merge_tag_instances_no_overlap(self):
        """
            Test that tag instances which do not caused any intersection
            conflicts can be merged
        """
        self._sign_in(self.admin)

        request = MergeTagRequestMessage(
            merging_from_tag_id=self.tag2.pk,
            merging_into_tag_id=self.tag1.pk
        )

        response = self.api.tag_merge(request)

        self.videotaginstance1_1_1_1 = self.reload(
            self.videotaginstance1_1_1_1)
        self.videotaginstance2_1_2_1 = self.reload(
            self.videotaginstance2_1_2_1)

        self.assertEqual(
            self.videotag1_1_1, self.videotaginstance1_1_1_1.video_tag)
        self.assertEqual(
            self.videotag1_1_1, self.videotaginstance2_1_2_1.video_tag)

    def test_merge_tag_instances_overlap(self):
        """
            Test that any tag instances which get added to a new VideoTag and
            that intersect with an existing tag instance get removed and the
            existing instance extended

            Master tags on video are 20-29s and 40-49s

            Merging tags on video are 10-24s and 25-45s
        """
        self._sign_in(self.admin)

        # this instance should extend the start_seconds of the master
        _, _, _, videotaginstance2_1_2_2 = \
            self.create_video_instance_tag(
                video_tag=self.videotag2_1_2,
                start_seconds=10,
                end_seconds=24
            )

        # this instance should extend the end_seconds of the master and
        # also cause the master (20-29s) to be merged with the other
        # master (40-49s)
        _, _, _, videotaginstance2_1_2_3 = \
            self.create_video_instance_tag(
                video_tag=self.videotag2_1_2,
                start_seconds=25,
                end_seconds=45
            )

        request = MergeTagRequestMessage(
            merging_from_tag_id=self.tag2.pk,
            merging_into_tag_id=self.tag1.pk
        )

        response = self.api.tag_merge(request)

        self.assertObjectAbsent(self.videotaginstance2_1_2_1)
        self.assertObjectAbsent(videotaginstance2_1_2_2)
        self.assertObjectAbsent(videotaginstance2_1_2_3)

        self.videotaginstance1_1_1_1 = self.reload(
            self.videotaginstance1_1_1_1)

        self.assertEqual(
            10, self.videotaginstance1_1_1_1.start_seconds)
        self.assertEqual(
            49, self.videotaginstance1_1_1_1.end_seconds)

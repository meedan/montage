"""
    Tests for :mod:`greenday_api.projecttag.projecttag_api <greenday_api.projecttag.projecttag_api>`
"""
from milkman.dairy import milkman

from greenday_core.models import (
    Project,
    GlobalTag,
    ProjectTag,
    VideoTag,
    VideoTagInstance
)
from greenday_core.tests.base import TestCaseTagHelpers
from greenday_core.api_exceptions import TagAlreadyAppliedToProject
from .base import ApiTestCase, TestEventBusMixin

from ..projecttag.projecttag_api import ProjectTagAPI
from ..projecttag.containers import (
    ProjectIDContainer,
    ProjectTagIDContainer,
    PutProjectTagContainer,
    CreateProjectTagContainer,
    MoveProjectTagContainer,
)


class ProjectTagAPITests(TestEventBusMixin, TestCaseTagHelpers, ApiTestCase):
    """
        Test case for
        :class:`greenday_api.projecttag.projecttag_api.ProjectTagAPI <greenday_api.projecttag.projecttag_api.ProjectTagAPI>`
    """
    api_type = ProjectTagAPI

    def setUp(self, *args, **kwargs):
        """
            Bootstrap test data
        """
        super(ProjectTagAPITests, self).setUp(*args, **kwargs)

        self.project = milkman.deliver(Project)
        self.project.set_owner(self.admin)
        self.video = self.create_video(project=self.project)

        self.globaltag, self.projecttag, self.videotag, _ = \
            self.create_video_instance_tag(
                name="top tag",
                description="buzz",
                image_url="img.jpg",
                project=self.project,
                video=self.video)

    def test_list_project_tags(self):
        """
            Get all tags on project
        """
        globaltag_2, projecttag_2 = self.create_project_tag(
            project=self.project, name="tag2"
        )

        globaltag_3 = milkman.deliver(GlobalTag, name="child tag")
        nested_project_tag = self.projecttag.add_child(
            global_tag=globaltag_3, project=self.project
        )

        self._sign_in(self.admin)
        request = ProjectIDContainer.combined_message_class(
            project_id=self.project.pk)
        with self.assertNumQueries(4):
            response = self.api.projecttag_list(request)

        self.assertEqual(3, len(response.items))
        self.assertEqual(self.projecttag.pk, response.items[0].id)
        self.assertEqual(nested_project_tag.pk, response.items[1].id)
        self.assertEqual(projecttag_2.pk, response.items[2].id)

        self.assertEqual(self.globaltag.pk, response.items[0].global_tag_id)
        self.assertEqual(globaltag_3.pk, response.items[1].global_tag_id)
        self.assertEqual(globaltag_2.pk, response.items[2].global_tag_id)

        first_tag_resp = response.items[0]
        self.assertEqual(self.globaltag.name, first_tag_resp.name)
        self.assertEqual(self.project.pk, first_tag_resp.project_id)
        self.assertEqual(
            self.globaltag.description, first_tag_resp.description)
        self.assertEqual(self.globaltag.image_url, first_tag_resp.image_url)
        self.assertEqual(1, first_tag_resp.video_tag_instance_count)

        nested_tag_resp = response.items[1]
        self.assertEqual(self.projecttag.pk, nested_tag_resp.parent_id)

    def test_get_project_tag(self):
        """
            Get a single tag on the project
        """
        self._sign_in(self.admin)
        request = ProjectTagIDContainer.combined_message_class(
            project_id=self.project.pk, project_tag_id=self.projecttag.pk
        )

        with self.assertNumQueries(4):
            response = self.api.projecttag_get(request)

        self.assertEqual(self.projecttag.pk, response.id)
        self.assertEqual(self.globaltag.pk, response.global_tag_id)
        self.assertEqual(self.project.pk, response.project_id)
        self.assertEqual(self.globaltag.name, response.name)
        self.assertEqual(self.globaltag.description, response.description)
        self.assertEqual(self.globaltag.image_url, response.image_url)
        self.assertEqual(1, response.videotag_count)

    def test_put_project_tag_update(self):
        """
            Update a tag on the project
        """
        self._sign_in(self.admin)
        request = PutProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            project_tag_id=self.projecttag.pk,
            name="foobar",
            description="fooz",
            image_url="http://imgr"
        )

        with self.assertNumQueries(8):
            response = self.api.projecttag_put(request)

        self.globaltag = self.reload(self.globaltag)
        self.assertEqual("foobar", self.globaltag.name)
        self.assertEqual("fooz", self.globaltag.description)
        self.assertEqual("http://imgr", self.globaltag.image_url)

    def test_patch_project_tag(self):
        """
            Patch a tag on the project
        """
        self._sign_in(self.admin)
        name = self.globaltag.name
        request = PutProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            project_tag_id=self.projecttag.pk,
            description="new description",
        )

        with self.assertNumQueries(8):
            response = self.api.projecttag_patch(request)

        self.globaltag = self.reload(self.globaltag)
        self.assertEqual(name, self.globaltag.name)
        self.assertEqual("new description", self.globaltag.description)

    def test_create_project_tag(self):
        """
            Create a new tag and assign to the project
        """
        self._sign_in(self.admin)
        request = CreateProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            name="foobar",
            description="fooz",
            image_url="http://imgr"
        )

        with self.assertNumQueries(8):
            response = self.api.projecttag_create(request)

        global_tag = GlobalTag.objects.get(
            name="foobar", created_from_project=self.project)
        project_tag = ProjectTag.objects.get(global_tag=global_tag)

        self.assertTrue(project_tag.is_root)
        self.assertEqual(self.project, project_tag.project)
        self.assertEqual("foobar", global_tag.name)
        self.assertEqual("fooz", global_tag.description)
        self.assertEqual("http://imgr", global_tag.image_url)

    def test_create_project_tag_existing_global_tag(self):
        """
            Create a tag
        """
        tag = milkman.deliver(GlobalTag, name="Bazooka")

        self._sign_in(self.admin)
        request = CreateProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            global_tag_id=tag.pk
        )

        with self.assertNumQueries(6):
            response = self.api.projecttag_create(request)

        project_tag = ProjectTag.objects.get(global_tag=tag)

        self.assertTrue(project_tag.is_root)
        self.assertEqual(self.project, project_tag.project)

    def test_create_project_tag_existing_project_tag(self):
        """
            Create tag. Same tag already exists on project.
        """
        self._sign_in(self.admin)
        request = CreateProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            name=self.globaltag.name
        )

        self.assertRaises(
            TagAlreadyAppliedToProject,
            self.api.projecttag_create,
            request)

    def test_create_tag_global_tag_duplicate_name(self):
        """
            If a public tag already exists with the given name then we should
            use that.
        """
        tag = milkman.deliver(GlobalTag, name="Bazooka")

        self._sign_in(self.admin)

        request = CreateProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            name="  " + tag.name.lower() + "    ")

        with self.assertNumQueries(6):
            response = self.api.projecttag_create(request)

        project_tag = ProjectTag.objects.get(global_tag=tag)

        self.assertTrue(project_tag.is_root)

    def test_delete_project_tag(self):
        """
            Delete a tag from the project
        """
        self._sign_in(self.admin)
        request = ProjectTagIDContainer.combined_message_class(
            project_id=self.project.pk,
            project_tag_id=self.projecttag.id
        )

        # create a tag instance to check cascade behaviour
        VideoTagInstance.objects.create(
            video_tag=self.videotag,
            user=self.admin
        )

        with self.assertNumQueries(23):
            # TODO: WAY WAY too many queries ^^
            response = self.api.projecttag_delete(request)

        self.globaltag = self.reload(self.globaltag)
        self.assertTrue(self.globaltag)
        self.assertEqual(0, self.project.projecttags.count())

        # video tag should also be deleted
        self.assertEqual(
            0,
            VideoTagInstance.objects.filter(video_tag=self.videotag).count())
        self.assertEqual(0, VideoTag.objects.filter(video=self.video).count())

    def test_move_project_tag_order(self):
        """
            Move a project tag relative to other tags
        """
        projecttag_2 = ProjectTag.add_root(
            global_tag=milkman.deliver(GlobalTag, name="foo2"),
            project=self.project)

        projecttag_3 = ProjectTag.add_root(
            global_tag=milkman.deliver(GlobalTag, name="foo3"),
            project=self.project)

        self._sign_in(self.admin)
        request = MoveProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            project_tag_id=self.projecttag.id,
            sibling_tag_id=projecttag_3.pk,
            before=True
        )

        with self.assertNumQueries(11):
            response = self.api.projecttag_move(request)

        self.assertEqual(
            [projecttag_2.pk, self.projecttag.pk, projecttag_3.pk],
            list(ProjectTag.objects.all().values_list('pk', flat=True))
        )

        request = MoveProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            project_tag_id=self.projecttag.pk,
            sibling_tag_id=projecttag_3.pk,
        )

        with self.assertNumQueries(10):
            response = self.api.projecttag_move(request)

        self.assertEqual(
            [projecttag_2.pk, projecttag_3.pk, self.projecttag.pk],
            list(ProjectTag.objects.all().values_list('pk', flat=True))
        )

    def test_move_project_tag_parent(self):
        """
            Move a tag in the hierarchy to become a child of another tag
        """
        projecttag_parent = ProjectTag.add_root(
            global_tag=milkman.deliver(GlobalTag, name="foo2"),
            project=self.project)

        self._sign_in(self.admin)
        request = MoveProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            project_tag_id=self.projecttag.id,
            parent_tag_id=projecttag_parent.pk
        )

        with self.assertNumQueries(11):
            response = self.api.projecttag_move(request)

        self.projecttag = self.reload(self.projecttag)
        projecttag_parent = self.reload(projecttag_parent)
        self.assertTrue(self.projecttag.is_child_of(projecttag_parent))

    def test_move_nested_tag_to_root(self):
        """
            Move a child tag to the root tag list on the project
        """
        tag_2 = milkman.deliver(GlobalTag, name="tag2")

        nested_project_tag = self.projecttag.add_child(
            global_tag=tag_2, project=self.project
        )

        self._sign_in(self.admin)
        request = MoveProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            project_tag_id=nested_project_tag.pk,
            sibling_tag_id=self.projecttag.pk
        )

        with self.assertNumQueries(11):
            response = self.api.projecttag_move(request)

        nested_project_tag = self.reload(nested_project_tag)

        self.assertTrue(nested_project_tag.is_root())
        self.assertFalse(nested_project_tag.is_child_of(self.projecttag))

    def test_move_nested_tag_to_root_no_sibling(self):
        """
            Passing parent_tag_id=0 should move the tag to root
        """
        tag_2 = milkman.deliver(GlobalTag, name="tag2")

        nested_project_tag = self.projecttag.add_child(
            global_tag=tag_2, project=self.project
        )

        self._sign_in(self.admin)
        request = MoveProjectTagContainer.combined_message_class(
            project_id=self.project.pk,
            project_tag_id=nested_project_tag.pk,
            parent_tag_id=0
        )

        with self.assertNumQueries(11):
            response = self.api.projecttag_move(request)

        nested_project_tag = self.reload(nested_project_tag)

        self.assertTrue(nested_project_tag.is_root())
        self.assertFalse(nested_project_tag.is_child_of(self.projecttag))

        self.assertEqual(nested_project_tag, ProjectTag.get_last_root_node())

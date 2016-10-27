from milkman.dairy import milkman

from django.db import DatabaseError

import mock

from greenday_core.denormalisers import denormalise_video, denormalise_project
from greenday_core.tests.base import AppengineTestBed
from greenday_core.models import Project, Video


class VideoDenormalisationTestCase(AppengineTestBed):
    @mock.patch('greenday_core.denormalisers._get_obj_silent_fail')
    def test_denormalise_video(self, mock_get_obj):
        project = milkman.deliver(Project)
        video = self.create_video(
            project=project,
            watch_count=5,
            tag_count=10,
            tag_instance_count=20,
            duplicate_count=3)
        self.assertEqual(video.watch_count, 5)
        self.assertEqual(video.tag_count, 10)
        self.assertEqual(video.tag_instance_count, 20)
        self.assertEqual(video.duplicate_count, 3)

        # set mock return value to that of the actual video (since this is
        # what the _get_obj_silent_fail method would return anyway). Then we
        # mock out and fake the 'real counts' that would have been returned by
        # the query so that it looks like the counts are out of date.
        video.watch_count_real = 10
        video.video_tag_count_real = 12
        video.video_tag_instance_count_real = 21
        video.duplicate_count_real = 4
        mock_get_obj.return_value = video

        # run the denormalisation
        method_resp = denormalise_video(video.pk)
        self.assertEqual(None, method_resp)

        # re-grab the object and check the values were updated.
        video = Video.objects.get(pk=video.pk)
        self.assertEqual(video.watch_count, 10)
        self.assertEqual(video.tag_count, 12)
        self.assertEqual(video.tag_instance_count, 21)
        self.assertEqual(video.duplicate_count, 4)

    @mock.patch('greenday_core.denormalisers._get_obj_silent_fail')
    def test_denormalise_video_does_not_exist(self, mock_get_obj):
        project = milkman.deliver(Project)
        video = self.create_video(
            project=project,
            watch_count=5,
            tag_count=10,
            tag_instance_count=20,
            duplicate_count=3)
        self.assertEqual(video.watch_count, 5)
        self.assertEqual(video.tag_count, 10)
        self.assertEqual(video.tag_instance_count, 20)
        self.assertEqual(video.duplicate_count, 3)

        # set mock return value to None. This replicates the case of a video
        # being deleted in between the denormalization being triggered and the
        # method being called.
        mock_get_obj.return_value = None

        # run the denormalisation - should just return quietly
        method_resp = denormalise_video(video.pk)
        self.assertEqual(None, method_resp)

    @mock.patch('greenday_core.denormalisers._get_obj_silent_fail')
    @mock.patch('greenday_core.denormalisers.Video.save')
    def test_denormalize_video_exception(self, mock_save, mock_get_obj):
        project = milkman.deliver(Project)
        video = self.create_video(
            project=project,
            watch_count=5,
            tag_count=10,
            tag_instance_count=20,
            duplicate_count=3)
        self.assertEqual(video.watch_count, 5)
        self.assertEqual(video.tag_count, 10)
        self.assertEqual(video.tag_instance_count, 20)
        self.assertEqual(video.duplicate_count, 3)

        # set mock return value to that of the actual video (since this is
        # what the _get_obj_silent_fail method would return anyway). Then we
        # mock out and fake the 'real counts' that would have been returned by
        # the query so that it looks like the counts are out of date.
        video.watch_count_real = 10
        video.video_tag_count_real = 12
        video.video_tag_instance_count_real = 21
        video.duplicate_count_real = 4
        mock_get_obj.return_value = video

        # now mock the response of the save to be an exception - this might
        # happen if the video is removed between the video being retrieved
        # and updated with new counts
        mock_save.side_effect = DatabaseError()

        # run the denormalisation and check the exception is swallowed
        method_resp = denormalise_video(video.pk)
        self.assertEqual(None, method_resp)


class ProjectDenormalisationTestCase(AppengineTestBed):
    @mock.patch('django.db.models.query.QuerySet.count')
    def test_denormalise_project(self, mock_qs_count):
        project = milkman.deliver(Project, video_tag_instance_count=0)
        mock_qs_count.return_value = 5

        # run the denormalisation
        method_resp = denormalise_project(project.pk)
        self.assertEqual(None, method_resp)

        # re-grab the object and check the values were updated.
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(project.video_tag_instance_count, 5)

    def test_denormalise_project_does_not_exist(self):
        # run the denormalisation with non-existing pk, should just return
        # quietly
        method_resp = denormalise_project(99999)
        self.assertEqual(None, method_resp)

    @mock.patch('greenday_core.denormalisers.Video.save')
    @mock.patch('django.db.models.query.QuerySet.count')
    def test_denormalize_project_exception(self, mock_qs_count, mock_save):
        project = milkman.deliver(Project, video_tag_instance_count=0)
        mock_qs_count.return_value = 5

        # now mock the response of the save to be an exception - this might
        # happen if the project is removed between the project being retrieved
        # and updated with new counts
        mock_save.side_effect = DatabaseError()

        # run the denormalisation and check the exception is swallowed
        method_resp = denormalise_project(project.pk)
        self.assertEqual(None, method_resp)

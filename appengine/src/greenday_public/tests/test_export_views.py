# -*- coding: utf-8 -*-
"""
    Tests for :mod:`greenday_public.export_views <greenday_public.export_views>`
"""
import os, datetime, csv

from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from greenday_core.tests.base import AppengineTestBed, TestCaseTagHelpers
from greenday_core.models import Project, TimedVideoComment
from greenday_core.utils import read_csv_to_dict

from milkman.dairy import milkman


def _sign_in(user):
    os.environ['USER_EMAIL'] = user.email
    os.environ['USER_IS_ADMIN'] = str(int(user.is_superuser))
    os.environ['USER_ID'] = user.username


class ExportVideoTestCase(TestCaseTagHelpers, AppengineTestBed):
    """
        Tests views to export video data
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(ExportVideoTestCase, self).setUp()

        self.admin = milkman.deliver(
            get_user_model(), email="admin@example.com", is_superuser=True,
            username='123456_gaia_id')

        self.project = milkman.deliver(Project)
        self.video = self.create_video(
            project=self.project,
            name='test video',
            notes='foobar\nbuzz',
            latitude='3.14',
            longitude='5.33')
        self.tag1, _, _, _ = self.create_video_instance_tag(
            project=self.project, video=self.video, name='غرفة عمليات انصار')

        self.comment = TimedVideoComment.add_root(
            video=self.video,
            user=self.admin,
            text='Hello world with UTF chars! غرفة عمليات انصار الشريع',
            start_seconds=0,
        )
        self.comment_reply = self.comment.add_reply('Goodbye!', self.admin)

    def test_no_vids(self):
        """
            Export videos. No video IDs passed.
        """
        _sign_in(self.admin)
        resp = self.client.post(
            reverse(
                'export:videos',
                kwargs={"project_id": self.project.pk}))
        self.assertEqual(400, resp.status_code)

    def test_unauthenticated(self):
        """
            Export videos. User not logged in
        """
        resp = self.client.post(
            reverse(
                'export:videos',
                kwargs={"project_id": self.project.pk}))
        self.assertEqual(302, resp.status_code)

    def test_unauthorised(self):
        """
            Export videos. User does not have permission on project.
        """
        unassigned_user = milkman.deliver(
            get_user_model(),
            email="unassigned_user@example.com",
            username='123456_unassigned_user')
        _sign_in(unassigned_user)

        url = reverse(
            'export:videos', kwargs={"project_id": self.project.pk})
        data = {
            'vids': self.video.pk
        }
        resp = self.client.post(url, data)
        self.assertEqual(403, resp.status_code)

    def test_csv_okay(self):
        """
            Export videos as CSV.
        """
        _sign_in(self.admin)

        url = reverse(
            'export:videos', kwargs={"project_id": self.project.pk})
        data = {
            'format': 'csv',
            'name': 'test123',
            'vids': self.video.pk
        }
        resp = self.client.post(url, data)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('attachment; filename="test123.csv"', resp['Content-Disposition'])

        vids = list(read_csv_to_dict(resp.content, encoding='utf-16'))
        self.assertEqual(1, len(vids))

        video = vids[0]
        self.assertEqual(str(self.video.pk), video['id'])
        self.assertEqual(self.video.name, video['name'])
        self.assertEqual(self.video.youtube_url, video['youtube_id'])
        self.assertEqual(
            str(self.video.get_recorded_date() or ''), video['recorded_date'])
        self.assertEqual(
            self.video.youtube_video.channel_name or '', video['channel_name'])
        self.assertEqual(self.video.channel_url, video['channel_id'])
        self.assertEqual(
            self.video.youtube_video.playlist_id or '', video['playlist_id'])
        self.assertEqual(
            self.video.youtube_video.playlist_name or '',
            video['playlist_name'])
        self.assertEqual('0', video['watch_count'])
        self.assertEqual('1', video['tag_count'])
        self.assertEqual('"%s"' % self.tag1.name, video['tags'])
        self.assertEqual(
            self.video.youtube_video.notes or '', video['notes'])
        # self.assertEqual(
            # self.video.created.strftime("%Y-%m-%d %H:%M:%S+00:00"),
            # video['created'])
        self.assertEqual(
            self.video.modified.strftime("%Y-%m-%d %H:%M:%S+00:00"),
            datetime.datetime.strptime(video['modified'], '%Y-%m-%d %H:%M:%S.%f+00:00').strftime("%Y-%m-%d %H:%M:%S+00:00"))
        self.assertEqual('', video['publish_date'])
        self.assertEqual(str(self.video.favourited), video['favourited'])
        self.assertEqual(
            str(self.video.get_longitude() or ''), video['longitude'])
        self.assertEqual(
            str(self.video.get_latitude() or ''), video['latitude'])
        self.assertEqual(
            str(self.video.youtube_video.duration), video['duration'])
        self.assertEqual(
            '"{}", "{}"'.format(self.comment.text, self.comment_reply.text),
            video['comments']
        )

    def test_kml_okay(self):
        """
            Export videos as KML.
        """
        _sign_in(self.admin)

        # video without location should be omitted
        video2 = self.create_video(
            project=self.project,
            name='test video',
            notes='foobar\nbuzz')

        url = reverse(
            'export:videos', kwargs={"project_id": self.project.pk})
        data = {
            'format': 'kml',
            'vids': '{0},{1}'.format(self.video.pk, video2.pk),
            'name': 'test123',
            'clean_name': 'Montage export test'
        }
        resp = self.client.post(url, data)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('attachment; filename="test123.kml"', resp['Content-Disposition'])

        self.assertEqual(u"""<?xml version=\'1.0\' encoding=\'utf-8\'?>
<kml:kml xmlns:kml="http://www.opengis.net/kml/2.2">\
<Document>\
<open>1</open>\
<name>Montage export test</name>\
<Placemark>\
<name>test video</name>\
<description>
<![CDATA[foobar<br/>buzz]]>
</description>\
<Point><coordinates>5.33,3.14,0</coordinates></Point>\
</Placemark>\
</Document>\
</kml:kml>""", resp.content)

class ExportProjectTagTestCase(TestCaseTagHelpers, AppengineTestBed):
    """
        Tests views to export project tag data
    """
    def setUp(self):
        """
            Bootstrap test data
        """
        super(ExportProjectTagTestCase, self).setUp()

        self.admin = milkman.deliver(
            get_user_model(), email="admin@example.com", is_superuser=True,
            username='123456_gaia_id')

        self.project = milkman.deliver(Project)
        self.video = self.create_video(project=self.project)
        self.tag1, projecttag1, _, _ = self.create_video_instance_tag(
            project=self.project, video=self.video)
        self.tag2, _, _, _ = self.create_video_instance_tag(
            project=self.project, video=self.video)

        video2 = self.create_video(project=self.project)
        self.create_video_instance_tag(project_tag=projecttag1, video=video2)

    def test_unauthenticated(self):
        """
            Export tags. User not logged in.
        """
        resp = self.client.get(
            reverse(
                'export:tags',
                kwargs={"project_id": self.project.pk}))
        self.assertEqual(302, resp.status_code)

    def test_unauthorised(self):
        """
            Export tags. User has no permission on project.
        """
        unassigned_user = milkman.deliver(
            get_user_model(),
            email="unassigned_user@example.com",
            username='123456_unassigned_user')
        _sign_in(unassigned_user)

        url = reverse(
            'export:tags', kwargs={"project_id": self.project.pk})
        resp = self.client.post(url)
        self.assertEqual(403, resp.status_code)

    def test_csv_okay(self):
        """
            Export tags as CSV.
        """
        _sign_in(self.admin)

        url = reverse(
            'export:tags', kwargs={"project_id": self.project.pk})
        resp = self.client.post(url)
        self.assertEqual(200, resp.status_code)

        tags = list(read_csv_to_dict(resp.content, encoding='utf-16', dialect=csv.excel))
        self.assertEqual(2, len(tags))

        tag1 = next(t for t in tags if long(t['id']) == self.tag1.pk)
        self.assertEqual(self.tag1.name, tag1['name'])
        self.assertEqual(str(self.tag1.description or ''), tag1['description'])
        self.assertEqual(str(self.tag1.image_url or ''), tag1['image_url'])
        self.assertEqual(
            timezone.make_naive(
                self.tag1.created, timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S+00:00"),
            datetime.datetime.strptime(tag1['created'], '%Y-%m-%d %H:%M:%S+00:00').strftime("%Y-%m-%d %H:%M:%S+00:00"))
        self.assertEqual(
            timezone.make_naive(
                self.tag1.modified, timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S+00:00"),
            datetime.datetime.strptime(tag1['modified'], '%Y-%m-%d %H:%M:%S+00:00').strftime("%Y-%m-%d %H:%M:%S+00:00"))
        self.assertEqual('2', tag1['instance_count'])
        self.assertEqual('', tag1['parent_id'])

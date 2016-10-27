import json
import logging
from collections import OrderedDict
from optparse import make_option

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from greenday_core.models import (
    Project, PendingUser, YouTubeVideo, Video, TimedVideoComment,
    ProjectComment, ProjectTag, VideoTag, VideoTagInstance, ProjectTagInstance,
    GlobalTag, Event, ProjectUser
)
from greenday_core.models.tag import TagInstance


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--project_ids', action='store', dest='project_ids',
            help='Comma separated ids', type="string"
        ),
    )

    def get_projects(self, project_ids):
        projects = Project.objects.filter(pk__in=project_ids)

        print 'Extracted %s projects out of %s ids' % (
            projects.count(), len(project_ids))

        return projects

    def get_users(self, project_ids):
        users = get_user_model().objects.filter(
            projects__in=project_ids).distinct()

        print 'Extracted %s users out of %s project ids' % (
            users.count(), len(project_ids))

        return users

    def get_pending_users(self, project_ids):
        pending_users = PendingUser.objects.filter(
            projectusers__project_id__in=project_ids).distinct()

        print 'Extracted %s pending_users out of %s project ids' % (
            pending_users.count(), len(project_ids))

        return pending_users

    def get_project_users(self, project_ids):
        project_users = ProjectUser.objects.filter(
            project_id__in=project_ids).distinct()

        print 'Extracted %s project users out of %s project ids' % (
            project_users.count(), len(project_ids))

        return project_users

    def get_youtubevideos(self, project_ids):
        youtube_videos = YouTubeVideo.objects.filter(
            projectvideos__project_id__in=project_ids).distinct()

        print 'Extracted %s youtubevideos out of %s project ids' % (
            youtube_videos.count(), len(project_ids))

        return youtube_videos

    def get_videos(self, project_ids):
        videos = Video.objects.filter(
            project_id__in=project_ids).distinct()

        print 'Extracted %s videos out of %s project ids' % (
            videos.count(), len(project_ids))

        return videos

    def get_timed_video_comments(self, project_ids):
        timed_video_comments = TimedVideoComment.objects.filter(
            project_id__in=project_ids).distinct()

        print 'Extracted %s timed video comments out of %s project ids' % (
            timed_video_comments.count(), len(project_ids))

        return timed_video_comments

    def get_project_comments(self, project_ids):
        project_comments = ProjectComment.objects.filter(
            tagged_content_type=ContentType.objects.get_for_model(Project),
            tagged_object_id__in=project_ids
        ).distinct()

        print 'Extracted %s project comments out of %s project ids' % (
            project_comments.count(), len(project_ids))

        return project_comments

    def get_project_tags(self, project_ids):
        project_tags = ProjectTag.objects.filter(
            project_id__in=project_ids).distinct()

        print 'Extracted %s project tags out of %s project ids' % (
            project_tags.count(), len(project_ids))

        return project_tags

    def get_video_tags(self, project_ids):
        video_tags = VideoTag.objects.filter(
            project_id__in=project_ids).distinct()

        print 'Extracted %s video tags out of %s project ids' % (
            video_tags.count(), len(project_ids))

        return video_tags

    def get_project_tag_instances(self, project_tags):
        project_tag_instances = ProjectTagInstance.objects.filter(
            project_tag__in=project_tags.values_list('pk', flat=True)).distinct()

        print 'Extracted %s project tag instances out of %s project tag ids' % (
            project_tag_instances.count(), project_tags.count())

        return project_tag_instances

    def get_video_tags(self, project_ids):
        video_tags = VideoTag.objects.filter(
            project_id__in=project_ids).distinct()

        print 'Extracted %s video tags out of %s project ids' % (
            video_tags.count(), len(project_ids))

        return video_tags

    def get_video_tag_instances(self, video_tags):
        video_tag_instances = VideoTagInstance.objects.filter(
            video_tag__in=video_tags.values_list('pk', flat=True)).distinct()

        print 'Extracted %s video tag instances out of %s video tag ids' % (
            video_tag_instances.count(), video_tags.count())

        return video_tag_instances

    def get_global_tags(self, project_ids):
        global_tags = GlobalTag.objects.filter(
            projecttags__project_id__in=project_ids).distinct()

        print 'Extracted %s global tags out of %s project ids' % (
            global_tags.count(), len(project_ids))

        return global_tags

    def get_events(self, project_ids):
        events = Event.objects.filter(
            project_id__in=project_ids).distinct()

        print 'Extracted %s events out of %s project ids' % (
            events.count(), len(project_ids))

        return events

    def handle(self, *args, **options):
        _project_ids = options.get('project_ids', None)

        if _project_ids is None:
            raise CommandError('You must provide some project ids.')

        project_ids = _project_ids.split(',')

        objs = OrderedDict()

        objs['projects'] = self.get_projects(project_ids)
        objs['users'] = self.get_users(project_ids)
        objs['pending_users'] = self.get_pending_users(project_ids)
        objs['project_users'] = self.get_project_users(project_ids)

        objs['youtube_videos'] = self.get_youtubevideos(project_ids)
        objs['videos'] = self.get_videos(project_ids)
        objs['project_tags'] = self.get_project_tags(project_ids)
        objs['project_tag_instances'] = self.get_project_tag_instances(objs['project_tags'])
        objs['video_tags'] = self.get_video_tags(project_ids)
        objs['video_tag_instances'] = self.get_video_tag_instances(objs['video_tags'])
        objs['timed_video_comments'] = self.get_timed_video_comments(project_ids)
        objs['project_comments'] = self.get_project_comments(project_ids)

        objs['tag_instances'] = TagInstance.objects.filter(
            Q(pk__in=objs['timed_video_comments'].values_list('pk', flat=True)) |
            Q(pk__in=objs['project_comments'].values_list('pk', flat=True)) |
            Q(pk__in=objs['project_tag_instances'].values_list('pk', flat=True)) |
            Q(pk__in=objs['video_tag_instances'].values_list('pk', flat=True))
        )
        print 'Extracted %s tag instances' % objs['tag_instances'].count()

        objs['global_tags'] = self.get_global_tags(project_ids)
        objs['events'] = self.get_events(project_ids)

        data = []
        for _objs in objs.values():
            data += json.loads(serializers.serialize(
                'json',
                _objs,
                indent=2,
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True,
            ))

        _file = open('dumped_data.json', 'w')
        _file.write(json.dumps(data))

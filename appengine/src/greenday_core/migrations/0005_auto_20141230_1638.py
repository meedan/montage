# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


def copy_video_data(apps, schema_editor):
    Video = apps.get_model("greenday_core", "Video")
    YouTubeVideo = apps.get_model("greenday_core", "YouTubeVideo")

    for project_video in Video.objects.all():
        yt_video, _ = YouTubeVideo.objects.get_or_create(
            youtube_id=project_video.youtube_id,
            defaults={
                "name": project_video.name,
                "channel_id": project_video.channel_id,
                "channel_name": project_video.channel_name,
                "playlist_id": project_video.playlist_id,
                "playlist_name": project_video.playlist_name,
                "duration": project_video.duration,
                "latitude": project_video.latitude,
                "longitude": project_video.longitude,
                "notes": project_video.notes,
                "publish_date": project_video.publish_date,
                "recorded_date": project_video.recorded_date
            }
        )

        if not project_video.location_overridden:
            project_video.latitude = project_video.longitude = None

        if not project_video.recorded_date_overridden:
            project_video.recorded_date = None

        project_video.youtube_video = yt_video
        project_video.save()


def reverse_copy_video_data(apps, schema_editor):
    Video = apps.get_model("greenday_core", "Video")
    YouTubeVideo = apps.get_model("greenday_core", "YouTubeVideo")

    for project_video in Video.objects.all():
        try:
            yt_video = project_video.youtube_video
        except YouTubeVideo.DoesNotExist:
            continue
        else:
            project_video.youtube_id = yt_video.youtube_id
            project_video.name = yt_video.name
            project_video.channel_id = yt_video.channel_id
            project_video.channel_name = yt_video.channel_name
            project_video.playlist_id = yt_video.playlist_id
            project_video.playlist_name = yt_video.playlist_name
            project_video.duration = yt_video.duration
            project_video.notes = yt_video.notes
            project_video.publish_date = yt_video.publish_date

            if not project_video.location_overridden:
                project_video.latitude = yt_video.latitude
                project_video.longitude = yt_video.longitude

            if not project_video.recorded_date_overridden:
                project_video.recorded_date = yt_video.recorded_date

        project_video.save()


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0004_auto_20141223_1204'),
    ]

    operations = [
        migrations.CreateModel(
            name='YouTubeVideo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('youtube_id', models.CharField(unique=True, max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('channel_id', models.CharField(max_length=255, null=True, blank=True)),
                ('channel_name', models.CharField(max_length=255, null=True, blank=True)),
                ('playlist_id', models.CharField(max_length=255, null=True, blank=True)),
                ('playlist_name', models.CharField(max_length=255, null=True, blank=True)),
                ('duration', models.PositiveIntegerField(default=0)),
                ('latitude', models.FloatField(null=True, blank=True)),
                ('longitude', models.FloatField(null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('publish_date', models.DateTimeField(null=True, blank=True)),
                ('recorded_date', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='video',
            name='youtube_video',
            field=models.ForeignKey(related_name=b'projectvideos', default=99999, to='greenday_core.YouTubeVideo'),
            preserve_default=False,
        ),
        migrations.RunPython(
            copy_video_data,
            reverse_copy_video_data
        ),
        migrations.RemoveField(
            model_name='video',
            name='channel_id',
        ),
        migrations.RemoveField(
            model_name='video',
            name='channel_name',
        ),
        migrations.RemoveField(
            model_name='video',
            name='duration',
        ),
        migrations.RemoveField(
            model_name='video',
            name='name',
        ),
        migrations.RemoveField(
            model_name='video',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='video',
            name='playlist_id',
        ),
        migrations.RemoveField(
            model_name='video',
            name='playlist_name',
        ),
        migrations.RemoveField(
            model_name='video',
            name='youtube_id',
        ),
    ]

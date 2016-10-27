# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone
import greenday_core.models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, max_length=30, verbose_name='username', validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username.', 'invalid')])),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(max_length=75, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('accepted_nda', models.BooleanField(default=False)),
                ('gaia_id', models.CharField(max_length=200, null=True, verbose_name='GAIA id', blank=True)),
                ('is_googler', models.BooleanField(default=False, verbose_name='Is Googler?')),
                ('profile_img_url', models.URLField(max_length=300, null=True, verbose_name='Profile image', blank=True)),
                ('google_plus_profile', models.URLField(max_length=300, null=True, verbose_name='Google+ profile', blank=True)),
                ('language', models.CharField(default=b'en', max_length=200, null=True, verbose_name='User Language', blank=True)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(db_index=True)),
                ('kind', models.IntegerField(verbose_name=((0, b'PROJECTCREATED'), (1, b'PROJECTUPDATED'), (2, b'PROJECTDELETED'), (50, b'PROJECTRESTORED'), (100, b'VIDEOCREATED'), (101, b'VIDEOUPDATED'), (102, b'VIDEODELETED'), (150, b'VIDEOHIGHLIGHTED'), (151, b'VIDEOUNHIGHLIGHTED'), (200, b'USERCREATED'), (201, b'USERUPDATED'), (202, b'USERDELETED'), (250, b'USERACCEPTEDNDA'), (251, b'USERINVITEDASPROJECTUSER'), (252, b'USERINVITEDASPROJECTADMIN'), (253, b'USERACCEPTEDPROJECTINVITE'), (254, b'USERREJECTEDPROJECTINVITE'), (255, b'USERREMOVED'), (300, b'VIDEOCOLLECTIONCREATED'), (301, b'VIDEOCOLLECTIONUPDATED'), (302, b'VIDEOCOLLECTIONDELETED'), (350, b'VIDEOADDEDTOCOLLECTION'), (351, b'VIDEOREMOVEDFROMCOLLECTION'), (450, b'PENDINGUSERINVITEDASPROJECTADMIN'), (451, b'PENDINGUSERINVITEDASPROJECTUSER')), db_index=True)),
                ('object_kind', models.IntegerField(db_index=True)),
                ('event_kind', models.IntegerField(db_index=True)),
                ('object_id', models.IntegerField(null=True, db_index=True)),
                ('project_id', models.IntegerField(null=True, db_index=True)),
                ('meta', models.TextField(null=True, blank=True)),
                ('user', models.ForeignKey(related_name=b'actions', on_delete=models.SET(greenday_core.models.user.get_sentinel_user), blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-timestamp', '-pk'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GlobalTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('image_url', models.URLField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PendingUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('email', models.EmailField(unique=True, max_length=75, blank=True)),
                ('user', models.OneToOneField(related_name=b'pending_user', null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('trashed_at', models.DateTimeField(verbose_name='Trashed', null=True, editable=False, blank=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(null=True, blank=True)),
                ('image_gcs_filename', models.CharField(max_length=500, null=True, blank=True)),
                ('image_url', models.TextField(null=True, blank=True)),
                ('privacy_project', models.IntegerField(default=1, verbose_name='Project privacy', choices=[(1, 'Private'), (2, 'Public')])),
                ('privacy_tags', models.IntegerField(default=2, verbose_name='Tag privacy', choices=[(1, 'Private'), (2, 'Public')])),
            ],
            options={
                'ordering': ['-created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProjectTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lft', models.PositiveIntegerField(db_index=True)),
                ('rgt', models.PositiveIntegerField(db_index=True)),
                ('tree_id', models.PositiveIntegerField(db_index=True)),
                ('depth', models.PositiveIntegerField(db_index=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('global_tag', models.ForeignKey(related_name=b'projecttags', to='greenday_core.GlobalTag')),
                ('project', models.ForeignKey(related_name=b'projecttags', to='greenday_core.Project')),
                ('user', models.ForeignKey(related_name=b'owner_of_projecttags', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProjectUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_pending', models.BooleanField(default=False)),
                ('is_assigned', models.BooleanField(default=False)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_owner', models.BooleanField(default=False)),
                ('last_updates_viewed', models.DateTimeField(default=django.utils.timezone.now)),
                ('pending_user', models.ForeignKey(related_name=b'projectusers', on_delete=django.db.models.deletion.SET_NULL, to='greenday_core.PendingUser', null=True)),
                ('project', models.ForeignKey(related_name=b'projectusers', to='greenday_core.Project')),
                ('user', models.ForeignKey(related_name=b'projectusers', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TagInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('tagged_object_id', models.PositiveIntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProjectTagInstance',
            fields=[
                ('taginstance_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='greenday_core.TagInstance')),
                ('project_tag', models.ForeignKey(to='greenday_core.ProjectTag')),
            ],
            options={
                'abstract': False,
            },
            bases=('greenday_core.taginstance',),
        ),
        migrations.CreateModel(
            name='TimedVideoComment',
            fields=[
                ('taginstance_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='greenday_core.TagInstance')),
                ('lft', models.PositiveIntegerField(db_index=True)),
                ('rgt', models.PositiveIntegerField(db_index=True)),
                ('tree_id', models.PositiveIntegerField(db_index=True)),
                ('depth', models.PositiveIntegerField(db_index=True)),
                ('start_seconds', models.FloatField()),
                ('text', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('greenday_core.taginstance', models.Model),
        ),
        migrations.CreateModel(
            name='UserVideoDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('favourite', models.BooleanField(default=False)),
                ('watched', models.BooleanField(default=False)),
                ('user', models.ForeignKey(related_name=b'related_videos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('trashed_at', models.DateTimeField(verbose_name='Trashed', null=True, editable=False, blank=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('archived_at', models.DateTimeField(null=True)),
                ('name', models.CharField(max_length=200)),
                ('youtube_id', models.CharField(max_length=200)),
                ('latitude', models.FloatField(null=True, blank=True)),
                ('longitude', models.FloatField(null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('publish_date', models.DateTimeField(null=True, blank=True)),
                ('recorded_date', models.DateTimeField(null=True, blank=True)),
                ('channel_id', models.CharField(max_length=255, null=True, blank=True)),
                ('channel_name', models.CharField(max_length=255, null=True, blank=True)),
                ('playlist_id', models.CharField(max_length=255, null=True, blank=True)),
                ('playlist_name', models.CharField(max_length=255, null=True, blank=True)),
                ('duration', models.PositiveIntegerField(default=0)),
                ('favourited', models.BooleanField(default=False)),
                ('location_overridden', models.BooleanField(default=False)),
                ('recorded_date_overridden', models.BooleanField(default=False)),
                ('duplicate_of', models.ForeignKey(related_name=b'duplicates', blank=True, to='greenday_core.Video', null=True)),
                ('project', models.ForeignKey(related_name=b'videos', to='greenday_core.Project')),
                ('user', models.ForeignKey(related_name=b'owner_of_videos', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VideoCollection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=200)),
                ('project', models.ForeignKey(related_name=b'collections', to='greenday_core.Project')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VideoCollectionVideo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lft', models.PositiveIntegerField(db_index=True)),
                ('rgt', models.PositiveIntegerField(db_index=True)),
                ('tree_id', models.PositiveIntegerField(db_index=True)),
                ('depth', models.PositiveIntegerField(db_index=True)),
                ('collection', models.ForeignKey(related_name=b'videocollectionvideos', to='greenday_core.VideoCollection')),
                ('video', models.ForeignKey(related_name=b'videocollectionvideos', to='greenday_core.Video')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VideoTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('project', models.ForeignKey(related_name=b'videotags', to='greenday_core.Project')),
                ('project_tag', models.ForeignKey(related_name=b'videotags', to='greenday_core.ProjectTag')),
                ('user', models.ForeignKey(related_name=b'owner_of_videotags', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('video', models.ForeignKey(related_name=b'videotags', to='greenday_core.Video')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VideoTagInstance',
            fields=[
                ('taginstance_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='greenday_core.TagInstance')),
                ('start_seconds', models.FloatField(null=True)),
                ('end_seconds', models.FloatField(null=True)),
                ('video_tag', models.ForeignKey(related_name=b'tag_instances', to='greenday_core.VideoTag')),
            ],
            options={
                'abstract': False,
            },
            bases=('greenday_core.taginstance',),
        ),
        migrations.AlterUniqueTogether(
            name='videotag',
            unique_together=set([('project_tag', 'video')]),
        ),
        migrations.AlterUniqueTogether(
            name='videocollectionvideo',
            unique_together=set([('collection', 'video')]),
        ),
        migrations.AddField(
            model_name='videocollection',
            name='videos',
            field=models.ManyToManyField(related_name=b'collections', through='greenday_core.VideoCollectionVideo', to='greenday_core.Video'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='videocollection',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AddField(
            model_name='uservideodetail',
            name='video',
            field=models.ForeignKey(related_name=b'related_users', to='greenday_core.Video'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='uservideodetail',
            unique_together=set([('user', 'video')]),
        ),
        migrations.AddField(
            model_name='taginstance',
            name='tagged_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taginstance',
            name='user',
            field=models.ForeignKey(related_name=b'owner_of_tag_instances', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='projectuser',
            unique_together=set([('project', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='projecttag',
            unique_together=set([('global_tag', 'project')]),
        ),
        migrations.AddField(
            model_name='project',
            name='users',
            field=models.ManyToManyField(related_name=b'projects', through='greenday_core.ProjectUser', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='globaltag',
            name='created_from_project',
            field=models.ForeignKey(to='greenday_core.Project'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='globaltag',
            name='user',
            field=models.ForeignKey(related_name=b'owner_of_globaltags', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]

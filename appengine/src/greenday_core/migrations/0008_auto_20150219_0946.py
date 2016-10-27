# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import greenday_core.utils
import greenday_core.models


def normalize_duplicate_markers(apps, schema_editor):
    DuplicateVideoMarker = apps.get_model("greenday_core", "DuplicateVideoMarker")

    for marker in DuplicateVideoMarker.objects.all():
        if marker.video_1_id > marker.video_2_id:
            marker.video_1_id, marker.video_2_id = marker.video_2_id, marker.video_1_id
            marker.save()


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0007_auto_20150127_1044'),
    ]

    operations = [
        migrations.RenameField(
            model_name='duplicatevideomarker',
            old_name='source_video',
            new_name='video_1',
        ),
        migrations.RenameField(
            model_name='duplicatevideomarker',
            old_name='target_video',
            new_name='video_2',
        ),
        migrations.AlterField(
            model_name='event',
            name='kind',
            field=models.IntegerField(verbose_name=((0, b'PROJECTCREATED'), (1, b'PROJECTUPDATED'), (2, b'PROJECTDELETED'), (50, b'PROJECTRESTORED'), (100, b'VIDEOCREATED'), (101, b'VIDEOUPDATED'), (102, b'VIDEODELETED'), (150, b'VIDEOHIGHLIGHTED'), (151, b'VIDEOUNHIGHLIGHTED'), (200, b'USERCREATED'), (201, b'USERUPDATED'), (202, b'USERDELETED'), (250, b'USERACCEPTEDNDA'), (251, b'USERINVITEDASPROJECTUSER'), (252, b'PENDINGUSERREMOVED'), (253, b'USERACCEPTEDPROJECTINVITE'), (254, b'USERREJECTEDPROJECTINVITE'), (255, b'USERREMOVED'), (256, b'PROJECTCOLLABORATORONLINE'), (257, b'PROJECTCOLLABORATOROFFLINE'), (300, b'VIDEOCOLLECTIONCREATED'), (301, b'VIDEOCOLLECTIONUPDATED'), (302, b'VIDEOCOLLECTIONDELETED'), (350, b'VIDEOADDEDTOCOLLECTION'), (351, b'VIDEOREMOVEDFROMCOLLECTION'), (450, b'PENDINGUSERINVITEDASPROJECTADMIN'), (451, b'PENDINGUSERINVITEDASPROJECTUSER'), (500, b'PROJECTROOTCOMMENTCREATED'), (501, b'PROJECTCOMMENTUPDATED'), (502, b'PROJECTCOMMENTDELETED'), (550, b'PROJECTREPLYCOMMENTCREATED'), (600, b'TIMEDVIDEOROOTCOMMENTCREATED'), (601, b'TIMEDVIDEOCOMMENTUPDATED'), (602, b'TIMEDVIDEOCOMMENTDELETED'), (650, b'TIMEDVIDEOREPLYCOMMENTCREATED')), db_index=True),
        ),
        migrations.AlterField(
            model_name='projectuser',
            name='pending_user',
            field=models.ForeignKey(related_name=b'projectusers', on_delete=greenday_core.utils.CONDITIONAL_CASCADE(greenday_core.models.project.project_user_has_user_id), blank=True, to='greenday_core.PendingUser', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='duplicatevideomarker',
            unique_together=set([('video_1', 'video_2')]),
        ),
        migrations.RunPython(
            normalize_duplicate_markers,
            lambda *a: None  # noop
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0014_auto_20150422_0900'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='duplicate_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='kind',
            field=models.IntegerField(verbose_name=((0, b'PROJECTCREATED'), (1, b'PROJECTUPDATED'), (2, b'PROJECTDELETED'), (50, b'PROJECTRESTORED'), (100, b'VIDEOCREATED'), (101, b'VIDEOUPDATED'), (102, b'VIDEODELETED'), (150, b'VIDEOHIGHLIGHTED'), (151, b'VIDEOUNHIGHLIGHTED'), (152, b'VIDEOARCHIVED'), (153, b'VIDEOUNARCHIVED'), (200, b'USERCREATED'), (201, b'USERUPDATED'), (202, b'USERDELETED'), (250, b'USERACCEPTEDNDA'), (251, b'USERINVITEDASPROJECTUSER'), (252, b'PENDINGUSERREMOVED'), (253, b'USERACCEPTEDPROJECTINVITE'), (254, b'USERREJECTEDPROJECTINVITE'), (255, b'USERREMOVED'), (256, b'PROJECTCOLLABORATORONLINE'), (257, b'PROJECTCOLLABORATOROFFLINE'), (300, b'VIDEOCOLLECTIONCREATED'), (301, b'VIDEOCOLLECTIONUPDATED'), (302, b'VIDEOCOLLECTIONDELETED'), (350, b'VIDEOADDEDTOCOLLECTION'), (351, b'VIDEOREMOVEDFROMCOLLECTION'), (450, b'PENDINGUSERINVITEDASPROJECTADMIN'), (451, b'PENDINGUSERINVITEDASPROJECTUSER'), (500, b'PROJECTREPLYCOMMENTCREATED'), (501, b'PROJECTCOMMENTUPDATED'), (502, b'PROJECTREPLYCOMMENTDELETED'), (600, b'TIMEDVIDEOROOTCOMMENTCREATED'), (601, b'TIMEDVIDEOCOMMENTUPDATED'), (602, b'TIMEDVIDEOCOMMENTDELETED'), (700, b'TIMEDVIDEOREPLYCOMMENTCREATED'), (701, b'TIMEDVIDEOREPLYCOMMENTUPDATED'), (702, b'TIMEDVIDEOREPLYCOMMENTDELETED')), db_index=True),
        ),
    ]

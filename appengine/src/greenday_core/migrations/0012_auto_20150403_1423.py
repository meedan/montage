# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0011_project_video_tag_instance_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='tag_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='video',
            name='tag_instance_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
    ]

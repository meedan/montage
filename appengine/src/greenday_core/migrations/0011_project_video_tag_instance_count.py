# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0010_auto_20150401_1206'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='video_tag_instance_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
    ]

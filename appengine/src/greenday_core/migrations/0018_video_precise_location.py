# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0017_auto_20150609_1112'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='precise_location',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]

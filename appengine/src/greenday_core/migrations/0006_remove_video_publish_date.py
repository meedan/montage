# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0005_auto_20141230_1638'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='video',
            name='publish_date',
        ),
    ]

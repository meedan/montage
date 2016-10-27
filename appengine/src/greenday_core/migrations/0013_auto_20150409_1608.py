# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0012_auto_20150403_1423'),
    ]

    operations = [
        migrations.AddField(
            model_name='pendinguser',
            name='is_whitelisted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='is_whitelisted',
            field=models.BooleanField(default=False, verbose_name='Is whitelisted?'),
            preserve_default=True,
        ),
    ]

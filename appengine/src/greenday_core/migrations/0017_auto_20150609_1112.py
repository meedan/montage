# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import greenday_core.models.user
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0016_auto_20150521_1325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='user',
            field=models.ForeignKey(related_name=b'actions', on_delete=models.SET(greenday_core.models.user.get_sentinel_user), db_constraint=False, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]

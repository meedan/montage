# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import greenday_core.utils
import greenday_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0003_auto_20141209_1911'),
    ]

    operations = [
        migrations.AddField(
            model_name='timedvideocomment',
            name='project',
            field=models.ForeignKey(default=1, to='greenday_core.Project'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='projectuser',
            name='pending_user',
            field=models.ForeignKey(related_name=b'projectusers', on_delete=greenday_core.utils.CONDITIONAL_CASCADE(greenday_core.models.project.project_user_has_user_id), to='greenday_core.PendingUser', null=True),
        ),
    ]

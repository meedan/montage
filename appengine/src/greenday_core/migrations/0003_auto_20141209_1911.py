# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0002_auto_20141202_1506'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectComment',
            fields=[
                ('taginstance_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='greenday_core.TagInstance')),
                ('lft', models.PositiveIntegerField(db_index=True)),
                ('rgt', models.PositiveIntegerField(db_index=True)),
                ('tree_id', models.PositiveIntegerField(db_index=True)),
                ('depth', models.PositiveIntegerField(db_index=True)),
                ('text', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('greenday_core.taginstance', models.Model),
        ),
        migrations.AlterField(
            model_name='projectuser',
            name='pending_user',
            field=models.ForeignKey(related_name=b'projectusers', to='greenday_core.PendingUser', null=True),
        ),
    ]

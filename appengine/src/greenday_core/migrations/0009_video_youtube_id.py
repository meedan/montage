# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, models, migrations


def add_youtube_id_to_video(apps, schema_editor):
	# because Django's F() expressions don't support joins
	raw = (
		'update greenday_core_video a inner join greenday_core_youtubevideo b '
		'on a.youtube_video_id = b.id '
		'set a.youtube_id = b.youtube_id'
	)
	cursor = connection.cursor()
	cursor.execute(raw)

class Migration(migrations.Migration):

    dependencies = [
        ('greenday_core', '0008_auto_20150219_0946'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='youtube_id',
            field=models.CharField(default='', max_length=200, db_index=True),
            preserve_default=False,
        ),
        migrations.RunPython(
            add_youtube_id_to_video,
            lambda *a: None  # noop
        ),
    ]

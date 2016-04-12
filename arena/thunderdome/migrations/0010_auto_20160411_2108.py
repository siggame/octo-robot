# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0009_auto_20160409_1308'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='swissUsed',
        ),
        migrations.AddField(
            model_name='game',
            name='tie_reason',
            field=models.CharField(default=b'Unknown reason', max_length=1024),
        ),
    ]

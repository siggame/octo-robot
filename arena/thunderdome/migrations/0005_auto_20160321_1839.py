# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0004_game_tied'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='lose_reason',
            field=models.CharField(default=b'Unknown reason', max_length=1024),
        ),
        migrations.AddField(
            model_name='game',
            name='win_reason',
            field=models.CharField(default=b'Unknown reason', max_length=1024),
        ),
    ]

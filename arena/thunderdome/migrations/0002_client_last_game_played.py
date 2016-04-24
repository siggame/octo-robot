# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='last_game_played',
            field=models.IntegerField(default=-1),
        ),
    ]

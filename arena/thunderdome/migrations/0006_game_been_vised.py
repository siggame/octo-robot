# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0005_auto_20160422_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='been_vised',
            field=models.BooleanField(default=False),
        ),
    ]

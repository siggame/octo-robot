# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0006_client_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='swissUsed',
            field=models.BooleanField(default=False),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0003_remove_client_test_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='tied',
            field=models.BooleanField(default=False),
        ),
    ]

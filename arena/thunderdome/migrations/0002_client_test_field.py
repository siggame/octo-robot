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
            name='test_field',
            field=models.IntegerField(default=100),
        ),
    ]

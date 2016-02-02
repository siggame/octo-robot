# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0002_client_test_field'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='client',
            name='test_field',
        ),
    ]

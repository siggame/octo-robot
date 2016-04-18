# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0010_auto_20160411_2108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='tie_reason',
            field=models.CharField(default=b'', max_length=1024),
        ),
    ]

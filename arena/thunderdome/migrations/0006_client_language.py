# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0005_auto_20160321_1839'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='language',
            field=models.CharField(default=b'', max_length=50),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0005_auto_20160417_1448'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='embargo_reason',
            field=models.CharField(default=b'See arena team for details', max_length=255),
        ),
    ]

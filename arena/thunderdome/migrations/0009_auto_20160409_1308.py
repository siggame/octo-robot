# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thunderdome', '0008_client_embargo_reason'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='embargo_reason',
            field=models.CharField(default=b'See arena team for details', max_length=255),
        ),
    ]

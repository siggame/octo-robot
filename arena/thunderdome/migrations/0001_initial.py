# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ArenaConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=False)),
                ('config_name', models.CharField(default=b'', max_length=200)),
                ('game_name', models.CharField(default=b'', max_length=200)),
                ('beanstalk_host', models.CharField(default=b'', max_length=200)),
                ('client_prefix', models.CharField(default=b'ssh://webserver@megaminerai.com', max_length=200)),
                ('req_queue_length', models.IntegerField(default=5)),
                ('api_url_template', models.CharField(default=b'http://megaminerai.com/api/repo/tags/', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('current_version', models.CharField(default=b'', max_length=100, null=True)),
                ('embargoed', models.BooleanField(default=False)),
                ('eligible', models.BooleanField(default=False)),
                ('repo', models.CharField(default=b'', max_length=200)),
                ('seed', models.IntegerField(default=0)),
                ('score', models.FloatField(default=0.0)),
                ('rating', models.IntegerField(default=2300)),
                ('stats', models.TextField(default=b'')),
                ('game_name', models.CharField(default=b'', max_length=200)),
                ('missing', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'New', max_length=20)),
                ('priority', models.IntegerField(default=1000)),
                ('gamelog_url', models.CharField(default=b'', max_length=200)),
                ('p0out_url', models.CharField(default=b'', max_length=200)),
                ('p1out_url', models.CharField(default=b'', max_length=200)),
                ('visualized', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0), null=True)),
                ('completed', models.DateTimeField(null=True)),
                ('claimed', models.BooleanField(default=True)),
                ('tournament', models.BooleanField(default=False)),
                ('stats', models.TextField(default=b'')),
            ],
            options={
                'ordering': ['-completed', '-id'],
            },
        ),
        migrations.CreateModel(
            name='GameData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('compiled', models.NullBooleanField()),
                ('won', models.NullBooleanField()),
                ('output_url', models.CharField(default=b'', max_length=200)),
                ('version', models.CharField(default=b'', max_length=100, null=True)),
                ('stats', models.TextField(default=b'')),
                ('client', models.ForeignKey(to='thunderdome.Client')),
                ('game', models.ForeignKey(to='thunderdome.Game')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('losses_to_eliminate', models.IntegerField(default=3)),
                ('wins_to_win', models.IntegerField(default=4)),
                ('father_type', models.TextField(default=b'win')),
                ('mother_type', models.TextField(default=b'win')),
                ('status', models.TextField(default=b'Waiting')),
                ('root', models.BooleanField(default=False)),
                ('tournament', models.IntegerField(default=20)),
                ('father', models.ForeignKey(related_name='matches_fathered', blank=True, to='thunderdome.Match', null=True)),
                ('games', models.ManyToManyField(to='thunderdome.Game')),
                ('loser', models.ForeignKey(related_name='matches_lost', blank=True, to='thunderdome.Client', null=True)),
                ('mother', models.ForeignKey(related_name='matches_mothered', blank=True, to='thunderdome.Match', null=True)),
                ('p0', models.ForeignKey(related_name='matches_as_p0', blank=True, to='thunderdome.Client', null=True)),
                ('p1', models.ForeignKey(related_name='matches_as_p1', blank=True, to='thunderdome.Client', null=True)),
                ('winner', models.ForeignKey(related_name='matches_won', blank=True, to='thunderdome.Client', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Referee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('blaster_id', models.CharField(default=b'', max_length=200)),
                ('referee_id', models.CharField(default=b'', max_length=20)),
                ('started', models.DateTimeField()),
                ('last_update', models.DateTimeField()),
                ('dead', models.BooleanField(default=False)),
                ('stats', models.TextField(default=b'')),
                ('games', models.ManyToManyField(to='thunderdome.Game')),
            ],
        ),
        migrations.CreateModel(
            name='WinRatePrediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('prediction', models.FloatField(default=0.5)),
                ('loser', models.ForeignKey(related_name='lose_prediction', to='thunderdome.Client')),
                ('winner', models.ForeignKey(related_name='win_prediction', to='thunderdome.Client')),
            ],
            options={
                'ordering': ['-prediction'],
            },
        ),
        migrations.AddField(
            model_name='game',
            name='clients',
            field=models.ManyToManyField(related_name='games_played', through='thunderdome.GameData', to='thunderdome.Client'),
        ),
        migrations.AddField(
            model_name='game',
            name='loser',
            field=models.ForeignKey(related_name='games_lost', blank=True, to='thunderdome.Client', null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='winner',
            field=models.ForeignKey(related_name='games_won', blank=True, to='thunderdome.Client', null=True),
        ),
    ]

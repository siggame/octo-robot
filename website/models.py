####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
####

# Standard Imports
from datetime import datetime

# Non-Django 3rd Party Imports
import beanstalkc
import time
import json

# Django Imports
from django import forms
from django.db import models
from django.db.models import Max


class Client(models.Model):
    ### A competitor in the arena
    name = models.CharField(max_length=100)
    current_version = models.CharField(max_length=100, default='', null=True)
    embargoed = models.BooleanField(default=False)  # fail to compile
    eligible = models.BooleanField(default=True)
    repo = models.CharField(max_length=200, default='')
    seed = models.IntegerField(default=0)
    score = models.FloatField(default=0.0)
    rating = models.IntegerField(default=2300)

    def inc_score(self, delta):
        # wishing for an atomic increment
        c = Client.objects.get(pk=self.pk)
        c.score += delta
        c.save()
        self.score = c.score

    def last_game(self):
        '''returns the pk of the most recently created gamedata associated
        with this client'''
        last = self.gamedata_set.aggregate(Max('pk'))
        if last['pk__max']:
            return last['pk__max']
        else:
            return -1

    def last_visualized(self):
        # FIXME this probably blows up. find out if it does.
        vis = self.games_played.all().aggregate(Max('visualized'))
        if vis['visualized__max']:
            return vis['visualized__max']
        else:
            return datetime(1970, 1, 1, 0, 0)

    def fitness(self):
        return self.rating
        #games_complete = self.games_played.filter(status="Complete").count()
        #if games_complete == 0:
        #    return 0
        #else:
        #    return self.score / games_complete

    def __unicode__(self):
        return self.name


class WinRatePrediction(models.Model):
    ### The predicted win rate for p0 over p1
    p0 = models.ForeignKey(Client)
    p1 = models.ForeignKey(Client)
    prediction = models.FloatField(default=0.5)


class Game(models.Model):
    ### A single game
    clients = models.ManyToManyField(Client, through='GameData',
                                     related_name='games_played')
    winner = models.ForeignKey(Client, null=True, blank=True,
                               related_name='games_won')
    loser = models.ForeignKey(Client, null=True, blank=True,
                              related_name='games_lost')
    status = models.CharField(max_length=20, default='New')
    priority = models.IntegerField(default=1000)
    gamelog_url = models.CharField(max_length=200, default='')
    p0out_url = models.CharField(max_length=200, default='')  # unused
    p1out_url = models.CharField(max_length=200, default='')  # unused
    visualized = models.DateTimeField(default=datetime(1970, 1, 1), null=True)
    completed = models.DateTimeField(null=True)
    claimed = models.BooleanField(default=True)
    tournament = models.BooleanField(default=False)
    stats = models.TextField(default='')  # holds extra stuff via JSON

    class Meta():
        ordering = ['-completed', '-id']

    def schedule(self):
        if self.status != 'New':
            return False
        if self.pk is None:
            self.save()
        return self.force_schedule()

    def get_spect_rating(self):
        data = json.loads(self.stats)
        try:
            r = data['spect_rating']
        except:
            r = 0
        return r

    def force_schedule(self):
        c = beanstalkc.Connection()
        c.use('game-requests')
        payload = json.dumps({'game_id'    : str(self.pk),
                              'entry_time' : str(time.time())})
        c.put(payload, priority=self.priority, ttr=600)
        c.close()
        self.status = 'Scheduled'
        self.save()
        return True

    def __unicode__(self):
        return unicode(self.pk)

    def game_time(self):
        return (self.completed - self.started)


class GameData(models.Model):
    ### each Game will have one of these for each competitor in that game
    game = models.ForeignKey(Game)
    client = models.ForeignKey(Client)
    compiled = models.NullBooleanField()
    won = models.NullBooleanField()
    output_url = models.CharField(max_length=200, default='')
    version = models.CharField(max_length=100, default='', null=True)
    stats = models.TextField(default='')  # holds extra stuff via JSON

    def __unicode__(self):
        return u"%s - %s" % (self.game.pk, self.client.name)

    class Meta():
        ordering = ['id']


class InjectedGameForm(forms.Form):
    ### Used to manually inject a game into the queue
    priority = forms.IntegerField(min_value=0, max_value=1000)
    clientOne = forms.ChoiceField()
    clientTwo = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(InjectedGameForm, self).__init__(*args, **kwargs)
        self.fields['clientOne'].choices = [(x.pk, x.name) for x in
                                            Client.objects.all()]
        self.fields['clientTwo']. choices = [(x.pk, x.name) for x in
                                             Client.objects.all()]


class Match(models.Model):
    ### A multi-game match
    p0 = models.ForeignKey(Client, null=True, blank=True,
                           related_name='matches_as_p0')
    p1 = models.ForeignKey(Client, null=True, blank=True,
                           related_name='matches_as_p1')
    winner = models.ForeignKey(Client, null=True, blank=True,
                               related_name='matches_won')
    loser = models.ForeignKey(Client, null=True, blank=True,
                              related_name='matches_lost')
    father = models.ForeignKey('self', null=True, blank=True,
                               related_name='matches_fathered')
    mother = models.ForeignKey('self', null=True, blank=True,
                               related_name='matches_mothered')
    games = models.ManyToManyField(Game)
    losses_to_eliminate = models.IntegerField(default=3)
    wins_to_win = models.IntegerField(default=4)
    father_type = models.TextField(default='win')
    mother_type = models.TextField(default='win')
    status = models.TextField(default='Waiting')
    root = models.BooleanField(default=False)
    tournament = models.IntegerField(default=20)

    def __unicode__(self):
        return u"%s - %s" % (self.p0.name, self.p1.name)


class Referee(models.Model):
    blaster_id = models.CharField(max_length=200, default='')
    referee_id = models.CharField(max_length=20, default='')
    started = models.DateTimeField(editable=True)
    last_update = models.DateTimeField(editable=True)
    games = models.ManyToManyField(Game)
    dead = models.BooleanField()
    stats = models.TextField(default='')  # holds extra stuff via JSON

    def __unicode__(self):
        return u"Ref %s (Blaster %s) %s Games Per Hour" % (self.referee_id,
                                                           self.blaster_id,
                                                           self.compute_rate())

    def compute_rate(self,
                     only_complete=True,
                     slice_end=None,
                     slice_start=None):
        if slice_end is None:
            slice_end = datetime.utcnow()
        if slice_start is None:
            slice_start = self.started
        time_alive = (slice_end - slice_start).total_seconds()
        games_completed = self.games.filter(completed__gte=slice_start,
                                            completed__lt=slice_end)
        if only_complete:
            games_completed = games_completed.filter(status='Complete').count()
        else:
            games_completed = games_completed.count()
        rate = games_completed / (time_alive / 3600)
        return rate

    def last_match(self, only_complete=False):
        if only_complete:
            game = self.games.filter(status='Completed')
        else:
            game = self.games.all()
        if game.count() < 1:
            return None
        else:
            return game.order_by('-pk')[0]

    def games_completed(self):
        return self.games.filter(status='Complete').count()

    def rate_table(self, time_period, step, interval, only_complete=True):
        rate = []
        slice_start = datetime.utcnow() - time_period
        slice_end = slice_start + interval
        while slice_end <= (datetime.utcnow()):
            curr = self.compute_rate(only_complete, slice_end, slice_start)
            if curr > 0:
                rate.append((slice_end, int(curr)))
            else:
                rate.append((slice_end, None))

            slice_start += step
            slice_end += step
        return rate

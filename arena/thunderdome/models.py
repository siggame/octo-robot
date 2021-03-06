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
from django.contrib.postgres.fields import ArrayField

class Client(models.Model):
    name = models.CharField(max_length=200)
    current_version = models.CharField(max_length=100, default='', null=True)
    current_tag = models.CharField(max_length=200, default='', null=True)
    embargoed = models.BooleanField(default=False) # broke
    embargo_reason = models.CharField(max_length=255, default='')
    eligible = models.BooleanField(default=False) # able to compete for prizes
    repo = models.CharField(max_length=200, default='')
    seed = models.IntegerField(default=0)
    score = models.FloatField(default=0.0)
    rating = models.FloatField(default=2300.0)
    stats = models.TextField(default='') # extra json field for stuff
    game_name = models.CharField(max_length=200, default='')
    missing = models.BooleanField(default=False)
    language = models.CharField(max_length=50, default='')
    last_game_played = models.IntegerField(default=-1)
    buchholz = models.FloatField(default=0.0)
    sumrate = models.FloatField(default=0.0)
    num_black = models.FloatField(default=0.0)
    winrate = models.FloatField(default=0.0)

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
    winner = models.ForeignKey(Client, related_name='win_prediction')
    loser = models.ForeignKey(Client, related_name='lose_prediction')
    prediction = models.FloatField(default=0.5)
    

    class Meta():
        ordering = ['-prediction']

    def __unicode__(self):
        return "%s - %s, %f" % (self.winner.name, self.loser.name,
                                self.prediction)

class Game(models.Model):
    ### A single game
    clients = models.ManyToManyField(Client, through='GameData',
                                     related_name='games_played')
    winner = models.ForeignKey(Client, null=True, blank=True,
                               related_name='games_won')
    loser = models.ForeignKey(Client, null=True, blank=True,
                              related_name='games_lost')
    status = models.CharField(max_length=20, default='New') # a few states New, Complete, Failed, Building
    priority = models.IntegerField(default=1000)
    gamelog_url = models.CharField(max_length=1000, default='')
    p0out_url = models.CharField(max_length=200, default='') # unused
    p1out_url = models.CharField(max_length=200, default='') # unused
    visualized = models.DateTimeField(default=datetime(1970, 1, 1), null=True)
    been_vised = models.BooleanField(default=False)
    completed = models.DateTimeField(null=True)
    claimed = models.BooleanField(default=True)
    tournament = models.BooleanField(default=False)
    tied = models.BooleanField(default=False)
    stats = models.TextField(default='') # holds extra stuff via JSON
    win_reason = models.CharField(max_length=1024, default='Unknown reason') #Reason the winner won
    lose_reason = models.CharField(max_length=1024, default='Unknown reason') #Reason the loser lost
    tie_reason = models.CharField(max_length=1024, default='') #Reason for a tie
    score = models.IntegerField(default=-1)
    discon_happened = models.BooleanField(default=False)

    class Meta():
        ordering = ['-completed', '-id']

    def set_visualized(self):
        visualized = datetime.now()
        self.save()
    
    def schedule(self):
        if self.status != 'New':
            return False
        if self.pk is None:
            self.save()
        return self.force_schedule()

    def update_calc_rating(self):
        # from masterblaster.utilities.kmeans import assign_calc_rating
        # assign_calc_rating(self)
        pass

    def set_calc_rating(self, rating):
        data = json.loads(self.stats)
        data['calc_rating'] = rating
        self.stats = json.dumps(data)
        self.save()
        
    def get_calc_rating(self):
        return self.score

    def add_rating(self, rating):
        data = json.loads(self.stats)
        try:
            data['rating'].append(int(rating))
        except:
            data['rating'] = []
            data['rating'].append(int(rating))
        self.stats = json.dumps(data)
        self.save()

    def get_average_rating(self):
        data = json.loads(self.stats)
        try:
            r = sum(data['rating'])/float(len(data['rating']))
        except KeyError:
            r = 0
        return r

    # TODO clean up force schedule some of the code is very out of date
    def force_schedule(self):
        c = beanstalkc.Connection()
        c.use('game-requests') # this is out of date very out of date
        payload = json.dumps({'game_id' : str(self.pk),
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
    
    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Game._meta.fields]

class GameData(models.Model):
    ### each Game will have one of these for each competitor in that game
    game = models.ForeignKey(Game)
    client = models.ForeignKey(Client)
    compiled = models.NullBooleanField()
    won = models.NullBooleanField()
    output_url = models.CharField(max_length=200, default='')
    version = models.CharField(max_length=100, default='', null=True)
    stats = models.TextField(default='') # holds extra stuff via JSON
    
    class Meta():
        ordering = ['id']

    def __unicode__(self):
        
        return u"%s - %s" % (self.game.pk , self.client.name)

class InjectedGameForm(forms.Form):
    ### Used to manually inject a game into the queue
    client_One = forms.ChoiceField()
    client_Two = forms.ChoiceField()
    
    def __init__(self, *args, **kwargs):
        super(InjectedGameForm, self).__init__(*args, **kwargs)
        self.fields['client_One'].choices = [(x.pk, x.name) for x in 
                                            Client.objects.all().order_by('name')]
        self.fields['client_Two'].choices = [(x.pk, x.name) for x in
                                            Client.objects.all().order_by('name')]

class SearchGamesForm(forms.Form):
    client = forms.ChoiceField()
    start = forms.IntegerField(initial=6, min_value=-6, label="Start Time (hours ago)")
    end = forms.IntegerField(initial=0, min_value=-6, label="End Time (hours ago)")
    showFailed = forms.BooleanField(required=False, label="Show All Failed Games")
    
    def __init__(self, *args, **kwargs):
        super(SearchGamesForm, self).__init__(*args, **kwargs)
        self.fields['client'].choices = [(x.pk, x.name) for x in
                                         Client.objects.filter(missing=False).order_by('name')]

class GameStatisticsForm(forms.Form):
    ### Used to view win preditions
    client = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(GameStatisticsForm, self).__init__(*args, **kwargs)
        self.fields['client'].choices = [(x.pk, x.name) for x in
                                            Client.objects.all().order_by('name')]
    
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

    def get_representative_game(self):
        if self.games.all():
            winners_games = self.games.filter(winner=self.winner).filter(status="Complete")
            best_score = -1
            game = None
            for i in winners_games:
                if i.score > best_score:
                    best_score = i.score
                    game = i
            return game
        else:
            return None
    
    def __unicode__(self):
        if self.p0 and self.p1:
            return u"%s - %s" % (self.p0.name, self.p1.name)
        else:
            return u"%s - %s" % (self.status, str(self.root))

class Referee(models.Model):
    blaster_id = models.CharField(max_length=200, default='')
    referee_id = models.CharField(max_length=20, default='')
    started = models.DateTimeField(editable=True)
    last_update = models.DateTimeField(editable=True)
    games = models.ManyToManyField(Game)
    dead = models.BooleanField(default=False)
    stats = models.TextField(default='') # holds extra stuff via JSON
    games_done = models.IntegerField(default=0)

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
            return game.order_by('-completed')[0]

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
                    

class ArenaConfig(models.Model):
    active = models.BooleanField(default=False)
    config_name = models.CharField(max_length=200, default='')
    game_name = models.CharField(max_length=200, default='')
    beanstalk_host = models.CharField(max_length=200, default='')
    client_prefix = models.CharField(max_length=200, default='ssh://webserver@megaminerai.com') # is the prefix url to where clients are stored
    req_queue_length = models.IntegerField(default=5) # Number of games to keep queued
    api_url_template = models.CharField(max_length=200, default='http://megaminerai.com/api/repo/tags/')
    client_port = models.IntegerField(default=3000) # Port that the clients will connect to
    web_client_port = models.IntegerField(default=3088) # Port that the web clients will connect to
    api_port = models.IntegerField(default=3080) # Port that the gameserver status will be at
    persistent = models.BooleanField(default=False)
    mode = models.CharField(max_length=200, default='git')
    
    parameters = {'active' : active,
                  'config_game' : config_name,
                  'game_name' : game_name,
                  'beanstalk_host' : beanstalk_host,
                  'client_prefix' : client_prefix,
                  'req_queue_length' : req_queue_length,
                  'api_url_template' : api_url_template,
                  'client_port' : client_port,
                  'web_client_port' : web_client_port,
                  'api_port' : api_port,
                  'persistent' : persistent,
                  'mode' : mode}
    
    def __unicode__(self):
        return "Active" + str(self.active) + "\n Config name " + str(self.config_name) + \
            "\n Game name " + str(self.game_name) + " \n Client Prefix " + str(self.client_prefix)



class SettingsForm(forms.Form):
    arenaConfig = forms.ChoiceField()

    def __init__(self, *args, **kwarfs):
        super(SettingsForm, self).__init__(*args, **kwarfs)
        self.fields['arenaConfig'].choices = [(x.pk, x.config_name) for x in ArenaConfig.objects.all()]
        
class GameStats(models.Model):
    game = models.CharField(max_length=200, default='')
    interesting_win_reasons = ArrayField(models.CharField(max_length=1024, default=''), default=[])
    numPlayed = models.IntegerField(default=0)
    maxSize = models.IntegerField(default=0)
    
    def __unicode__(self):
        return self.game

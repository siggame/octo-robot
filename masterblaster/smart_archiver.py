#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####


# Standard Imports
import time
import urllib
import math
import gzip
import os
import urllib2
from copy import copy
from multiprocessing import Process
from datetime import datetime, timedelta
from bz2 import BZ2Decompressor
from collections import defaultdict

# Non-Django 3rd Party Imports
import beanstalkc
import json

# My Imports
from thunderdome.config import game_name
from thunderdome.models import Client, Game, GameData, Referee
from thunderdome.models import WinRatePrediction


import django
django.setup()

#from datatizer import add_gamelog_data

#from thunderdome.loggly_logging import log
from gviz_api import DataTable

import settings

# Rating Imports
#from utilities import gamelog_regepars
#from utilities import kmeans

stalk = None
tourny_time = True 

games = Game.objects.filter(tournament=False).filter(status='Complete')


# will not be using k-means clustering this competition
#if tourny_time:
#    print "Generating Clusters"
#    clusters = kmeans.obtain_clusters(games, 8)

print "Thunder birds are a go go!"


def main():
    result_tube = "game-results-%s" % game_name
    #p = Process(target=processing)
    #p.start()

    #CALEB: I commented out the global here to see if that fixes the memory
    #  leak if everything breaks comment it back in
    global stalk
    stalk = beanstalkc.Connection()
    stalk.watch(result_tube)

    while True:
        job = stalk.reserve()
        request = json.loads(job.body)
        try:
            game = Game.objects.get(id=int(request['number']))
        except:
            job.delete()
            continue
        game.stats = job.body
        if game.status != request['status']:
            game.status = request['status']
            if game.status in ["Complete", "Failed"]:
                if 'gamelog_url' in request:
                    game.gamelog_url = request['gamelog_url']
                if 'completed' in request:
                    game.completed = request['completed']
                game.tied = request['tied']
                if game.tied or game.status == 'Failed':
                    try:
                        game.tie_reason = request['tie_reason']
                    except:
                        print "Warning: Unable to read tie_reason for game", game
                    count = 0
                    for guy in request['clients']:
                        if count > 0:
                            print "vs.",
                        print guy['name'],
                        count += 1
                    print ":", game.tie_reason
                else:
                    game.win_reason = request['win_reason']
                    game.lose_reason = request['lose_reason']
                    print request['winner']['name'], "beat", request['loser']['name'], "because", game.win_reason
                handle_completion(request, game)
            game.save()
            print "Game", request['number'], "status", request['status']
        job.delete()
        del job.conn
        del job
        (r, c) = Referee.objects.get_or_create(
            blaster_id=request['blaster_id'],
            referee_id=request['referee_id'],
            defaults={'started': datetime.now(),
                      'last_update': datetime.now()})
        r.last_update = datetime.now()
        r.dead = False
        r.games.add(game)
        r.save()
        request.update({'reporter': 'archiver'})
        for x in Referee.objects.filter(dead=False):
            if x.last_update < datetime.now() - timedelta(hours=1):
                x.dead = True
            x.save()


def handle_completion(request, game):
    if 'winner' in request:
        game.winner = Client.objects.get(name=request['winner']['name'])
    if 'loser' in request:
        game.loser = Client.objects.get(name=request['loser']['name'])

    if 'winner' in request and 'loser' in request:
        assign_elo(game.winner, game.loser)
        adjust_win_rate(game.winner, game.loser)


    #add_gamelog_data(game)

    # increment winner and losers game played
    #for client in [game.winner, game.loser]:
    #    try:
    #        stats = json.loads(client.stats)
    #    except ValueError:
    #        stats = defaultdict(int)
    #    stats['games-played'] = stats['games-played'] + 1
    #    client.stats = json.dumps(stats)

    clidict = dict()
    for client in request['clients']:
        clidict[client['name']] = client
    for gd in GameData.objects.filter(game=game):
        if gd.client == game.winner:
            gd.won = True
        gd.compiled = clidict[gd.client.name]['compiled']
        gd.version = clidict[gd.client.name]['tag']
        if not gd.compiled:
            gd.client.embargoed = True
            gd.client.embargo_reason = "Your client didn't compile"
        if 'noconnect' in clidict[gd.client.name]:
	    gd.client.embargoed = True
            gd.client.embargo_reason = "Your client didn't connect to the game"
        if 'gamservdied' in clidict[gd.client.name]:
	    gd.client.embargoed = True
            gd.client.embargo_reason = "Gameserver broke, please see an Arena Dev"
        if 'discon' in clidict[gd.client.name]:
            game.discon_happened = True
            game.save()
	    #gd.client.embargoed = True
            #gd.client.embargo_reason = "Your client disconnected from the game unexpectedly"
        try:
            stats = json.loads(gd.client.stats)
        except:
            stats = {}
        gd.client.last_game_played = game.pk
        gd.client.stats = json.dumps(stats)
        try:
            gd.output_url = clidict[gd.client.name]['output_url']
        except KeyError:
            pass
        gd.client.save()
        gd.save()


def assign_elo(winner, loser):
    delta = winner.rating - loser.rating
    exp = (-1 * delta) / 400
    odds = 1 / (1 + math.pow(10, exp))
    if winner.rating < 2100:
        k = 32
    elif winner.rating > 2500:
        k = 12
    else:
        k = 24
    modifier = k * (1 - odds)
    winner.rating += modifier
    loser.rating = max([1, loser.rating - modifier])
    winner.save()
    loser.save()


def adjust_win_rate(w, l, alpha=0.15):
    win_p, w_created = WinRatePrediction.objects.get_or_create(winner=w, loser=l)
    old_win = copy(win_p)
    lose_p, l_created = WinRatePrediction.objects.get_or_create(winner=l, loser=w)
    old_lose = copy(lose_p)
    win_p.prediction += alpha * (1 - win_p.prediction)
    lose_p.prediction -= alpha * lose_p.prediction
    print "Prediction Updated:", w.name, old_win.prediction, "to", win_p.prediction
    print "Prediction Updated:", l.name, old_lose.prediction, "to", lose_p.prediction
    win_p.save()
    lose_p.save()


if __name__ == "__main__":
    main()

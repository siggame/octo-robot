#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import json
import time

# My Imports
from thunderdome.models import Game, GameData
from thunderdome.config import persistent

def sked(guy0, guy1, stalk, origin, priority=1000, ttr=400, claimed=True):
    '''Schedule these guys for a game'''
    if(origin == "Priority Game Request"):
        if(Game.objects.filter(priority=1).filter(status="Scheduled").count() >= 300):
            print 'Custom game not scheduled as there are more than 300 custom games scheduled'
            return
    game = Game.objects.create()
    game.status = "Scheduled"
    game.claimed = claimed
    game.priority = priority
    if origin == 'Tournament':
        game.tournament = True
    for guy in (guy0, guy1):
        GameData(game=game, client=guy).save()

    payload = {'number'     : str(game.pk),
               'status'     : "Scheduled",
               'time_scheduled' : str(time.time()),
               'origin'     : origin,
               'timeout'    : ttr,
               'persistent' : persistent,
               'clients'    : [{'name' : p.name,
                                'repo' : p.repo,
                                'hash' : p.current_version,
                                'tag'  : p.current_tag,
                                'language': p.language}
                               for p in (guy0, guy1)]}

    game.stats = json.dumps(payload)
    stalk.put(game.stats, priority=priority, ttr=ttr)
    game.save()
    if(origin == "Priority Game Request"):
        print 'scheduled', game, guy0, payload['clients'][0]['tag'], guy1, payload['clients'][1]['tag'], 'Current Custom Game Count:', Game.objects.filter(priority=1).filter(status="Scheduled").count()
    else:
        print 'scheduled', game, guy0, payload['clients'][0]['tag'], guy1, payload['clients'][1]['tag']
    payload.update({'reporter':origin})
    # log.info(json.dumps(payload))
    return game

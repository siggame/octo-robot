#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import json
import time

# My Imports
from thunderdome.models import Game, GameData

def sked(guy0, guy1, stalk, origin, priority=1000, ttr=400, claimed=True):
    '''Schedule these guys for a game'''
    game = Game.objects.create()
    game.status = "Scheduled"
    game.claimed = claimed
    for guy in (guy0, guy1):
        GameData(game=game, client=guy).save()

    payload = {'number'     : str(game.pk),
               'status'     : "Scheduled",
               'time_scheduled' : str(time.time()),
               'origin'     : origin,
               'timeout'    : ttr,
               'clients'    : [{'name' : p.name,
                                'repo' : p.repo,
                                'hash' : p.current_version,
                                'tag'  : p.current_tag,
                                'language': p.language}
                               for p in (guy0, guy1)]}

    game.stats = json.dumps(payload)
    stalk.put(game.stats, priority=priority, ttr=ttr)
    game.save()
    print 'scheduled', game, guy0, payload['clients'][0]['tag'], guy1, payload['clients'][1]['tag']
    payload.update({'reporter':origin})
    # log.info(json.dumps(payload))
    return game

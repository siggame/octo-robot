#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import json
import time

# My Imports
from thunderdome.models import Game, GameData
from thunderdome.loggly_logging import log


def sked(guy0, guy1, stalk, origin):
    '''Schedule these guys for a game'''
    game = Game.objects.create()
    game.status = "Scheduled"
    for guy in (guy0, guy1):
        GameData(game=game, client=guy).save()

    payload = {'number'         : str(game.pk),
               'status'         : "Scheduled",
               'time_scheduled' : str(time.time()),
               'origin'         : origin,
               'clients' : [{'name' : p.name,
                             'repo' : p.repo,
                             'tag'  : p.current_version}
                            for p in (guy0, guy1)]}
    game.stats = json.dumps(payload)
    stalk.put(game.stats)
    game.save()
    print 'scheduled', game, guy0, guy1
    payload.update({'reporter': origin})
    log.info(json.dumps(payload))

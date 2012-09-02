#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

from config import game_name

# Some magic to get a standalone python program hooked in to django
import bootstrap

# Non-Django 3rd Party Imports
from itertools import combinations
import beanstalkc
import urllib, json
import time

# My Imports
from thunderdome.models import Client, Game, GameData

stalk = None

def main():
    req_tube = "game-requests-%s" % game_name
    
    global stalk
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    clients = Client.objects.filter(eligible=True))
    for (guy, otherguy) in combinations(clients,2):
        sked(guy, otherguy)
        sked(otherguy, guy)

 
def sked(client, partner):
    '''Sched these guys for a game'''
    players = [client, partner]
 
    game = Game.objects.create()
    [GameData(game=game, client=x).save() for x in players]
    game.tournament = True
    game.status = "Scheduled"
    
    payload_d = { 'number'         : str(game.pk),
                  'status'         : "Scheduled",
                  'time_scheduled' : str(time.time())
                  'tournament'     : True,
                  'clients' : [{'name' : p.name,
                                'repo' : p.repo,
                                'tag'  : p.current_version}
                               for p in players ]}
    game.stats = json.dumps(payload_d)
    game.save()
    stalk.put(game.stats)
    print 'scheduled', game, client, partner

    
if __name__ == "__main__":
    main()

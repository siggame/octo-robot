#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Some magic to get a standalone python program hooked in to django
import bootstrap

# Non-Django 3rd Party Imports
from itertools import combinations
import beanstalkc
import urllib, json
import time

# My Imports
from thunderdome.config import game_name
from thunderdome.models import Client, Game, GameData
from scheduler_roundrobin import skedRoundRobin
from seeder import seed

stalk = None

def main():
    req_tube = "game-requests-%s" % game_name

    global stalk
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    seed()
    clients = list(Client.objects.filter(eligible=True)
                                 .filter(embargoed=False))
    clients.sort(key=lambda x: x.seed)

    """ counter = 0
      for c in clients:
    counter +=1

    print counter"""

    byes = 31 #FIXME

    if len(clients) >= 43:
#lowest 2 teams in each group should be eliminated to avoid groups of < 4
      numGroups = (len(clients) - 32)/2
    else:
#lowest 1 team in each group should be eliminated
      numGroups = len(clients) - 32

    clientGroups = [clients[start::numGroups] 
		    for start in xrange(byes,byes+numGroups)]
    
    for group in clientGroups:
      games = skedRoundRobin(group, 3, stalk)
      for game in games:
        game.tournament = True
        game.claimed = True

main()


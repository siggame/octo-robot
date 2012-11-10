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
from scheduler_roundrobin import skedRoundRobin
from seeder import seed

stalk = None

def main():
    req_tube = "game-requests-%s" % game_name

		global stalk
	  stalk = beanstalkc.Connection()
		stalk.use(req_tube)
	  seed()
		clients = list(Client.objects.filter(eligible=True)))
		clients.sort(key=lambda x: x.seed)

		byes = 3 #FIXME

    if len(clients) >= 43:
#lowest 2 teams in each group should be eliminated to avoid groups of < 4
			numGroups = (len(clients) - 32 - byes)/2
		else:
#lowest 1 team in each group should be eliminated
			numGroups = len(clients) - 32 - byes

		clientGroups = [clients[start::numGroups] 
		                for start in xrange(byes,byes+numGroups)]

		for group in clientGroups:
			games = skedRoundRobin(group, 3, stalk)
			for game in games:
				game.tournament = True

main()



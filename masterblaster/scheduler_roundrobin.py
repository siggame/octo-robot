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
from thunderdome.sked import sked

def skedRoundRobin(group, numGames, stalk)
		result = list()
		for (guy, otherguy) in combinations(clients,2):
			for counter in xrange(numGames):
				if (counter % 2):
					g = sked(guy, otherguy, stalk, 'skedRoundRobin')
		  	else:
					g = sked(otherguy, guy, stalk, 'skedRoundRobin')
        result.append(g)

		return result


def main():
    req_tube = "game-requests-%s" % game_name
    
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    clients = Client.objects.filter(eligible=True))
		skedRoundRobin(clients, 2 stalk)

    
if __name__ == "__main__":
	main()



#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
from itertools import combinations

# Non-Django 3rd Party Imports
import beanstalkc

# My Imports
import bootstrap
from thunderdome.config import game_name
from thunderdome.models import Client
from thunderdome.sked import sked

def skedRoundRobin(group, numGames, stalk):
    result = list()
   
    for (guy, otherguy) in combinations(group,2):
      for counter in range(numGames):
        if (counter % 2):
          g = sked(guy, otherguy, stalk, 'skedRoundRobin')
        else:
          g = sked(otherguy, guy, stalk, 'skedRoundRobin')
        #result.append(g)
    return result


def main():
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    clients = Client.objects.filter(eligible=True).filter(embargoed=False)
    skedRoundRobin(clients, 2, stalk)

if __name__ == "__main__":
  main()



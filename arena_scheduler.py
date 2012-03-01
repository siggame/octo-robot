#!/usr/bin/env python2
"""
Missouri S&T ACM SIG-Game Arena (Thunderdome)

The master of all. Responsible for keeping the referees playing matches
so they won't rise up against it.

@author: Matthew Nuckolls <mannr4@mst.edu>
"""

# Some magic to get a standalone python program hooked in to django
import bootstrap
import sys
sys.path = ['/srv/uard', '/srv'] + sys.path


# Non-Django 3rd Party Imports
import beanstalkc
import random
from time import sleep

# My Imports
from thunderdome.models import Client, Game, GameData

def main():
    """
    Intializes a connection to the stalk and starts stuffing games into
    the tubes.
    
    Only schedules one game at a time to allow fast preemption for game
    requests.
    """
    stalk = beanstalkc.Connection()
    if 'game-requests' not in stalk.tubes():
        schedule_a_game()
    while True:
        if stalk.stats_tube('game-requests')['current-jobs-ready'] < 1:
            schedule_a_game()
        sleep(0.2)
    stalk.close()
    
    
def schedule_a_game():
    """
    Schedules a game. Clients are selected by scheduling clients who
    haven't had a game in the longest period of time against a random
    opponent.

    @pre: There are two clients to play a game
    @post: A game has been put into the job queue.
    """
    clients = list(Client.objects.exclude(name='bye')) # list so I can .remove
    worst_client = min(clients, key = lambda x: x.last_game())
    clients.remove(worst_client)
    partner = random.choice(clients)
    game = Game.objects.create()
    [GameData(game=game, client=x).save() for x in (worst_client, partner)]
    game.schedule()
    print 'scheduled', game, worst_client, partner
    
main()

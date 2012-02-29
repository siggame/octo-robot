#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Some magic to get a standalone python program hooked in to django
import sys
sys.path = ['/srv/uard', '/srv'] + sys.path

from django.core.management import setup_environ
import settings

setup_environ(settings)

# Non-Django 3rd Party Imports
import beanstalkc
import random
from time import sleep

# My Imports
from thunderdome.models import Client, Game, GameData

def main():
    stalk = beanstalkc.Connection()
    if 'game-requests' not in stalk.tubes():
        schedule_a_game()
    while True:
        if stalk.stats_tube('game-requests')['current-jobs-ready'] < 1:
            schedule_a_game()
        sleep(0.2)
    stalk.close()
    
    
def schedule_a_game():
    clients = list(Client.objects.exclude(name='bye')) # list so I can .remove
    worst_client = min(clients, key = lambda x: x.last_game())
    clients.remove(worst_client)
    partner = random.choice(clients)
    game = Game.objects.create()
    [GameData(game=game, client=x).save() for x in (worst_client, partner)]
    game.schedule()
    print 'scheduled', game, worst_client, partner
    
main()

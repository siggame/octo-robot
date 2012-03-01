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
import urllib, json
from time import sleep

# My Imports
from thunderdome.models import Client, Game, GameData

def main():
    stalk = beanstalkc.Connection()
    if 'game-requests' not in stalk.tubes():
        update_clients()
        schedule_a_game()
    while True:
        try:
            if stalk.stats_tube('game-requests')['current-jobs-ready'] < 5:
                update_clients()
                schedule_a_game()
        except:
            pass
        sleep(1)
    
    
def schedule_a_game():
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))
#    for client in clients:
#        print client.name
    
    if len(clients) < 2:
        return
    worst_client = min(clients, key = lambda x: x.last_game())
    clients.remove(worst_client)
    partner = random.choice(clients)
    game = Game.objects.create()
    players = [worst_client, partner]
    random.shuffle(players)
    [GameData(game=game, client=x).save() for x in players]
    game.schedule()
    print 'scheduled', game, worst_client, partner

    
def update_clients():
    f = urllib.urlopen("http://megaminerai.com/api/git/repo?c=chess-2012")
    derp = f.read()
    f.close()
    data = json.loads(derp)
    for block in data:
        if block['tag'] is None:
            block['tag'] = ''
        if Client.objects.filter(name=block['login']).count() == 0:
            makeClient( block )
        client = Client.objects.get(name=block['login'])
        if client.current_version != block['tag']:
            client.embargoed = False
            client.current_version = block['tag']
            client.save()
            

def makeClient( block ):
    print block
    client = Client.objects.create()
    client.name = block['login']
    client.current_version = block['tag']
    client.repo = block['path']
    client.embargoed = True
    client.eligible = True
    client.seed = 0
    client.save()


main()


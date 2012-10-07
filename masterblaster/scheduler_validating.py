#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import random
import json
import time

# Non-Django 3rd Party Imports
import beanstalkc

# My Imports
from thunderdome.models import Client, Game, GameData
from config import game_name

stalk = None


def main():
    req_tube = "game-requests-%s" % game_name

    global stalk
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    clients = list(Client.objects.filter(eligible=True))
    for client in clients:
        client.embargoed = False
        client.save()
    while len(clients) > 1:
        (c1, c2) = random.sample(clients, 2)
        clients.remove(c1)
        clients.remove(c2)
        sked(c1, c2)
        sked(c2, c1)

    if len(clients) == 1:
        lastguy = clients[0]
        clients = list(Client.objects.all())
        clients.remove(lastguy)
        otherguy = random.choice(clients)
        sked(lastguy, otherguy)
        sked(otherguy, lastguy)


def sked(client, partner):
    '''Sched these guys for a game'''
    worst_client = client
    players = [worst_client, partner]

    game = Game.objects.create()
    [GameData(game=game, client=x).save() for x in players]

    payload_d = { 'number'         : str(game.pk),
                  'status'         : "Scheduled",
                  'clients'        : list(),
                  'time_scheduled' : str(time.time())}
    for p in players:
        payload_d['clients'].append({ 'name' : p.name,
                                      'repo' : p.repo,
                                      'tag'  : p.current_version })
    game.stats = json.dumps(payload_d)
    game.status = "Scheduled"
    game.save()
    stalk.put(game.stats)
    print 'scheduled', game, worst_client, partner


main()

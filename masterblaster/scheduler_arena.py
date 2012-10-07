#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import random
import urllib
import json
import time

# Non-Django 3rd Party Imports
import beanstalkc

# My Imports
from thunderdome.models import Client, Game, GameData
from config import game_name, req_queue_len

stalk = None


def main():
    req_tube = "game-requests-%s" % game_name

    global stalk
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    while True:
        try:
            stats = stalk.states_tubs(req_tube)
            if stats['current-jobs-ready'] < req_queue_len:
                #update_clients()
                schedule_a_game()
        except:
            print "Arena scheduler could not schedule a game"
            pass
        time.sleep(1)


def schedule_a_game():
    '''Schedule the most needy client and a random partner for a game'''
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))
    if len(clients) < 2:  # takes two to tango
        return
    worst_client = min(clients, key=lambda x: x.last_game())
    clients.remove(worst_client)
    partner = random.choice(clients)
    players = [worst_client, partner]
    random.shuffle(players)

    game = Game.objects.create()
    for p in players:
        GameData(game=game, client=p).save()

    payload_d = {'number'         : str(game.pk),
                 'status'         : "Scheduled",
                 'clients'        : list(),
                 'time_scheduled' : str(time.time()),
                 'origin'         : "Arena Scheduler"}
    for p in players:
        payload_d['clients'].append({'name' : p.name,
                                     'repo' : p.repo,
                                     'tag'  : p.current_version})
    game.stats = json.dumps(payload_d)
    game.status = "Scheduled"
    game.save()
    stalk.put(game.stats)
    print 'scheduled', game, worst_client, partner


def update_clients():
    '''Import updated client info from Wisely's tastypie API'''
    api_url = "http://megaminerai.com/api/git/repo?c=%s" % game_name
    try:
        f = urllib.urlopen(api_url)
        data = json.loads(f.read())
        f.close()
    except:
        return
    for block in data:
        if block['tag'] is None:
            block['tag'] = ''
        if Client.objects.filter(name=block['login']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['login'])
        if client.current_version != block['tag']:
            client.embargoed = False  # only place an embargo can be broken
            client.current_version = block['tag']
            client.save()


def makeClient(block):
    '''Make a client object from the provided API data block'''
    client = Client.objects.create()
    client.name = block['login']
    client.current_version = block['tag']
    client.repo = block['path']
    client.embargoed = True
    client.eligible = True  # tournament eligible
    client.seed = 0
    client.save()
    return client


main()

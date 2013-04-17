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
# import to try to fix the memory leak
import gc

# My Imports
import bootstrap
from thunderdome.config import game_name, req_queue_len
from thunderdome.models import Client
from thunderdome.sked import sked


def main():
    #stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    while True:
        try:
            stalk = beanstalkc.Connection()
            stalk.use(req_tube)
            stats = stalk.stats_tube(req_tube)
            if stats['current-jobs-ready'] < req_queue_len:
                update_clients()
                schedule_a_game(stalk)
            stalk.close()
    #to try to get rid or memory leak
            gc.collect()
        except:
            print "Arena scheduler could not schedule a game"
        time.sleep(1)


def schedule_a_game(stalk):
    '''Schedule the most needy client and a random partner for a game'''
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))
    if len(clients) < 2:  # takes two to tango
        print "only", len(clients), "clients in the arena"
        return
    worst_client = min(clients, key=lambda x: x.last_game())
    clients.remove(worst_client)
    partner = random.choice(clients)
    players = [worst_client, partner]
    random.shuffle(players)
    sked(players[0], players[1], stalk, "Arena Scheduler")
  #gc.collect is to try to get rid of memory leak
    gc.collect()


def update_clients():
    '''Import updated client info from Wisely's tastypie API'''
    api_url = "http://megaminerai.com/api/repo/tags/?competition=%s" % game_name
    try:
        f = urllib.urlopen(api_url)
        data = json.loads(f.read())
        f.close()
    except:
        return
    for block in data:
        if block['tag'] is None:
            block['tag'] = ''
        if Client.objects.filter(name=block['name']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['name'])
        if client.current_version != block['tag']:
            client.embargoed = False  # only place an embargo can be broken
            client.current_version = block['tag']
            client.save()


def makeClient(block):
    '''Make a client object from the provided API data block'''
    client = Client.objects.create()
    client.name = block['name']
    client.current_version = block['tag']
    client.repo = block['path']
    client.embargoed = True
    client.eligible = True  # tournament eligible
    client.seed = 0
    client.save()
    return client


if __name__ == "__main__":
    main()

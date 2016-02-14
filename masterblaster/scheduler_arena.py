#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import random
import urllib
import json
import time

import beanstalkc
import gc

from thunderdome.config import game_name, req_queue_len
from thunderdome.models import Client, ArenaConfig
from thunderdome.sked import sked

from utilities import webinteraction as wi

import threading
import time

import django
django.setup()

def t_clients():
    while True:
        print "Updating Clients"
        wi.update_clients()
        time.sleep(20)

def main():
    try:
        stalk = beanstalkc.Connection()
    except:
        raise Exception("Beanstalk Error: Possible that beanstalkd is not running, try running it from var/parts/beanstalkd")
    
    #client_updater = threading.Thread(target=t_clients)
    #client_updater.daemon = True
    #client_updater.start()
    req_tube = "game-requests-%s" % game_name
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    while True:
        #try:
        # wi.update_clients()
        stats = stalk.stats_tube(req_tube)
        if stats['current-jobs-ready'] < req_queue_len:
            print "schedule a game"
            schedule_a_game(stalk)
        time.sleep(1)
    stalk.close()

def schedule_a_game(stalk):
    '''Schedule the most needy client and a random partner for a game'''
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False).filter(missing=False))
    if len(clients) < 2: # takes two to tango
        print "only", len(clients), "clients in the arena"
        return

    worst_client = min(clients, key=lambda x: x.last_game())
    clients.remove(worst_client)
    partner = random.choice(clients)
    players = [worst_client, partner]
    random.shuffle(players)
    sked(players[0], players[1], stalk, "Arena Scheduler", ttr=300)

if __name__ == "__main__":
    main()

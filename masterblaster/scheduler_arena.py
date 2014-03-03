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
from thunderdome.models import Client
from thunderdome.sked import sked

from utilities import webinteraction as wi

def main():
    try:
        stalk = beanstalkc.Connection()
    except:
        raise Exception("Beanstalk Error: Possible that beanstalkd is not running, try running it from var/parts/beanstalkd")

    req_tube = "game-requests-%s" % game_name
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    while True:
        #try:
        stats = stalk.stats_tube(req_tube)
        if stats['current-jobs-ready'] < req_queue_len:
            wi.update_clients()
            schedule_a_game(stalk)
        #except:
        #    print "Arena scheduler could not schedule a game"
        time.sleep(1)
    stalk.close()

def schedule_a_game(stalk):
    '''Schedule the most needy client and a random partner for a game'''
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))
    if len(clients) < 2: # takes two to tango
        print "only", len(clients), "clients in the arena"
        return

    worst_client = min(clients, key=lambda x: x.last_game())
    clients.remove(worst_client)
    partner = random.choice(clients)
    players = [worst_client, partner]
    random.shuffle(players)
    sked(players[0], players[1], stalk, "Arena Scheduler")

if __name__ == "__main__":
    main()

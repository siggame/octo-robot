
import random
import urllib
import json
import time

# Non-Django 3rd Party Imports
import beanstalkc

import bootstrap
from thunderdome.config import game_name, req_queue_len
from thunderdome.models import Client
from thunderdome.sked import sked


def main():
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    while True:
        try:
            stalk = beanstalkc.Connection()
            stalk.use(req_tube)
            stats = stalk.stats_tube(req_tube)
            if stats['current-jobs-ready'] < req_queue_len:
                schedule_a_game(stalk)
            stalk.close()
        except:
            print "Arena scheduler could not schedule a game"
        time.sleep(1)


def schedule_a_game(stalk):
    '''Schedule the most needy client and a random partner for a game'''

    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))
    if len(clients) < 2:
        print "only", len(clients), "clients in the arena"
        return
    worst_client = min(clients, key=lambda x: x.last_game())
    clients.remove(worst_client)
    partner = random.choice(clients)
    players = [worst_client, partner]
    random.shuffle(players)
    sked(players[0], players[1], stalk, "Fake Arena Scheduler")


if __name__ == "__main__":
    main()

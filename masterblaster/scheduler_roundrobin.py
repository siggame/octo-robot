
from itertools import combinations
import beanstalkc

from thunderdome.config import game_name
from thunderdome.models import Client
from thunderdome.sked import sked
from utilities.webinteraction import update_clients

import time
import json

import django
django.setup()

def skedRoundRobin(group, numGames, stalk):
    result = list()
    for (guy, otherguy) in combinations(group, 2):
        for counter in range(numGames):
            if (counter % 2):
                g = sked(guy, otherguy, stalk, 'skedRoundRobin')
            else:
                g = sked(otherguy, guy, stalk, 'skedRoundRobin')
            result.append(g)
    return result

def validateResults(results):
    for i in results:
        if i.status == "Failed":
            print "Game ", i, "Failed"
            exit()
        elif i.status != "Complete":
            return False

def main():
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    update_clients()
    clients = list(Client.objects.filter(eligible=True).filter(embargoed=False).filter(missing=False))
    
    # remove humans
    for i in list(clients):
        if i.language == 'Human':
            clients.remove(i)

    results = skedRoundRobin(clients, 2, stalk)
    print "Number of clients: ", len(clients)
    print "Number of games: ", len(results)
    print "first game id", results[0].pk, "last game id", results[len(results)-1].pk
    temp = validateResults(results)
    while not temp:
        temp = validateResults(results)
        time.sleep(3)
    

if __name__ == "__main__":
    main()

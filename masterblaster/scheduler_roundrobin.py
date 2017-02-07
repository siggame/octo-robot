from itertools import combinations
import beanstalkc

from thunderdome.config import game_name
from thunderdome.models import Client, Game
from thunderdome.sked import sked
from utilities.webinteraction import update_clients

import time
import json

import django
django.setup()

results = list()

def skedRoundRobin(group, numGames, stalk):
    global results
    for (guy, otherguy) in combinations(group, 2):
        for counter in range(numGames):
            if (counter % 2):
                g = sked(guy, otherguy, stalk, 'Tournament')
            else:
                g = sked(otherguy, guy, stalk, 'Tournament')
            results.append(g)
    return

def validateResults(stalk):
    global results
    for i in results:
        game = Game.objects.get(pk=i.pk)
        i.status = game.status
        if i.status == "Failed":
            print "Game ", i, "Failed"
            game_clients = list(i.gamedata_set.all())
            g = sked(game_clients[0].client, game_clients[1].client, stalk, 'Tournament')
            results.append(g)
            results.remove(i)
            return False
        elif i.status != "Complete":
            return False    
    return True

def main():
    global results
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    #update_clients()
    clients = list(Client.objects.filter(eligible=True).filter(embargoed=False).filter(missing=False))
    
    # remove humans
    for i in list(clients):
        if i.language == 'Human':
            clients.remove(i)

    skedRoundRobin(clients, 2, stalk)
    print "Number of clients: ", len(clients)
    print "Number of games: ", len(results)
    print "first game id", results[0].pk, "last game id", results[len(results)-1].pk
    temp = validateResults(stalk)
    while not temp:
        temp = validateResults(stalk)
        time.sleep(3)
    

if __name__ == "__main__":
    main()


import random

import beanstalkc

from thunderdome.config import game_name
from thunderdome.models import Client
from thunderdome.sked import sked

def validateSched(stalk):
    print("Scheduling validation games")
    games = []
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    clients = list(Client.objects.filter(eligible=True))
    random.shuffle(clients)
    for client in clients:
        client.embargoed = False
        client.save()
    while len(clients) > 1:
        (c1, c2) = clients[:2]
        clients = clients[2:]
        games.append(sked(c1, c2, stalk, "Validating Scheduler"))
        games.append(sked(c2, c1, stalk, "Validating Scheduler"))

    if len(clients) == 1:
        lastguy = clients[0]
        clients = list(Client.objects.all())
        clients.remove(lastguy)
        otherguy = random.choice(clients)
        games.append(sked(lastguy, otherguy, stalk, "Validating Scheduler"))
        games.append(sked(otherguy, lastguy, stalk, "Validating Scheduler"))
    print "Total of %d games were scheduled" % len(games)
    return games

def main():
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    clients = list(Client.objects.filter(eligible=True))
    random.shuffle(clients)
    for client in clients:
        client.embargoed = False
        client.save()
    while len(clients) > 1:
        (c1, c2) = clients[:2]
        clients = clients[2:]
        sked(c1, c2, stalk, "Validating Scheduler")
        sked(c2, c1, stalk, "Validating Scheduler")

    if len(clients == 1):
        lastguy = clients[0]
        clients = list(Client.objects.all())
        clients.remove(lastguy)
        otherguy = random.choice(clients)
        sked(lastguy, otherguy, stalk, "Validating Scheduler")
        sked(otherguy, lastguy, stalk, "Validating Scheduler")

if __name__ == "__main__":
    main()

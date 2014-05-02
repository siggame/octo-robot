
import random
import json
import beanstalkc

import break_embargos

from thunderdome.config import game_name
from thunderdome.models import Client
from thunderdome.sked import sked
from masterblaster.utilities.webinteraction import update_clients


def validateSched(stalk):
    print "updating clients"
    update_clients()
    print "Breaking embargoes"
    break_embargos.break_embargos()
    print "Scheduling validation games"
    games = []
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    clients = list(Client.objects.filter(eligible=True))
    # remove humans
    for i in list(clients):
        stats = json.loads(i.stats)
        if stats['language'] == 'Human':
            clients.remove(i)
        try:
            if stats['missing']:
                clients.remove(i)
        except KeyError:
            pass

    random.shuffle(clients)
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
    validateSched(stalk)

if __name__ == "__main__":
    main()

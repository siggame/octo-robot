#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import random

# Non-Django 3rd Party Imports
import beanstalkc

# My Imports
import bootstrap
from thunderdome.config import game_name
from thunderdome.models import Client
from thunderdome.sked import sked


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

    if len(clients) == 1:
        lastguy = clients[0]
        clients = list(Client.objects.all())
        clients.remove(lastguy)
        otherguy = random.choice(clients)
        sked(lastguy, otherguy, stalk, "Validating Scheduler")
        sked(otherguy, lastguy, stalk, "Validating Scheduler")


if __name__ == "__main__":
    main()

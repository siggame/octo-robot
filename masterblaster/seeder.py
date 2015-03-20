#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

#import bootstrap
import random

# My Imports
from thunderdome.models import Client


def wins_in_range(c):
    return c.games_won.count()

def seed():
    for client in Client.objects.all():
        client.seed = -1
        client.save()

    clients = list(Client.objects.filter(embargoed=False).filter(missing=False))
    random.shuffle(clients)
    for (i, client) in enumerate(clients, 1):
        print i, client.name
        client.seed = i
        client.save()

def seed_tournament():
    print "Seeding Tournament"
    for client in Client.objects.all():
        client.seed = -1
        client.save()

    clients = list(Client.objects.filter(embargoed=False).filter(eligible=True).filter(missing=False))
    random.shuffle(clients)
    for (i, client) in enumerate(clients, 1):
        print i, client.name
        client.seed = i
        client.save()

if __name__ == "__main__":
    seed()

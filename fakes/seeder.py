#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import bootstrap
import json

# My Imports
from thunderdome.models import Client


def wins_in_range(c):
    return c.games_won.filter(pk__gte=94579).filter(pk__lte=97166).count()


def seed():
    result = dict()
    clients = list(Client.objects
                   .filter(eligible=True)
                   .filter(embargoed=False))
    clients.sort(reverse=True, key=wins_in_range)
    for (i, client) in enumerate(clients, 1):
        result[i] = client.name
    print json.dumps(result)

seed()

#!/usr/bin/env python
"""
Missouri S&T ACM SIG-Game Arena (Thunderdome)

A doodad to see how long it's been since a particular pairing played a game

@author: Matthew Nuckolls <mannr4@mst.edu>
"""

import bootstrap
from collections import defaultdict
from itertools import product
from django.db.models import Max

from thunderdome.models import Client, Game


def pairmax(p0, p1):
    a = Game.objects.filter(winner=p0, loser=p1).aggregate(Max('pk'))['pk__max']
    b = Game.objects.filter(winner=p1, loser=p0).aggregate(Max('pk'))['pk__max']
    return max(a, b)


def main():
    newest = Game.objects.aggregate(Max('pk'))['pk__max']
    cs = Client.objects.all()
    pairs = product(cs, cs)
    results = defaultdict(dict)
    for (p0, p1) in pairs:
        pm = pairmax(p0, p1)
        if pm is None:
          result = None
        else:
          result = newest - pm
        results[p0.name][p1.name] = result

    for key in results.keys():
        results[key] = sorted([(v,k) for (k,v) in results[key].items()])
        for item in results[key]:
          print key, item


if __name__ == "__main__":
    main()

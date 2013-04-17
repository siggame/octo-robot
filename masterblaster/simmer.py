#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import json

import bootstrap

# My Imports
from thunderdome.models import Game


def build_grid():
    grid = dict()
    for g in Game.objects.filter(pk__gte=98661).filter(pk__lte=108245):
        if g.winner is None:
            continue
        if g.winner.name not in grid:
            grid[g.winner.name] = dict()
        if g.loser.name not in grid[g.winner.name]:
            grid[g.winner.name][g.loser.name] = 0
        grid[g.winner.name][g.loser.name] += 1

    return grid


if __name__ == '__main__':
    print json.dumps(build_grid())

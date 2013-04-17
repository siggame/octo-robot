#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import json

import bootstrap

# My Imports
from thunderdome.models import Game


def build_grid():
    grid = dict()
    teams = set()
    for g in Game.objects.filter(pk__gte=98661):
        if g.winner is None or g.loser is None:
            continue
        teams.add(g.winner.name)
        teams.add(g.loser.name)
        if g.winner.name not in grid:
            grid[g.winner.name] = dict()
        if g.loser.name not in grid[g.winner.name]:
            grid[g.winner.name][g.loser.name] = 0
        grid[g.winner.name][g.loser.name] += 1
    for t in teams:
        if t not in grid:
            grid[t] = dict()
            for s in teams:
                grid[t][s] = 0
        else:
            for s in teams:
                if t != s and s not in grid[t]:
                    grid[t][s] = 0

    return grid


def normalize_grid(grid):
    result = dict()
    for winner in grid:
        result[winner] = dict()
        for loser in grid[winner]:
            result[winner][loser] = \
                float(grid[winner][loser]) / \
                (grid[winner][loser] + grid[loser][winner])
    return result


if __name__ == '__main__':
    print json.dumps(normalize_grid(build_grid()))

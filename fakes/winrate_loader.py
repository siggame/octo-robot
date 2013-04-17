#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import bootstrap
from collections import defaultdict

# My Imports
from thunderdome.models import Game, WinRatePrediction


def load_winrate(a, b, ratio):
    print a, b, ratio
    return  ### comment this out to actually run this bad boy
    wrpf = list(WinRatePrediction.objects.filter(winner=a).filter(loser=b))
    if len(wrpf) == 0:
        wrp = WinRatePrediction(winner=a, loser=b, prediction=ratio)
    else:
        wrp = wrpf[0]
        wrp.prediction = ratio
    wrp.save()


def main():
    grid = defaultdict(lambda: defaultdict(int))
    games = Game.objects.filter(status='Complete')
    for g in games:
        grid[g.winner][g.loser] += 1

    for (a, v) in grid.items():
        for (b, v) in v.items():
            ratio = float(grid[a][b]) / (grid[a][b] + grid[b][a])
            load_winrate(a, b, ratio)


if __name__ == "__main__":
    main()

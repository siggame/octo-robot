#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# System Imports
from collections import Counter

# My Imports
import bootstrap
from thunderdome.models import Game

games = Game.objects.filter(pk__gte=352079).filter(pk__lte=352709).filter(status='Complete')
#results = [(g.winner.name, g.loser.name) for g in games]
#histogram = Counter(results)
#for key, value in histogram.items():
#    print key, value

#p1wins = [g for g in games if g.winner == g.gamedata_set.all()[0].client]
#print len(p1wins), len(games)

#games = Game.objects.filter(status="Complete")
results = [(g.winner.name, g.loser.name, g.winner == g.gamedata_set.all()[0].client) for g in games]

histogram = Counter(results)

for key, value in histogram.items():
    print key, value

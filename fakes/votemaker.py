#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import bootstrap
import json

# My Imports
from thunderdome.models import Game


def votemake():
    result = list()
    g = Game.objects.get(pk=98566)
#    result.append(str(g.completed))
    games = Game.objects.filter(pk__gte=87212).filter(pk__lte=97166)
    for g in games:
        if g.status == "Complete":
            data = json.loads(g.stats)
#            winner = "%s %s" % (data['winner']['name'], data['winner']['tag'])
#            loser  = "%s %s" % (data['loser']['name'], data['loser']['tag'])
            winner = data['winner']['name']
            loser = data['loser']['name']
            result.append([winner, loser])
    print json.dumps(result)


if __name__ == "__main__":
    votemake()

#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import bootstrap
import json

# My Imports
from thunderdome.models import Game

def glogdump():
    games = Game.objects.filter(pk__gte=87212).filter(pk__lte=97166)
    for g in games:
        if g.status == "Complete":
            data = json.loads(g.stats)
            print data['gamelog_url']


if __name__ == "__main__":
    glogdump()

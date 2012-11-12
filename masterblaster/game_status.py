#!/usr/bin/env python

import bootstrap
import sys

# My Imports
from thunderdome.models import Game

g = Game.objects.get(pk=sys.argv[-1])
print 'Status', g.status
print 'P1', g.gamedata_set.all()[0]
print 'P2', g.gamedata_set.all()[1]
print 'Winner', g.winner
print 'Loser', g.loser

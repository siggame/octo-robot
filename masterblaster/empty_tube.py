#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import bootstrap
from thunderdome.config import game_name

tube = 'game-requests-' + game_name

import beanstalkc
c = beanstalkc.Connection()
c.watch(tube)
while c.stats_tube(tube)['current-jobs-ready'] > 0:
  j = c.reserve()
  j.delete()

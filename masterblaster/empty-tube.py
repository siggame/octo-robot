from config import game_name

import beanstalkc
c = beanstalkc.Connection()
c.watch('game-requests-%s' % game_name)
while c.stats_tube('game-requests-%s' % game_name)['current-jobs-ready'] > 0:
  j = c.reserve()
  j.delete()


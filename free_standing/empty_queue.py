#!/usr/bin/env python

import beanstalkc
stalk = beanstalkc.Connection()
stalk.watch('game-requests')
while stalk.stats_tube('game-requests')['current-jobs-ready'] > 0:
    job = stalk.reserve()
    job.delete()

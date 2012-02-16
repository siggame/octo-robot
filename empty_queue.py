#!/usr/bin/env python
"""
Missouri S&T ACM SIG-Game Arena (Thunderdome)

Dumps out all the jobs in the beanstalk queue

@author: Matthew Nuckolls <mannr4@mst.edu>
"""

import beanstalkc
stalk = beanstalkc.Connection()
stalk.watch('game-requests')
while stalk.stats_tube('game-requests')['current-jobs-ready'] > 0:
    job = stalk.reserve()
    job.delete()

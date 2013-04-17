#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import random

# Non-Django 3rd Party Imports
import beanstalkc

# My Imports
import bootstrap
from thunderdome.config import game_name
from thunderdome.models import Client
from thunderdome.sked import sked


def main():
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    ubs = Client.objects.get(name="unbendable-steel-clouds")
    men = Client.objects.get(name="men-of-war")
    bal = Client.objects.get(name="balls-deep")

    c1, c2 = ubs, men
    for i in xrange(100):
        sked(c1, c2, stalk, "Dueling Scheduler")
        sked(c2, c1, stalk, "Dueling Scheduler")

    c1, c2 = men, bal
    for i in xrange(100):
        sked(c1, c2, stalk, "Dueling Scheduler")
        sked(c2, c1, stalk, "Dueling Scheduler")

    c1, c2 = bal, ubs
    for i in xrange(100):
        sked(c1, c2, stalk, "Dueling Scheduler")
        sked(c2, c1, stalk, "Dueling Scheduler")



if __name__ == "__main__":
    main()

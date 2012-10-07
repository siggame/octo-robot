#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
from itertools import combinations

# Non-Django 3rd Party Imports
import beanstalkc

# My Imports
from thunderdome.models import Client
from config import game_name
from sked import sked


def main():
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    clients = Client.objects.filter(eligible=True)
    for (guy, otherguy) in combinations(clients, 2):
        sked(guy, otherguy, stalk, "Round Robin Scheduler")
        sked(otherguy, guy, stalk, "Round Robin Scheduler")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####


# Standard Imports
import time
import urllib
import math
import gzip
import os
import urllib2
from copy import copy
from multiprocessing import Process
from datetime import datetime, timedelta
from bz2 import BZ2Decompressor
from collections import defaultdict

# Non-Django 3rd Party Imports
import beanstalkc
import json

# My Imports
from thunderdome.config import game_name
from thunderdome.models import Client, Game, GameData, Referee

def main():
    while True:
        for x in Game.objects.filter(been_vised=False):
            try:
                if x.completed < datetime.now() - timedelta(hours=1):
                    x.been_vised = True
                    x.save()
                    print "Game", x, "is too old, no longer showing on games page."
            except:
                continue
    return

if __name__ == "__main__":
    main()

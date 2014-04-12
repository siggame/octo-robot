#!/user/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
from time import sleep
from multiprocessing import Process
from datetime import datetime, timedelta
import urllib

# Non-Django 3rd Party Imports
import beanstalkc

from thunderdome.models import Game

dum_url = 'http://arena.megaminerai.com/mies/thunderdome/get_next_game_url_to_viualize_and_mark'

pool_size = 10

def get_pool(pool_size):
   latest_game = Game.objects.filter(status="Complete").latest('completed')
   watcher_id = latest_game.pk - pool_size
   upper_limit = latest_game.pk
   pool = Game.objects.filter(pk__get=watcher_id).filter(pk__lte=upper_limit)
   return pool

def check_pool(pool, watcher_id):
    # watcher_id is the starting pk for the pool
    # should be the smallest pk in the pool
    if len(pool) < 10:
        pool = Game.objects.filter(pk__gte=watcher_id)
    
    if len(pool) >= 10:
        return True
    elif len(pool) < 10:
        return False

def update_pool(pool):
    if len(pool) < pool_size:
        max_pk = 0
        for i in pool:
            if max_pk < i.pk:
                max_pk = i.pk
        new_pool = Game.objects.filter(pk__gt=max_pk)
        new_pool.reverse()
        while len(pool) < pool_size:
            pool.append(new_pool.pop())

def showit(stalk):
    f = urllib.urlopen(dumb_url)
    url = f.read()
    f.close()
    stalk.put(url)
    print url

def main():
    stalk = beanstalkc.Connection()
    stalk.use('visualizer-requests')
    if 'visualizer-requests' not in stalk.tubes():
        showit(stalk)
    while True:
        if stalk.stats_tube('visualizers-requests')['current-jobs-ready'] < 1:
            showit(stalk)
        sleep(1)

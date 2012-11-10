#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
from time import sleep
import urllib

# Non-Django 3rd Party Imports
import beanstalkc

dumb_url = 'http://space.arena.megaminerai.com/mies/thunderdome/get_next_game_url_to_visualize_and_mark'


def showit(stalk):
    with urllib.urlopen(dumb_url) as f:
        url = f.read()
    stalk.put(url)
    print url


def main():
    stalk = beanstalkc.Connection()
    stalk.use('visualizer-requests')

    if 'visualizer-requests' not in stalk.tubes():
        showit(stalk)
    while True:
        if stalk.stats_tube('visualizer-requests')['current-jobs-ready'] < 1:
            showit(stalk)
        sleep(1)

main()

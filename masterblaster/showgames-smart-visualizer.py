#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# jesus this needs some love
# FIXME
# FIXME
# FIXME
# FIXME
# FIXME
# FIXME

from time import sleep
import beanstalkc
import urllib

dumb_url = 'http://space.arena.megaminerai.com/mies/thunderdome/get_next_game_url_to_visualize_and_mark'

def main():
    stalk = beanstalkc.Connection()
    stalk.use('visualizer-requests')
    
    def showit(): 
        f = urllib.urlopen(dumb_url)
        url = f.read()
        f.close()
        stalk.put(url)
        print url
           
    if 'visualizer-requests' not in stalk.tubes():
        showit()
    while True:
        if stalk.stats_tube('visualizer-requests')['current-jobs-ready'] < 1:
            showit()
        sleep(1)

main()

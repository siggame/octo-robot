#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

from time import sleep
import beanstalkc
import urllib

def main():
    stalk = beanstalkc.Connection()
    stalk.use('visualizer-requests')
    if 'visualizer-requests' not in stalk.tubes():
        pass
    while True:
        if stalk.stats_tube('visualizer-requests')['current-jobs-ready'] < 1:
            f = urllib.urlopen('http://r09mannr4.device.mst.edu:8080/uard/thunderdome/get_next_game_url_to_visualize_and_mark')
            url = f.read()
            f.close()
            stalk.put(url)
            print url
        sleep(1)

main()

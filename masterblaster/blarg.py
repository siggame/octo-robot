#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports

# Non-Django 3rd Party Imports
import beanstalkc


def showTest(stalk):
    stalk.put("https://s3.amazonaws.com/siggame-glog-megaminerai-11-reef/1.gamelog")
    print "test glog loaded", "https://s3.amazonaws.com/siggame-glog-megaminerai-11-reef/1.gamelog"
    return


def main():
    stalk = beanstalkc.Connection()
    stalk.use('visualizer-requests')
    showTest(stalk)
    exit()

main()

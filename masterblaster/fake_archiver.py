#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# doesn't actually touch the database. testing if maybe the django
# connection is what is leaking

# Standard Imports

# Non-Django 3rd Party Imports
import beanstalkc as beanstalkc_test
import json

# My Imports
from config import game_name
from thunderdome.loggly_logging import log


def main():
    result_tube = "game-results-%s" % game_name

    while True:
        #stalk = beanstalkc_test.Connection()
        stalk = beanstalkc.Connection()
        stalk.watch(result_tube)
        job = stalk.reserve()
        request = json.loads(job.body)
        job.delete()
        print "Game", request['number'], "status", request['status']
        request.update({'reporter': 'archiver'})
        log.info(json.dumps(request))
        del job.conn
        del job
        del request
        stalk.close()


main()

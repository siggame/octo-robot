#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# doesn't actually touch the database. testing if maybe the django
# connection is what is leaking

# Standard Imports

# Non-Django 3rd Party Imports
import beanstalkc
import json

# My Imports
import bootstrap
from thunderdome.config import game_name
from thunderdome.models import Game
from thunderdome.loggly_logging import log


def main():
    result_tube = "game-results-%s" % game_name

    while True:
        stalk = beanstalkc.Connection()
        stalk.watch(result_tube)
        job = stalk.reserve()
        request = json.loads(job.body)
        request['Fake game'] = True
        try:
            game = Game.objects.get(id=int(request['number']))
        except:
            job.delete()
            continue
        game.stats = job.body
        game.status = request['status']
        print "Game", request['number'], "status", request['status']
        request.update({'reporter': 'archiver'})
        #log.info(json.dumps(request))
        game.save()
        job.delete()
        del job.conn
        del job
        del request
        stalk.close()

if __name__ == "__main__":
    main()

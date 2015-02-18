import re
import json
import subprocess
import os
import signal
import random
import socket
import md5
import zipfile
from time import sleep
from datetime import datetime
from bz2 import BZ2File
import beanstalkc
from pprint import pprint

from thunderdome.config import game_name, beanstalk_host

def main():
    # stalk = beanstalkc.Connection(host=os.environ['BEANSTALK_HOST'])
    # stalk.watch('game-requests-%s' % os.environ['GAME_NAME']) # input
    # stalk.use('game-results-%s' % os.environ['GAME_NAME']) # output
    stalk = beanstalkc.Connection(host=beanstalk_host)
    stalk.watch('game-requests-%s' % game_name)
    stalk.use('game-results-%s' % game_name)

    while True:
        looping(stalk)


def looping(stalk):
    job = stalk.reserve()
    game = json.loads(job.body)

    print "processing game", game['number']

    game['blaster_id'] = socket.gethostname()
    game['referee_id'] = os.getpid()
    game['started'] = str(datetime.now())

    game['status'] = "Building"
    stalk.put(json.dumps(game))
    job.touch()

    for client in game['clients']:
        client['compiled'] = True
        job.touch()
        print "result for make in %s was %s" % (client['name'],
                                                client['compiled'])

    if not all(x['compiled'] for x in game['clients']):
        print "failing the game, someone didn't compile"
        game['status'] = "Failed"
        game['completed'] = str(datetime.now())
        stalk.put(json.dumps(game))
        job.delete()
        return

    print "running...", game['number']
    game['status'] = "Running"
    stalk.put(json.dumps(game))
    sleep_amount = random.random() * 1
    print "Sleep amount", sleep_amount
    while sleep_amount > 0:
        sleep(1)
        job.touch()
        sleep_amount -= 1

    print "determining winner..."
    winner = random.randint(0, 1)
    if winner == 2:
        game['tied'] = True
        print game['clients'][0]['name'], "and", \
            game['clients'][1]['name'], "tied!"
    else:
        if winner == 0:
            game['winner'] = game['clients'][0]
            game['loser'] = game['clients'][1]
        elif winner == 1:
            game['winner'] = game['clients'][1]
            game['loser'] = game['clients'][1]
        print game['winner']['name'], "beat", game['loser']['name']

    # clean up
    game['status'] = "Complete"
    game['completed'] = str(datetime.now())
    game['gamelog_url'] = 'wakka'
    pprint(game)
    stalk.put(json.dumps(game))
    job.delete()
    print "%s done %s" % (game['number'], str(datetime.now()))

if __name__ == "__main__":
    main()

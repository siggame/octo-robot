from thunderdome.models import Game
from thunderdome.config import game_name
from empty_tube import empty_tube
import beanstalkc
import time


def main():

    empty_tube()

    p = dict()
    c = beanstalkc.Connection()

    while True:
        c.use('game-requests-%s' % game_name)
        tube_status = c.stats_tube('game-requests-%s' % game_name)
        (p['ready_requests'], p['running_requests'], p['current_tube']) = \
            [tube_status[x] for x in ('current-jobs-ready',
                                      'current-jobs-reserved',
                                      'name')]
        print "Waiting for gladiators to finish"
        time.sleep(1)
        if p['running_requests'] == 0:
            break
    c.close()


    for x in Game.objects.all():
        if x.status == 'Complete' or x.status == 'Failed':
            pass
        else:
            x.status = 'Failed'
            x.save()

if __name__ == "__main__":
    main()

import beanstalkc
from thunderdome.config import game_name
from thunderdome.models import Client
from thunderdome.sked import sked

from utilities import webinteraction as wi
import json
import random
import time

def main():
    try:
        stalk = beanstalkc.Connection()
    except:
        raise Exception("Beanstalk error")
    wi.update_clients()
    req_tube = "game-requests-%s" % game_name    
    stalk.use(req_tube)
    while True:
        stats = stalk.stats_tube(req_tube)
        if stats['current-jobs-ready'] < 5:
            schedule_a_game(stalk)
        time.sleep(3)
    stalk.close()
    

def schedule_a_game(stalk):
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))
    
    if len(clients) < 2:
        return
    
    h = [i for i in clients if json.loads(i.stats)['language'] == 'Human']
    k = h.pop()
    while k.name != 'fortheswarm':
        k = h.pop()
    partner = random.choice(clients)
    sked(k, partner, stalk, "human test")

if __name__ == "__main__":
    main()

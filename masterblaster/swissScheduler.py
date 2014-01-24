import random
import urllib
import json
import time
import pprint

import beanstalkc
import gc

from thunderdome.config import game_name, req_queue_len
from thunderdome.models import Client, Game

from thunderdome.sked import sked

import scheduler_validating as SV

from collections import defaultdict

swiss_scores = {}
uncompleted_games = []
competing_clients = []
current_round = 0

def main():
    try:
        stalk = beanstalkc.Connection()
    except:
        raise Exception("Beanstalk error:")
    
    req_tube = "game-requests-%s" % game_name
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    while True:
        stats = stalk.stats_tube(req_tube)
        if not uncompleted_games:
            schedule_volley(stalk, current_round)
        else:
            score_games()
        time.sleep(5)
    stalk.close()           
    
def game_status(g_id):
    return Game.objects.get(pk=g_id).status

def schedule_volley(stalk, sRound):
    global current_round
    global competing_clients
    global uncompleted_games
    print("current round %d" % sRound)
    if sRound == 0:
        update_clients()
        #uncompleted_games.extend([i.pk for i in SV.validateSched(stalk)])
        while uncompleted_games:
            for c in list(uncompleted_games):
                if game_status(c) in ["Complete", "Failed"]:
                    uncompleted_games.remove(c)
            print("games to go: %d" % len(uncompleted_games))
            time.sleep(2)
        competing_clients = [j.name for j in list(Client.objects.exclude(name='bye').filter(embargoed=False))]
        print(len(competing_clients))
        if len(competing_clients) % 2 != 0:
            competing_clients.pop(random.randint(0, len(competing_clients) - 1))
    if len(competing_clients) < 2:
        print "only", len(competing_clients)
        return
    if sRound == 0:
        for c in competing_clients:
            swiss_scores[c] = 0
        # random pairs
        temp_c = list(competing_clients)
        while len(temp_c) > 2:
            c1 = Client.objects.get(name=temp_c.pop(random.randint(0, len(temp_c)-1)))
            c2 = Client.objects.get(name=temp_c.pop(random.randint(0, len(temp_c)-1)))
            uncompleted_games.append(sked(c1, c2, stalk, "Swiss sked").pk)
    else:        
        print("Forming groups")
        groupes = formGroups()
        print(groupes)
        while groupes:
            m_group = max(groupes.keys())
            goupin = groupes[m_group]
            pprint.pprint(goupin)
            del groupes[m_group]
            if len(goupin) % 2 != 0:
                temp_m = max(groupes.keys())
                groupes[temp_m].append(goupin.pop(random.randint(0, len(goupin)-1)))
            while len(goupin) >= 2:
                goupin.sort(key=lambda x: scores[x])
                c1 = Client.objects.get(name=goupin.pop(0))
                c2 = Client.objects.get(name=goupin.pop(0))
                uncompleted_games.append(sked(c1, c2, stalk, "Swiss sked").pk)
                time.sleep(1)
    current_round += 1
        
def score_games():
    print "Current swiss scores"
    pprint.pprint(swiss_scores)
    pprint.pprint(uncompleted_games)
    for g in list(uncompleted_games):
        if game_status(g) == "Complete":
            uncompleted_games.remove(g)
            swiss_scores[Game.objects.get(pk=g).winner.name] += 1
        elif game_status(g) == "Failed":
            print "Game: ", g, "Failed aborting automated swiss, switch to manual swiss."
            print "Printing out standing"
            f = open("scores.txt", 'w')
            
            f.close()
    
def formGroups():
    groups = defaultdict(list)
    for i, j in swiss_scores.items():
        groups[j].append(i)
    return groups
            
def update_clients():
    print 'updating clients'
    api_url = "http://megaminerai.com/api/repo/tags/?competition=%s" % game_name
    try:
        f = urllib.urlopen(api_url)
        data = json.loads(f.read())
        f.close()
    except:
        print "couldn't read updated clients is website up? is the right api_url: %s" % api_url

    for block in data:
        if block['tag'] is None:
            block['tag'] = ''
        if Client.objects.filter(name=block['name']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['name'])
        if client.current_version != block['tag']:
            client.embargoed = False # only place an embargo can be broken
            client.current_version = block['tag']
            client.save()


def makeClient(block):
    '''Make a client object from the provided API data block'''
    client = Client.objects.create()
    client.name = block['name']
    client.current_version = block['tag']
    client.repo = block['path']
    client.embargoed = False # True # odd so the first client obtained from the api is embargoed?
    client.eligible = True # tournament eligible
    client.seed = 0
    client.save()
    return client


if __name__ == "__main__":
    main()


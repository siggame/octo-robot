#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
##### Swiss Schedular

#goal, swiss schedular

#for every match
    #inilize everyones score to zero
    
    #need to loop every round
        #find the comps current score
        #generate who plays who
        #put all games into beanstalk
        #wait until beanstalk is empty
        #find results of that round
        #update scores
        
        #score = number of wins
        #rest round when score = number of clients/2
        
# Standard Imports
import random
import urllib
import json
import time
import math
from collections import defaultdict

# Non-Django 3rd Party Imports
import beanstalkc
# import to try to fix the memory leak
import gc

# My Imports
import bootstrap
from thunderdome.config import game_name
from thunderdome.models import Client , Game
from thunderdome.sked import sked

rounds = 1
match = 1


def main():
    global rounds, match
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    stop = False
    client_dict = defaultdict(int)  #key is client name, value is score
    while not stop:
        try:
            stats = stalk.stats_tube(req_tube)
            #check if we need to schedual another round
            if stats['current-jobs-ready'] <= 0:
                update_clients()
                #schedule the next round
                print "Scheduling a Round"
                schedule_a_round(stalk, client_dict)
                print "Scheduling round over"
                rounds += 1
        except:
            print "Arena scheduler could not schedule a game"
        time.sleep(1)
    stalk.close()


def schedule_a_round(stalk, scores):
    global rounds, match
    '''Schedule the games for the next round'''
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))
    #make sure each client has a entry in scores
    #scores is default dict always returns 0 if key is not found
    for player in clients:
        if player.name not in scores.keys():
            scores[player.name] = 0

    print "Scores has been built"

    #check if new match needs to be played
    for rank in scores.values():
        if rank[1] > (math.log(2, len(clients)) / 2 + 2):
            match += 1
            rounds = 1
            # should clear out clients, and their scores?
            return

    print "Updating Scores"
    #search old games for all games in round -1
    origin_msg = "Arena Scheduler-Swiss: Match %d Round %d" % (match, rounds - 1)
    games = list(Game.objects.all())
    gamesLastRound = []
    for currentGame in games:
        #unpack stats
        stats = json.loads(currentGame.stats)
        #seach stats for all games last round
        if stats['origin'] is origin_msg:
            gamesLastRound.append(currentGame)

    #modify client's score by who won last round, no clear win, no points
    for gamePlayed in gamesLastRound:
        if gamePlayed.winner.name in scores.keys():
            scores[gamePlayed.winner.name] = scores[gamePlayed.winner.name] + 1

    print "Scores have been updated"
    #sort clients by score
    sorted_scores = sorted([(name, score) for name, score in scores.iteritems],
                           key = lambda x: x[1], reverse=True)

    #loop through and have top to play each other
    origin = "Arena Scheduler-Swiss: Match " + match + " Round " + rounds
    while len(sorted_scores) >= 2:
        p1 = sorted_scores.pop(0)
        p2 = sorted_scores.pop(0)
        sked(Client.objects.get(name=p1[0]),
             Client.objects.get(name=p2[0]), stalk, origin)

    #last guy auto wins
    if sorted_scores:
        p0 = sorted_scores.pop()
        scores[p0[0]] = scores[p0[0]] + 1


def update_clients():
    '''Import updated client info from Wisely's tastypie API'''
    print 'updating clients'
    api_url = "http://megaminerai.com/api/repo/tags/?competition=%s" % game_name
    try:
        f = urllib.urlopen(api_url)
        data = json.loads(f.read())
        f.close()
    except:
        return
    for block in data:
        if block['tag'] is None:
            block['tag'] = ''
        if Client.objects.filter(name=block['name']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['name'])
        if client.current_version != block['tag']:
            client.embargoed = False  # only place an embargo can be broken
            client.current_version = block['tag']
            client.save()


def makeClient(block):
    '''Make a client object from the provided API data block'''
    client = Client.objects.create()
    client.name = block['name']
    client.current_version = block['tag']
    client.repo = block['path']
    client.embargoed = True
    client.eligible = True  # tournament eligible
    client.seed = 0
    client.save()
    return client


if __name__ == "__main__":
    main()

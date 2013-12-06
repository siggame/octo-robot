import time
import math
import os
import urllib2
from multiprocessing import Process
from datetime import datetime, timedelta
from bz2 import BZ2Decompressor

import beanstalkc
import json

from thunderdome.config import game_name
from thunderdome.models import Client, Game, GameData, Referee

import settings

stalk = None
tourny_time = False

def main():
    result_tube = "game-results-%s" % game_name
    global stalk
    stalk = beanstalkc.Connection()
    stalk.watch(result_tube)
    
    while True:
        job = stalk.reserve()
        request = json.loads(job.body)
        
        try:
            game = Game.objects.get(id=int(request['number']))
        except:
            job.delete()
            continue
        
        game.stats = job.body
        game.status = request['status']
        if game.status in ["Complete", "Failed"]:
            if 'gamelog_url' in request:
                game.gamelog_url = request['gamelog_url']
            if 'completed' in request:
                game.completed = request['completed']
            handle_completion(request, game)
        game.save()
        job.delete()
        del job.conn
        del job
        
        print "Game", request['number'], "status", request['status']
    
def handle_completion(request, game):
    if 'winner' in request:
        game.winner = Client.objects.get(name=request['winner']['name'])
        game.winner.score += 1.0
    if 'loser' in request:
        game.loser = Client.objects.get(name=request['loser']['name'])
        
        
    if 'winner' in request and 'loser' in request:
        pass
    
    clidict = dict()
    for client in request['clients']:
        clidict[client['name']] = client
    for gd in GameData.objects.filter(game=game):
        if gd.client == game.winner:
            gd.won = True
        gd.compiled = clidict[gd.client.name]['compiled']
        gd.version = clidict[gd.client.name]['tag']
        if not gd.compiled or 'broken' in clidict[gd.client.name]:
            gd.client.embargoed = True
        try:
            gd.output_url = clidict[gd.client.name]['output_url']
        except KeyError:
            print "Key error"
        if 'tied' in request:
            gd.client.score += 0.5
        gd.client.save()
        gd.save()
        
        
if __name__ == "__main__":
    main()

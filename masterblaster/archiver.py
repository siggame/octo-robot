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

from gviz_api import DataTable

import settings.defaults as settings

stalk = None
tourny_time = False

def main():
    global stalk
    result_tube = "game-results-%s" % game_name
    
    #p = Process(target=processing)
    #p.start()
    
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
    
def processing():
    while True:
        start = datetime.now()
        compute_throughput()
        compute_scoreboard()
        td = datetime.now()-start
        delay = max(td*2, timedelta(seconds=30)).total_seconds()
        print "Next run in %s secs" % delay
        time.sleep(delay)
        
def compute_throughput():
    refs = Referee.objects.all().order_by('pk')
    if refs.count() == 0:
        return
    out = dict()
    formatted = dict()
    earliest_start = min([ref.started for ref in refs])
        
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

#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

game_name = 'chess-2012'
queue_len = 1

# Some magic to get a standalone python program hooked in to django
import sys
sys.path = ['/srv/uard', '/srv'] + sys.path

from django.core.management import setup_environ
import settings

setup_environ(settings)

# Non-Django 3rd Party Imports
import beanstalkc
import json

# My Imports
from thunderdome.models import Client, Game, GameData

stalk = None

def main():
    result_tube = "game-results-%s" % game_name
    
    global stalk
    stalk = beanstalkc.Connection()
    stalk.watch(result_tube)
    while True:
        job = stalk.reserve()
        request = json.loads(job.body)
        game = Game.objects.get(id=int(request['number']))
        
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
        print "Game", request['number'], "status", request['status']
        

def handle_completion(request, game):
    if 'winner' in request:
        game.winner = Client.objects.get(name=request['winner']['name'])
        game.winner.score += 1.0
    if 'loser' in request:
        game.loser  = Client.objects.get(name=request['loser']['name'])
    
    clidict = dict()
    for client in request['clients']:
        clidict[client['name']] = client
    for gd in GameData.objects.filter(game=game):
        gd.compiled = clidict[gd.client.name]['compiled']
        if not gd.compiled or 'broken' in clidict[gd.client.name]:
            gd.client.embargoed = True
        gd.output_url = clidict[gd.client.name]['output_url']
        if 'tied' in request:
            gd.client.score += 0.5
        gd.client.save()
        gd.save()


main()

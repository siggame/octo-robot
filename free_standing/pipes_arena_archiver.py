#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

game_name = 'chess-2012'
queue_len = 1

# Some magic to get a standalone python program hooked in to django
import sys
sys.path = ['/srv/uard', '/srv'] + sys.path

import bootstrap

# Non-Django 3rd Party Imports
import beanstalkc
import json

# My Imports
from thunderdome.models import Client, Game, GameData, Referee
from datetime import datetime,timedelta
from gviz_api import DataTable
from django.core.cache import cache

stalk = None

def main():
    result_tube = "game-results-%s" % game_name
    next_run = processing()  

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
            #Recompute the scoreboard and throughput
            if datetime.today() > next_run:
                next_run = processing()
            handle_completion(request, game)
        game.save()
        job.delete()
        (r,c) = Referee.objects.get_or_create(blaster_id=request['blaster_id'],referee_id=request['referee_id'])
        r.games.add(game)
        r.save()
        print "Game", request['number'], "status", request['status']
        
def processing():
    start = datetime.today()
    compute_throughput()
    compute_scoreboard()
    td = datetime.today()-start
    return max(td*2,timedelta(seconds=30))+datetime.today()

def compute_throughput():
    refs = Referee.objects.all().order_by('pk')
    if refs.count() == 0:
        return
    out = dict()
    formatted = dict()
    earliest_start = min([ref.started for ref in refs])
    period = datetime.today()-earliest_start
    step = timedelta(minutes=10)
    interval = timedelta(minutes=30)
    for ref in refs:
        table = ref.rate_table(period, step, interval)
        v0 = None
        for (t,v) in table:
            t = t.replace(second=0,microsecond=0)
            try:
                formatted[t].append(v)
            except KeyError:
                formatted[t] = [v]
    struct =[ [k]+v for (k,v) in sorted(formatted.iteritems()) ]
    desc =  [('Time','datetime')]
    desc += [('%s/%s' % (ref.blaster_id,ref.referee_id),'number') for ref in refs]
    dt = DataTable(desc,struct)
    cache.set('throughput_chart',dt.ToJSCode('data'))
    print "Throughput chart computed!"

def compute_scoreboard():
    clients = Client.objects.exclude(current_version="")
    # Build the speedy lookup table
    grid = dict()    
    for c1 in clients:
        grid[c1] = dict()
        for c2 in clients:
            grid[c1][c2] = 0

    for c1 in clients:
        for c2 in clients:
            grid[c1][c2] = c1.games_won.filter(loser=c2).count()
                
    # Sort the clients by winningness
    clients = list(clients)
    clients.sort(reverse=True, key = lambda x: x.fitness())

    client_link = "<a href='view_client/%s'>%s</a>"

    desc = [('vs','string')]
    desc += [('embargoed','boolean')]
    desc += [(client_link % (client.pk,client.name), 'string') for client in clients]
    
    struct = []

    for client1 in clients:
        tmp = [client_link % (client1.pk, client1.name), client1.embargoed]
        for client2 in clients:
            link = "<a href='matchup/%svs%s'>%s</a>" % (client1.pk,client2.pk,grid[client1][client2])
            tmp.append(link)
        struct.append(tmp)
    dt = DataTable(desc,struct)
    cache.set('scoreboard_chart',dt.ToJSCode('data'))
    print "Scoreboard Computed!"
    pass

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
        if gd.client == game.winner:
            gd.won = True
        gd.compiled = clidict[gd.client.name]['compiled']
        if not gd.compiled or 'broken' in clidict[gd.client.name]:
            gd.client.embargoed = True
        try:
            gd.output_url = clidict[gd.client.name]['output_url']
        except KeyError:
            pass
        if 'tied' in request:
            gd.client.score += 0.5
        gd.client.save()
        gd.save()


main()

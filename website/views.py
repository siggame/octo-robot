####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
####

# Non-Django 3rd Party Imports
import beanstalkc
import boto
import re
import os

# Django Imports
import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.db.models import Max

# My Imports
from thunderdome.models import Game, Client, GameData, InjectedGameForm, Match, Referee
from datetime import datetime


def matchup_odds(client1, client2):
    # manual join. fix this if you know how
    c1games = set(client1.games_played.all())
    c2games = set(client2.games_played.all())    
    shared_games = list(c1games & c2games)
    c1wins = len([x for x in shared_games if x.winner == client1])
    c2wins = len([x for x in shared_games if x.winner == client2])
    return c1wins, c2wins


import json
def bet_list(request):
    # a list of all scheduled games
    games = Game.objects.filter(status="Scheduled")    
    payload = list()
    for g in games:
        clients = list(g.clients.all())
        c0w, c1w = matchup_odds( clients[0], clients[1] )
        
        total = float(max( [c0w + c1w, 1] ))
        odds0 = total / c0w if c0w != 0 else total
        odds1 = total / c1w if c1w != 0 else total
        
        payload.append({'gameID'   : g.pk,
                        'clientID' : clients[0].name,
                        'odds'     : odds0 })
        payload.append({'gameID'   : g.pk,
                        'clientID' : clients[1].name,
                        'odds'     : odds1 })
            
    return HttpResponse(json.dumps(payload))


def health(request):
    # Let's start by having this page show some arena health statistics
    p = dict() # payload for the render_to_response

    c = beanstalkc.Connection()
    c.use('game-requests-megaminerai-9-space')
    tube_status = c.stats_tube('game-requests-megaminerai-9-space')
    (p['ready_requests'], p['running_requests']) = \
        [tube_status[x] for x in ('current-jobs-ready',
                                  'current-jobs-reserved')]
    c.close()

    (p['scheduled_games'], p['running_games'], 
     p['complete_games'], p['failed_games'], p['building_games']) = \
         [Game.objects.filter(status = x).count 
          for x in ('Scheduled', 'Running', 'Complete', 'Failed', 'Building')]

    p['sanity'] = p['ready_requests']  == p['scheduled_games'] \
              and p['running_games'] == p['running_requests']
    
    p['matches'] = list(Match.objects.order_by('-id'))
    p['matches'].sort(key=lambda x: x.status, reverse=True)
    
    p['last'] = Game.objects.all().aggregate(Max('completed'))['completed__max']
    # Compute the overall node throughput
    refs = Referee.objects.all().order_by('-pk')
    p['refs'] = refs
    return render_to_response('thunderdome/health.html', p)


def throughput_chart(request):
    out = dict()
    try:
        path = os.path.join(settings.STATIC_ROOT,'throughput.js')
        print path
        f = open(path)
        out['chart'] = f.read()
        f.close()
    except IOError:
        print "Couldn't open throughput"
        out['chart'] = ""
    return render_to_response('thunderdome/throughput_chart.html',out)


@login_required
def scoreboard_chart(request):
    out = dict()
    try:
        f = open(os.path.join(settings.STATIC_ROOT,'scoreboard.js'))
        out['chart'] = f.read()
        f.close()
    except IOError:
        print "Couldn't open scoreboard"
        out['chart'] = ""
    return render_to_response('thunderdome/scoreboard_chart.html',out)


@login_required
def inject(request):
    ### Handle manual injection of a game into the system
    if request.method == 'POST':
        form = InjectedGameForm(request.POST)
        if form.is_valid():
			
			# FIXME use code in arena scheduler for guidance
            game = Game.objects.create(priority=form.cleaned_data['priority'])
            for client in Client.objects.filter(pk__in = \
                                                form.cleaned_data['clients']):
                GameData(game=game, client=client).save()
            game.tournament = True
            game.schedule()
            payload = {'game': game}
            payload.update(csrf(request))
            return HttpResponseRedirect('view/%s' % game.pk)
    else:
        form = InjectedGameForm()
    
    payload = {'form': form}
    payload.update(csrf(request))
    return render_to_response('thunderdome/inject.html', payload)


@login_required
def view_game(request, game_id):
    ### View the status of a single game
    return render_to_response('thunderdome/view_game.html', 
                              {'game': get_object_or_404(Game, pk=game_id)})


@login_required
def view_match(request, match_id):
    ### View the status of a single match
    return render_to_response('thunderdome/view_match.html', 
                              {'match': get_object_or_404(Match, pk=match_id)})


@login_required
def view_client(request, client_id):
    ### View the status of a single client
    return render_to_response('thunderdome/view_client.html', 
                              {'client': get_object_or_404(Client, 
                                                           pk=client_id)})


def scoreboard(request):
#    clients = Client.objects.all()
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

    # Load the data in the format the template expects
    for c1 in clients:
        c1.row = list()
        for c2 in clients:
            if c1 in grid and c2 in grid[c1]:
                c1.row.append((c1.pk,c2.pk,grid[c1][c2]))
            else:
                c1.row.append((c1.pk,c2.pk,' '))

    payload = {'clients': clients}
    return render_to_response('thunderdome/scoreboard.html', payload)


@login_required
def matchup(request, client1_id, client2_id):
    client1 = get_object_or_404(Client, pk=client1_id)
    client2 = get_object_or_404(Client, pk=client2_id)
    
    # manual join. fix this if you know how
    shared_games = Game.objects.filter(clients=client2).filter(clients=client1).order_by('-pk')

    c1wins = len([x for x in shared_games if x.winner == client1])
    c2wins = len([x for x in shared_games if x.winner == client2])
    
    payload = {'client1' : client1,
               'client2' : client2,
               'c1wins'  : c1wins,
               'c2wins'  : c2wins,
               'games'   : shared_games}    
    return render_to_response('thunderdome/matchup.html', payload)


def get_next_game_url_to_visualize(request):
    clients = Client.objects.exclude(name='bye')
    worst_client = min(clients, key = lambda x: x.last_visualized())
    next_gid = worst_client.games_played.all().filter(status='Complete').aggregate(Max('pk'))['pk__max']
    next_game = Game.objects.get(pk=next_gid)
    return HttpResponse(next_game.gamelog_url)


def game_visualized(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    game.visualized = datetime.now()
    game.save()
    return HttpResponse("OK")


def get_and_mark(request):
    clients = list(Client.objects.exclude(name='bye').exclude(embargoed=True))
    ok_clients = list()
    for c in clients:
        if c.games_played.all().exclude(gamelog_url='').count() != 0:
            ok_clients.append(c)
    
    worst_client = min(ok_clients, key = lambda x: x.last_visualized())
    next_gid = worst_client.games_played.all().exclude(gamelog_url='').aggregate(Max('pk'))['pk__max']
#    next_gid = list(worst_client.games_played.all().filter(status='Complete'))
    next_game = Game.objects.get(pk=next_gid)
    next_game.visualized = datetime.now()
    next_game.save()
    return HttpResponse(next_game.gamelog_url)
#    return HttpResponse(str(worst_client.name))


def visualize(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    stalk = beanstalkc.Connection()
    stalk.use('visualizer-requests')
    stalk.put(str(game.gamelog_url))
    stalk.close()
    return HttpResponse(game.gamelog_url)


def url_to_keyname(url):
    regex = "http://siggame-gamelogs\.s3\.amazonaws\.com/([\.\w-]+)"
    keyname = re.search(regex, url).groups()[0]
    return keyname


def sizeof_key(bucket, key):
    key = bucket.lookup(key)
    return key.size


from config import game_name, access_cred, secret_cred
def get_representative_game_url(match):    
    conn = boto.connect_s3(access_cred, secret_cred)
    bucket = conn.get_bucket('siggame-glog-%s' % game_name )
    
    urls = [x.gamelog_url for x in match.games.all() 
            if x.winner == match.winner]
    
    keynames = [url_to_keyname(x) for x in urls]
    biggest = max(keynames, key=lambda x: sizeof_key(bucket,x))
    regex = "([\d]+)-([\w]+)\.glog"
    game_id = re.search(regex,biggest).groups()[0]
    return game_id


def visualize_match(request, match_id):
    match = Match.objects.get(pk=match_id)
    if match.status != 'Complete':
        return HttpResponse("Incomplete match!")
    game_id = get_representative_game_url(match)
    return visualize(request, game_id)


def representative_game(request, match_id):
    ### View the status of the game that best represents a match
    match = Match.objects.get(pk=match_id)
    if match.status != 'Complete':
        return HttpResponse("Incomplete match!")
    game_id = get_representative_game_url(match)
    return view_game(request, game_id)

#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import re
import os
import json
from datetime import datetime

# Non-Django 3rd Party Imports
import beanstalkc
import boto

# Django Imports
import settings.defaults
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.db.models import Max

# My Imports
from thunderdome.config import game_name, access_cred, secret_cred
from thunderdome.models import Client, Game
from thunderdome.models import Match, Referee, InjectedGameForm
from thunderdome.sked import sked

def index(request):
    msg = "<html><body><p>Hello index page!</p></body></html>"
    return HttpResponse(msg)


def health(request):
    # Let's start by having this page show some arena health statistics
    p = dict() # payload for the render_to_response
    
    c = beanstalkc.Connection()
    c.use('game-requests-%s' % game_name)
    tube_status = c.stats_tube('game-requests-%s' % game_name)
    (p['ready_requests'], p['running_requests'], p['current_tube']) = \
        [tube_status[x] for x in ('current-jobs-ready',
                                  'current-jobs-reserved',
                                  'name')]
    c.close()
    
    (p['scheduled_games'], p['running_games'],
     p['complete_games'], p['failed_games'], p['building_games']) = \
        [Game.objects.filter(status=x).count
         for x in ('Scheduled', 'Running', 'Complete', 'Failed', 'Building')]
    
    p['sanity'] = p['ready_requests'] == p['scheduled_games'] \
        and p['running_games'] == p['running_requests']
    
    p['matches'] = list(Match.objects.order_by('-id'))
    p['matches'].sort(key=lambda x: x.status, reverse=True)
    
    p['last'] = \
        Game.objects.all().aggregate(Max('completed'))['completed__max']
    
    refs = Referee.objects.all().order_by('-pk')
    p['refs'] = refs
    return render_to_response('thunderdome/health.html', p)

def human_swiss(request):
    p = dict()
    
    clients = list(Client.objects.all())

    #h_clients = []
    #for i in clients:
    #    stats = json.loads(i.stats)
    #    if stats['language'] == "Human":
    #        h_clients.append(i)

    h_clients = [(i, json.loads(i.stats)) for i in clients if json.loads(i.stats)['language'] == "Human"]
    
    p['clients'] = h_clients
    p['client_names'] = [i[0].name for i in h_clients]
    return render_to_response('thunderdome/human_swiss.html', p)


def view_game(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    return render_to_response('thunderdome/view_game.html', {'game': game})

def view_match(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    return render_to_response('thunderdome/view_match.html', {'match' : match})

def representative_game(request, match_id):
    match = Match.objects.get(pk=match_id)
    if match.stats != 'Complete':
        return HttpResponse("Incomplete match!")
    game_id = 1
    return view_game(request, game_id)

def display_clients(request):
    clients = list(Client.objects.all())
    clients.sort(key = lambda x: x.rating, reverse=True)
    return render_to_response('thunderdome/clients.html', {'clients':clients})

def scoreboard(request):
    clients = Client.objects.exclude(current_version="")
    grid = dict()
    for c1 in clients:
        grid[c1] = dict()
        for c2 in clients:
            grid[c1][c2] = 0
            
    for c1 in clients:
        for c2 in clients:
            grid[c1][c2] = c1.games_won.filter(loser=c2).count()
            
    clients = list(clients)
    clients.sort(reverse=True, key=lambda x: x.fitness())
    
    for c1 in clients:
        c1.row = list()
        for c2 in clients:
            if c1 in grid and c2 in grid[c1]:
                c1.row.append((c1.pk, c2.pk, grid[c1][c2]))
            else:
                c1.row.append((c1.pk, c2.pk, ' '))
    payload = {'clients':clients}
    return render_to_response('thunderdome/scoreboard.html', payload)


@login_required
def inject(request):
    ### Handle manual inject of a game into the system
    if request.method == 'POST':
        form = InjectedGameForm(request.POST)
        if form.is_valid():
            clientOne = get_object_or_404(
                Client, pk__iexact=form.cleaned_data['clientOne'])
            clientTwo = get_object_or_404(
                Client, pk__iexact=form.cleaned_data['clientTwo'])
            
            stalk = beanstalkc.Connection()
            stalk.use('game-requests-%s' % game_name)
            game = sked(clientOne, clientTwo, stalk,
                        "Priorty Game Request", 0)
            stalk.close()
            return HttpResponseRedirect('view/%s' % game.pk)
    else:
        form = InjectedGameForm()
    payload = {'form': form}
    payload.update(csrf(request))
    return render_to_response('thunderdome/inject.html', payload)

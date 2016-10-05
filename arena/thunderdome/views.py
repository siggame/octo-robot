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
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.db.models import Max

# My Imports
from thunderdome.config import game_name, access_cred, secret_cred
from thunderdome.models import Client, Game, ArenaConfig
from thunderdome.models import Match, Referee, InjectedGameForm, SettingsForm
from thunderdome.sked import sked

from k_storage.models import DataPoint

def index(request):
    msg = "<html><body><p>Hello index page!</p></body></html>"
    return HttpResponse(msg)


@login_required(login_url='/admin')
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
        [Game.objects.filter(status=x).count()
         for x in ('Scheduled', 'Running', 'Complete', 'Failed', 'Building')]
    
    p['sanity'] = p['ready_requests'] == p['scheduled_games'] \
        and p['running_games'] + p['building_games'] == p['running_requests']
    
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

def get_next_game_url_to_visualize(request):
    found = False
    best_possible = False
    score_level = 0
    current_game = 0
    for x in Game.objects.all():
        if x.been_vised == False and x.status == 'Complete' and x.score == 6:
            next_game_url = x.gamelog_url
            x.been_vised = True
            found = True
            best_possible = True
            x.save()
            break
        if x.been_vised == False and x.status == 'Complete' and x.score == 5:
            found = True
            current_game = x
            score_level = 5
        if x.been_vised == False and x.status == 'Complete' and x.score == 3 and score_level < 3:
            found = True
            current_game = x
            score_level = 3
        if x.been_vised == False and x.status == 'Complete' and x.score == 2 and score_level < 2:
            found = True
            current_game = x
            score_level = 2
        if x.been_vised == False and x.status == 'Complete' and x.score == 1 and score_level == 0:
            found = True
            current_game = x
            score_level = 1
        if x.been_vised == False and x.status == 'Complete' and x.score == 0 and score_level == 0:
            found = True
            current_game = x
    if found and not best_possible:
        current_game.been_vised = True
        current_game.save()
        next_game_url = current_game.gamelog_url
    if not found:
        x = Game.objects.order_by('?').first()
        while x.status != 'Complete':
            x = Game.objects.order_by('?').first()
        next_game_url = x.gamelog_url
    return HttpResponse(next_game_url)

def rate_game(request, game_id, rating):
    print 'rating game', game_id, 'with rating', rating
    game = Game.objects.get(pk=game_id)
    game.add_rating(rating)
    game.save()
    
    data_point = DataPoint.objects.get(game_id=game_id)
    data_point.rating_value = game.get_average_rating()
    data_point.save()

    message = {"status" : "Rated"}
    return HttpResponse(json.dumps(message))

def representative_game(request, match_id):
    match = Match.objects.get(pk=match_id)
    if match.stats != 'Complete':
        return HttpResponse("Incomplete match!")
    game_id = 1
    return view_game(request, game_id)

def scores(request):
    clients = list(Client.objects.all().filter(embargoed=False).filter(missing=False))
    clients = sorted(clients, key = lambda x: x.rating, reverse=True)
    clients = sorted(clients, key = lambda x: x.num_black, reverse=True)
    clients = sorted(clients, key = lambda x: x.sumrate, reverse=True)
    clients = sorted(clients, key = lambda x: x.buchholz, reverse=True)
    clients = sorted(clients, key = lambda x: x.score, reverse=True)
    return render_to_response('thunderdome/scores.html', {'clients':clients})

def get_scores(request):
    clients = list(Client.objects.all().filter(embargoed=False).filter(missing=False))
    clients = sorted(clients, key = lambda x: x.rating, reverse=True)
    clients = sorted(clients, key = lambda x: x.num_black, reverse=True)
    clients = sorted(clients, key = lambda x: x.sumrate, reverse=True)
    clients = sorted(clients, key = lambda x: x.buchholz, reverse=True)
    clients = sorted(clients, key = lambda x: x.score, reverse=True)
    return JsonResponse({'clients':clients})

def display_clients(request):
    clients = list(Client.objects.all())
    clients.sort(key = lambda x: x.rating, reverse=True)
    return render_to_response('thunderdome/clients.html', {'clients':clients})

@login_required(login_url='/admin')
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


@login_required(login_url='/admin')
def settings(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            for i in ArenaConfig.objects.all():
                i.active = False
                i.save()
            arenaConfig = get_object_or_404(ArenaConfig, pk__iexact=form.cleaned_data['arenaConfig'])
            arenaConfig.active = True
            arenaConfig.save()
            # TODO have a redirect to a page that indicates what must be done
            # after settings have been changed
    else:
        form = SettingsForm()
    payload = {'arena_settings' : list(ArenaConfig.objects.all())}
    payload.update({'form' : form})
    payload.update(csrf(request))
    return render_to_response('thunderdome/settings.html', payload)



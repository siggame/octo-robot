#####
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import re
import os
import json
from datetime import datetime, timedelta

# Non-Django 3rd Party Imports
import beanstalkc
import boto

# Django Imports
import settings.defaults
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db.models import Max, Q

# My Imports
from thunderdome.config import game_name, access_cred, secret_cred
from thunderdome.models import Client, Game, ArenaConfig, GameData, WinRatePrediction
from thunderdome.models import Match, Referee, InjectedGameForm, SettingsForm, SearchGamesForm, GameStatisticsForm
from thunderdome.sked import sked

from k_storage.models import DataPoint

def index(request):
    #msg = "<html><body><p>Hello index page!</p></body></html>"
    #return HttpResponse(msg)
    return render_to_response('thunderdome/welcome.html')

def logout_view(request):
    logout(request)
    return render_to_response('thunderdome/logout.html')

@login_required(login_url='/admin')
def howtodev(request):
    return render_to_response('thunderdome/howtodev.html')

@login_required(login_url='/admin')
def health(request):
    # Let's start by having this page show some arena health statistics
    p = dict() # payload for the render_to_response
    
    c = beanstalkc.Connection()
    c.use('game-requests-%s' % game_name)
    tube_status = c.stats_tube('game-requests-%s' % game_name)
    (p['ready_requests'], p['running_requests']) = \
        [tube_status[x] for x in ('current-jobs-ready',
                                  'current-jobs-reserved')]
    c.use('game-results-%s' % game_name)
    tube_status = c.stats_tube('game-results-%s' % game_name)
    p['results_waiting'] = tube_status['current-jobs-ready']
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
    
    refs = Referee.objects.filter(~Q(games_done=0) | Q(dead=False)).order_by('-pk')
    p['refs'] = refs
    return render_to_response('thunderdome/health.html', p)

@login_required(login_url='/admin')
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

@login_required(login_url='/admin')
def view_game(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    return render_to_response('thunderdome/view_game.html', {'game': game})

@login_required(login_url='/admin')
def view_match(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    return render_to_response('thunderdome/view_match.html', {'match' : match})

def get_next_game_url_to_visualize(request):
    found = False
    for x in Game.objects.filter(score=6).filter(status='Complete').filter(been_vised=False):
        next_game_url = x.gamelog_url
        x.been_vised = True
        found = True
        x.save()
        break
    if not found:
        for x in Game.objects.filter(score=5).filter(status='Complete').filter(been_vised=False):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        for x in Game.objects.filter(score=3).filter(status='Complete').filter(been_vised=False):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        for x in Game.objects.filter(score=2).filter(status='Complete').filter(been_vised=False):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        for x in Game.objects.filter(score=1).filter(status='Complete').filter(been_vised=False):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        for x in Game.objects.filter(score=0).filter(status='Complete').filter(been_vised=False):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        x = Game.objects.order_by('?').first()
        while x.status != 'Complete':
            x = Game.objects.order_by('?').first()
        next_game_url = x.gamelog_url
    return HttpResponse(next_game_url)


def get_next_chess_game_url_to_visualize(request):
    found = False
    for x in Game.objects.filter(score=6).filter(status='Complete').filter(been_vised=False).filter(claimed=True):
        next_game_url = x.gamelog_url
        x.been_vised = True
        found = True
        x.save()
        break
    if not found:
        for x in Game.objects.filter(score=5).filter(status='Complete').filter(been_vised=False).filter(claimed=True):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        for x in Game.objects.filter(score=3).filter(status='Complete').filter(been_vised=False).filter(claimed=True):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        for x in Game.objects.filter(score=2).filter(status='Complete').filter(been_vised=False).filter(claimed=True):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        for x in Game.objects.filter(score=1).filter(status='Complete').filter(been_vised=False).filter(claimed=True):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        for x in Game.objects.filter(score=0).filter(status='Complete').filter(been_vised=False).filter(claimed=True):
            found = True
            x.been_vised = True
            x.save()
            next_game_url = x.gamelog_url
            break
    if not found:
        x = Game.objects.filter(claimed=True).order_by('?').first()
        while x.status != 'Complete':
            x = Game.objects.filter(claimed=True).order_by('?').first()
        next_game_url = x.gamelog_url
    return HttpResponse(next_game_url)


@login_required(login_url='/admin')
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

@login_required(login_url='/admin')
def representative_game(request, match_id):
    match = Match.objects.get(pk=match_id)
    if match.stats != 'Complete':
        return HttpResponse("Incomplete match!")
    game_id = 1
    return view_game(request, game_id)

#@login_required(login_url='/admin')
def scoreboards(request):
    return render_to_response('thunderdome/scoreboards.html')

#@login_required(login_url='/admin')
def scoreboard(request):
    return render_to_response('thunderdome/scoreboard.html')

#@login_required(login_url='/admin')
def mmai_scoreboard(request):
    return render_to_response('thunderdome/mmai_scoreboard.html')

def get_chess_scores(request):
    clients = list(Client.objects.filter(embargoed=False).filter(missing=False))
    clients = sorted(clients, key = lambda x: x.rating, reverse=True)
    clients = sorted(clients, key = lambda x: x.num_black, reverse=True)
    clients = sorted(clients, key = lambda x: x.sumrate, reverse=True)
    clients = sorted(clients, key = lambda x: x.buchholz, reverse=True)
    clients = sorted(clients, key = lambda x: x.score, reverse=True)
    client_data = [pull_chess_fields(i,c) for i,c in enumerate(clients)]    
    return JsonResponse({"data": client_data})

def get_mmai_scores(request):
    clients = list(Client.objects.filter(missing=False))
    clients = sorted(clients, key = lambda x: x.rating, reverse=True)
    client_data = [pull_mmai_fields(i,c) for i,c in enumerate(clients)]    
    return JsonResponse({"data": client_data})

def pull_chess_fields(i, c): #meant to pull client fields
    return {"rank": i+1,
            "name": c.name,
            "score": c.score,
            "sum_of_opps_score": c.buchholz,
            "sum_of_opps_rat": c.sumrate,
            "num_black": c.num_black,
            "language": c.language}

def pull_mmai_fields(i, c): #meant to pull client fields
    return {"rank": i+1,
            "name": c.name,
            "rating": c.rating}

@login_required(login_url='/admin')
def display_clients(request):
    return render_to_response('thunderdome/clients.html')

def get_clients(request):
    clients = list(Client.objects.all())
    clients = sorted(clients, key = lambda x: x.rating, reverse=True)
    client_data = [pull_client_fields(i,c) for i,c in enumerate(clients)]
    return JsonResponse({"data": client_data})

def pull_client_fields(i, c):
    return {"rank": i+1,
            "rating": c.rating,
            "client_name": c.name,
            "embargoed?": str(c.embargoed),
            "embargo_reason": c.embargo_reason,
            "missing?": str(c.missing),
            "eligible?": str(c.eligible),
            "last_game_played": c.last_game_played,
            "current_version": c.current_tag,
            "language": c.language}

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
                        "Priority Game Request", 0)
            stalk.close()
            return HttpResponseRedirect('view/%s' % game.pk)
    else:
        form = InjectedGameForm()
    payload = {'form': form}
    payload.update(csrf(request))
    return render_to_response('thunderdome/inject.html', payload)

#@login_required(login_url='/admin')
def gamestatistics(request):
    ### Used for showing win predictions
    if request.method == 'POST':
        form = GameStatisticsForm(request.POST)
        if form.is_valid():
            client = get_object_or_404(
                Client, pk__iexact=form.cleaned_data['client'])
            return HttpResponseRedirect('clientstatistics/%s' % client.name)
    else:
        form = GameStatisticsForm()
    winpredicts = WinRatePrediction.objects.exclude(winner__current_tag__iexact='shellai').exclude(loser__current_tag__iexact='shellai').exclude(winner__embargo_reason__icontains='cheat').exclude(loser__embargo_reason__icontains='cheat')
    clients = Client.objects.filter(missing=False).exclude(current_tag__iexact='shellai').exclude(embargo_reason__icontains='cheat').order_by('-winrate')
    colors = []
    for i, x in enumerate(clients):
        colors.append([])
        for y in clients:
            if x.name != y.name:
                for z in winpredicts:
                    if z.winner.name == x.name and z.loser.name == y.name:
                        if z.prediction >= 0.95:
                            colors[i].append('#15ff00')
                        elif z.prediction >= 0.9:
                            colors[i].append('#7fff00')
                        elif z.prediction >= 0.75:
                            colors[i].append('#bfff00')
                        elif z.prediction >= 0.5:
                            colors[i].append('#fff200')
                        elif z.prediction >= 0.25:
                            colors[i].append('#ff9000')
                        else:
                            colors[i].append('#ff0000')
                        break
            else:
                colors[i].append('#ffffff')
    payload = {'form':form, 'clients':clients, 'colors':colors} #'winpredicts':winpredicts}
    payload.update(csrf(request))
    return render_to_response('thunderdome/winpredictions.html', payload)

#@login_required(login_url='/admin')
def clientstatistics(request, clientname):
    client = Client.objects.get(name=clientname)
    winstats = WinRatePrediction.objects.filter(winner=client).order_by('-prediction').exclude(loser__current_tag__iexact='shellai')
    return render_to_response('thunderdome/clientstatistics.html', {'client':client, 'winstats':winstats})

@login_required(login_url='/admin')
def searchgames(request):
    if request.method == 'POST':
        form = SearchGamesForm(request.POST)
        if form.is_valid():
            client = get_object_or_404(
                Client, pk__iexact=form.cleaned_data['client'])
            start = form.cleaned_data['start']
            end = form.cleaned_data['end']
            showFailed = form.cleaned_data['showFailed']

            return HttpResponseRedirect('gameslist/{0}/{1}/{2}/{3}'.format(client.name, str(start), str(end), showFailed))
    else:
        form = SearchGamesForm()
    payload = {'form': form}
    payload.update(csrf(request))
    return render_to_response('thunderdome/searchgames.html', payload)

@login_required(login_url='/admin')
def gameslist(request, clientname, start, end, showFailed):
    time_delta_start = datetime.now() - timedelta(hours=float(start))
    time_delta_end = datetime.now() - timedelta(hours=float(end))
    games1 = list(Game.objects.filter(clients__name=clientname).filter(completed__gte=time_delta_start).filter(completed__lte=time_delta_end).order_by('-pk'))
    if showFailed == "True":
        games2 = list(Game.objects.filter(clients__name=clientname).filter(status='Failed').order_by('-pk'))
    else:
        games2 = {}
    gamedatas = list(GameData.objects.filter(client__name=clientname))
    client = Client.objects.get(name=clientname)
    return render_to_response('thunderdome/gameslist.html', {'games1':games1, 'games2':games2, 'client':client, 'gamedatas':gamedatas})

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
    else:
        form = SettingsForm()
    payload = {'arena_settings' : list(ArenaConfig.objects.all())}
    payload.update({'form' : form})
    payload.update(csrf(request))
    return render_to_response('thunderdome/settings.html', payload)



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
import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.db.models import Max

# My Imports
from thunderdome.config import game_name, access_cred, secret_cred
from thunderdome.models import Client, Game
#from thunderdome.sked import sked

def index(request):
    msg = "<html><body><p>Hello index page!</p></body></html>"
    return HttpResponse(msg)

def view_game(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    return render_to_response('thunderdome/view_game.html', {'game': game})

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

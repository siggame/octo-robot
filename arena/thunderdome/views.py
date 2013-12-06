
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
    return render_to_reponse('thunderdome/view_game.html', {'game': game})

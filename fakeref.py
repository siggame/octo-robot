#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

from datetime import datetime
import sys

# Some magic to get a standalone python program hooked in to django
sys.path = ['/home/gladiator', '/home/gladiator/djangolol'] + sys.path

from django.core.management import setup_environ
import settings

setup_environ(settings)

# Non-Django 3rd Party Imports
import json               # special strings
import beanstalkc         # networky
import random, time

# My Imports
from thunderdome.models import Game

stalk = None

def main():
    global stalk
    stalk = beanstalkc.Connection()
    
    stalk.watch('game-requests')
    while True:
        looping()
    

def looping():
    global stalk
    # get a game
    job = stalk.reserve(timeout=2)
    if job is None:
        return
    game_id = json.loads(job.body)['game_id']
    game = Game.objects.get(pk=game_id)
    print "fake processing game", game_id

    gamedatas = list(game.gamedata_set.all())

    sleepytime = random.randint(12,24)
    for i in xrange(sleepytime):
        time.sleep(10)
        job.touch()
    
    # figure out who won by reading the gamelog
    winner, loser = coin_flip(gamedatas[0].client, gamedatas[1].client)
    game.winner = winner
    game.loser = loser
    print winner.name, "beats", loser.name
    if game.winner == gamedatas[0].client:
        gamedatas[0].won = True
        gamedatas[1].won = False
    else:
        gamedatas[0].won = False
        gamedatas[1].won = True
    [x.save() for x in gamedatas]        
    
    # clean up
    game.status = "Complete"
    game.completed = datetime.now()
    
    game.save()
    job.delete()

    
def coin_flip(client1, client2):
    winner = SUS([client1, client2], 1, lambda x: x.fitness())[0]
    if client1 == winner:
        loser = client2
    else:
        loser = client1
    return winner, loser
    

def SUS(population, n, weight):
    ### @brief  roulette wheel selection, select n individuals
    ### @pre    None
    ### @post   None
    ### @param  population the set from which individuals are to be chosen
    ### @param  n the number of individuals to choose
    ### @param  weight the function that determines the weight of an individual
    ###           hint: lambda functions work well here
    ### @return A list of randomly chosen individuals
    result = list()
    weight_range = sum([weight(x) for x in population])
    spacing = weight_range / n
    offset = random.random() * spacing
    accumulator = 0
    i = 0
    for individual in population:
        accumulator += weight(individual)
        if accumulator >= i * spacing + offset:
            result.append(individual)
            i += 1
        if i >= n:
            break
    return result


main()

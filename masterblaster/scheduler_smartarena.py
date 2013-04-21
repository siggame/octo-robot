#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import random
import urllib
import json
import time
from collections import defaultdict

# Non-Django 3rd Party Imports
import beanstalkc

# My Imports
import bootstrap
from thunderdome.config import game_name, req_queue_len, api_url_template
from thunderdome.models import Client, WinRatePrediction
from thunderdome.sked import sked

api_url = api_url_template % game_name


def main():
    req_tube = "game-requests-%s" % game_name
    while True:
        try:
            stalk = beanstalkc.Connection()
            stalk.use(req_tube)
            stats = stalk.stats_tube(req_tube)
            if stats['current-jobs-ready'] < req_queue_len:
                update_clients()
                schedule_a_game(stalk)
            stalk.close()
        except:
            print "Arena scheduler could not schedule a game"
        time.sleep(1)


def schedule_a_game(stalk):
    '''Schedule the most needy client and a random partner for a game'''
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))
    if len(clients) < 2:  # takes two to tango
        print "only", len(clients), "clients in the arena"
        return
    worst_client = min(clients, key=lambda x: x.last_game())
    clients.remove(worst_client)
    partner = pick_partner(worst_client, clients)
    players = [worst_client, partner]
    random.shuffle(players)
    sked(players[0], players[1], stalk, "Smart Arena Scheduler")


def pick_partner(needy, potentials):
    predict = defaultdict(lambda: 0.5,
                          {(x.winner, x.loser): x.prediction
                           for x in WinRatePrediction
                                     .objects
                                     .filter(winner=needy)})
    fitness = lambda x: (1.5 - abs(0.5 - predict[(needy, x)])) ** 15
    return FP(potentials, fitness=fitness)


def update_clients():
    '''Import updated client info from Wisely's tastypie API'''
    try:
        f = urllib.urlopen(api_url)
        data = json.loads(f.read())
        f.close()
    except:
        return
    for block in data:
        if block['tag'] is None:
            block['tag'] = ''
        if Client.objects.filter(name=block['name']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['name'])
        if client.current_version != block['tag']:
            client.embargoed = False  # only place an embargo can be broken
            client.current_version = block['tag']
            client.save()
        if client.repo != block['path']:
            client.repo = block['path']
            client.save()


def makeClient(block):
    '''Make a client object from the provided API data block'''
    client = Client.objects.create()
    client.name = block['name']
    client.current_version = block['tag']
    client.repo = block['path']
    client.embargoed = False
    client.eligible = True  # tournament eligible
    client.seed = 0
    client.save()
    return client


def stochastic_universal_sampling(population,
                                  fitness=lambda x: x.fitness,
                                  n=1):
    '''Selects members of a population'''
    total_fitness = sum([fitness(x) for x in population])
    spacing = total_fitness / float(n)
    choice_point = random.random() * spacing
    accumulated_fitness = 0
    result = list()
    for individual in population:
        accumulated_fitness += fitness(individual)
        while choice_point < accumulated_fitness:
            result.append(individual)
            choice_point += spacing
    return result

SUS = stochastic_universal_sampling


def fitness_proportional(population, fitness=lambda x: x.fitness):
    '''Selects a single member of a population'''
    return SUS(population, fitness, 1)[0]

FP = fitness_proportional

if __name__ == "__main__":
    main()



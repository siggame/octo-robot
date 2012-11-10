#!/usr/bin/env python
"""
Missouri S&T ACM SIG-Game Arena (Thunderdome)

A task process that starts the referees (who play the matches.)

@author: Matthew Nuckolls <mannr4@mst.edu>
"""

# Standard Imports
import json
import time
import random

# Non-Django 3rd Party Imports
import beanstalkc

# My Imports
import bootstrap
from thunderdome.config import game_name
from thunderdome.models import Game, GameData, Match

stalk = None


def main():
    req_tube = "game-requests-%s" % game_name
    """
    Starts the main tournament managment loops. Creates a beanstalk
    connection and watches for signals from processes that they are
    requeststing matches.
    """
    global stalk
    stalk = beanstalkc.Connection()
    stalk.watch(req_tube)
    stalk.use(req_tube)
    championships = list(Match.objects.filter(root=True))
    while not all([x.winner for x in championships]):
        for championship in championships:
            maintain_bracket(championship)
        if stalk.stats_tube(req_tube)['current-jobs-ready'] < 1:
            generate_speculative_game(random.choice(championships))


def generate_speculative_game(match):
    """
    Traverses the tree to identify matches that should be played. Keeps the
    tournament moving forward.

    @param match: The root match to try and fulfill the dependencies for.
    @pre: A match tree needs to be played.
    @post: Some dependency of match is scheduled to be played.
    """
    traverse = [match]
    closed = set([match.id])
    needy_matches = list()
    ### concept here is that we're going to find matches who are waiting, and
    ### whos parents are either running or complete.
    while len(traverse) > 0:
        match = traverse.pop(0)
        if match.status == 'Waiting':
            zeros = list()
            ones = list()
            if match.p0:
                zeros = [match.p0]
            else:  # match.father is not None. this is a fact.
                if match.father.status == 'Complete':
                    if match.father_type == 'win':
                        zeros = [match.father.winner]
                    else:
                        zeros = [match.father.loser]
                if match.father.status == 'Running':
                    zeros = [match.father.p0, match.father.p1]
                if match.father.status == 'Waiting':
                    if match.father.id not in closed:
                        traverse.append(match.father)
                        closed.add(match.father.id)
            if match.p1:
                ones = [match.p1]
            else:  # match.mother is not None. this is a fact.
                if match.mother.status == 'Complete':
                    if match.mother_type == 'win':
                        ones = [match.mother.winner]
                    else:
                        ones = [match.mother.loser]
                if match.mother.status == 'Running':
                    ones = [match.mother.p0, match.mother.p1]
                if match.mother.status == 'Waiting':
                    if match.mother.id not in closed:
                        traverse.append(match.mother)
                        closed.add(match.mother.id)
            while 'bye' in zeros:
                zeros.remove('bye')
            while 'bye' in ones:
                ones.remove('bye')
            if all([zeros, ones]):
                match.zeros = zeros
                match.ones = ones
                needy_matches.append(match)

    if len(needy_matches) > 0:
      for match in needy_matches:
        if match.father_type == 'win':
            fit = lambda x: x.fitness()
        else:
            fit = lambda x: 1 - x.fitness()
        try:
            p0 = SUS(match.zeros, 1, fit)[0]
        except:
            p0 = random.choice(match.zeros)
        if match.mother_type == 'win':
            fit = lambda x: x.fitness()
        else:
            fit = lambda x: 1 - x.fitness()
        try:
            p1 = SUS(match.ones, 1, fit)[0]
        except:
            p1 = random.choice(match.ones)
        if p0.name == 'bye' or p1.name == 'bye':
            continue
        game = Game.objects.create()
        GameData(game=game, client=p0).save()
        GameData(game=game, client=p1).save()
        game.tournament = True
        game.claimed = False
        payload_d = { 'number'         : str(game.pk),
                      'status'         : "Scheduled",
                      'clients'        : list(),
                      'time_scheduled' : str(time.time()),
                      'tournament'     : True}
        for p in [p0, p1]:
            payload_d['clients'].append({ 'name' : p.name,
                                          'repo' : p.repo,
                                          'tag'  : p.current_version })
        game.stats = json.dumps(payload_d)
        game.status = "Scheduled"
        game.save()
        stalk.put(game.stats, ttr=300)
        match.games.add(game)
        print "Speculatively scheduled", p0.name, \
            "vs", p1.name, "in match", match.id


def maintain_bracket(match):
    """
    Updates the state of the bracket so that the speculative scheduler can
    determine which dependencies have already been fulfilled.

    @pre: The bracket state may have changed
    @post: Does a breadth first search down the dependency tree, looking
    for solvable dependencies. except it's not a dependency tree.
    it's a tournament bracket. which is jock-speak for dependency tree.
    """
    matchlist = list()
    closed = set()
    matchlist.append(match)
    while len(matchlist) > 0:
        match = matchlist.pop(0)
        if match.status != 'Complete':
            if match.p0 is None:
                if match.father.id not in closed:
                    matchlist.append(match.father)
                    closed.add(match.father.id)
            if match.p1 is None:
                if match.mother.id not in closed:
                    matchlist.append(match.mother)
                    closed.add(match.mother.id)
            maintain_match(match)


def maintain_match(match):
    """
    Determines and attempts to resolve dependencies to get a single match
    scheduled in the tournament. Schedules all the subgames of a match.

    @param match: The match to attempt to play.
    """
    ### Check on a single match, get it going if possible
    if match.status == 'Complete':
        return

    # check if parent maintanence can get this match started
    if match.p0 is None and match.father is not None:
        if match.father_type == 'win' and match.father.winner is not None:
            match.p0 = match.father.winner
        if match.father_type == 'lose' and match.father.loser is not None:
            match.p0 = match.father.loser

    if match.p1 is None and match.mother is not None:
        if match.mother_type == 'win' and match.mother.winner is not None:
            match.p1 = match.mother.winner
        if match.mother_type == 'lose' and match.mother.loser is not None:
            match.p1 = match.mother.loser

    #  might have gotten one but not the other
    if match.p0 is None or match.p1 is None:
        match.save()
        return

    # handle the byes
    if match.p0.name == 'bye':
        match.winner = match.p1
        match.loser = match.p0
        match.status = 'Complete'
        match.save()
        print "********", match.winner.name, "gets a bye"
        return
    elif match.p1.name == 'bye':
        match.winner = match.p0
        match.loser = match.p1
        match.status = 'Complete'
        match.save()
        print "********", match.winner.name, "gets a bye"
        return

    # handle the "maybe" matches.
    if match.p0.matches_lost.count() >= match.losses_to_eliminate:
        match.winner = match.p1
        match.loser = match.p0
        match.status = 'Complete'
        match.save()
        print "********", match.winner.name, "doesn't need to play", \
            match.loser.name, "in an optional match"
        return
    if match.p1.matches_lost.count() >= match.losses_to_eliminate:
        match.winner = match.p0
        match.loser  = match.p1
        match.status = 'Complete'
        match.save()
        print "********", match.winner.name, "doesn't need to play", \
            match.loser.name, "in an optional match"
        return

    match.status = 'Running'
    p0wins = match.games.filter(winner=match.p0).count()
    p1wins = match.games.filter(winner=match.p1).count()
    ### there will be speculative games in the list. 
    ### gotta check both winner and loser.
    ### actually no there won't.
    if p0wins >= match.wins_to_win:
        match.winner = match.p0
        match.loser = match.p1
        match.status = 'Complete'
        print "********", match.winner.name, "beats", match.loser.name
        match.save()
        return
    if p1wins >= match.wins_to_win:
        match.winner = match.p1
        match.loser = match.p0
        match.status = 'Complete'
        print "********", match.winner.name, "beats", match.loser.name
        match.save()
        return

    # if we made it to here, we're making games. but, how many?
    # how about "enough to possibly finish, if the loser would
    # kindly stop winning"
    # cancel that. schedule 7 games, you cheap bastard.
    real_games = list()
    for game in list(match.games.all()):
        p0found = False
        p1found = False
        for data in game.gamedata_set.all():
            if match.p0 == data.client:
                p0found = True
            if match.p1 == data.client:
                p1found = True
        if p0found and p1found:
            real_games.append(game)
        else:  # kick the unneeded games out into the pool
            game.claimed = False
            game.save()
            match.games.remove(game)

    #count = match.wins_to_win + min([p0wins,p1wins]) - len(real_games)
    count = (match.wins_to_win * 2) - 1 - len(real_games)
    for i in xrange(count):
        game = get_game_from_pool(match)
        if game is None:
            game = Game.objects.create()
            GameData(game=game, client=match.p0).save()
            GameData(game=game, client=match.p1).save()
            game.tournament = True
            payload_d = { 'number'         : str(game.pk),
                          'status'         : "Scheduled",
                          'clients'        : list(),
                          'time_scheduled' : str(time.time()),
                          'tournament'     : True }
            for p in [match.p0, match.p1]:
                payload_d['clients'].append({ 'name' : p.name,
                                              'repo' : p.repo,
                                              'tag'  : p.current_version })
            game.stats = json.dumps(payload_d)
            game.status = "Scheduled"
            game.save()
            stalk.put(game.stats, ttr=300)

            print "Scheduled", match.p0.name, "vs", match.p1.name
        else:
            print "Got", match.p0.name, "vs", match.p1.name, "from pool"
            game.claimed = True
            game.save()
        match.games.add(game)
    match.save()


def get_game_from_pool(match):
    """
    Picks a game from the game pool.

    @param: The match to find games from.
    """
    for game in list(Game.objects.filter(claimed=False).order_by('id')):
        gd = list(game.gamedata_set.all())
        if gd[0].client == match.p0 and gd[1].client == match.p1:
            return game
        if gd[0].client == match.p1 and gd[1].client == match.p0:
            return game
    return None


def SUS(population, n, weight):
    """
    roulette wheel selection, select n individuals

    @pre    None
    @post   None
    @param  population the set from which individuals are to be chosen
    @param  n the number of individuals to choose
    @param  weight the function that determines the weight of an individual
             hint: lambda functions work well here
    @return A list of randomly chosen individuals
    """
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

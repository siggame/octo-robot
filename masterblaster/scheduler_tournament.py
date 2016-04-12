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
#import bootstrap
from thunderdome.config import game_name
from thunderdome.models import Game, GameData, Match

import django
django.setup()

stalk = None


def main():
    req_tube = "game-requests-%s" % game_name
    """
    Starts the main tournament managment loops. Creates a beanstalk
    connection and watches for signals from processes that they are
    requesting matches.
    """
    global stalk
    stalk = beanstalkc.Connection()
    stalk.watch(req_tube)
    stalk.use(req_tube)
    championships = list(Match.objects.filter(root=True))
    needy = [x for x in championships if x.winner is None]
    while needy:
        maintain_bracket(needy[0])
        championships = list(Match.objects.filter(root=True))
        needy = [x for x in championships if x.winner is None]
        stats = stalk.stats_tube(req_tube)
        if stats['current-jobs-ready'] < 1:
	    try:
		generate_speculative_game(random.choice(needy))
	    except:
		print "No needy matches to schedule speculative games for."
    for g in Game.objects.filter(claimed=False):
        g.claimed = True
        g.save()
    finish()

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
    while traverse:
        match = traverse.pop(0)
        if match.status == 'Waiting':
            zeros = list()
            ones = list()
            if match.p0:
                zeros = [match.p0]
            else:  # match.father is not None. this is a fact.
                if match.father.status == 'Complete':
                    zeros = {'win'  : [match.father.winner],
                             'lose' : [match.father.loser]}[match.father_type]
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
                    ones = {'win'  : [match.mother.winner],
                            'lose' : [match.mother.loser]}[match.mother_type]
                if match.mother.status == 'Running':
                    ones = [match.mother.p0, match.mother.p1]
                if match.mother.status == 'Waiting':
                    if match.mother.id not in closed:
                        traverse.append(match.mother)
                        closed.add(match.mother.id)
            zeros = [x for x in zeros if x != 'bye']
            ones = [x for x in ones if x != 'bye']
            if all([zeros, ones]):
                match.zeros = zeros
                match.ones = ones
                needy_matches.append(match)

    for match in needy_matches:
        p0 = random.choice(match.zeros)
        p1 = random.choice(match.ones)
        if p0.name == 'bye' or p1.name == 'bye' or p0.name == p1.name:
            continue
        game = Game.objects.create()
        GameData(game=game, client=p0).save()
        GameData(game=game, client=p1).save()
        game.tournament = True
        game.claimed = False
        payload_d = {'number'         : str(game.pk),
                     'status'         : "Scheduled",
                     'clients'        : list(),
                     'time_scheduled' : str(time.time()),
                     'tournament'     : True}
        for p in [p0, p1]:
            payload_d['clients'].append({'name' : p.name,
                                         'repo' : p.repo,
                                         'tag'  : p.current_version})
        game.stats = json.dumps(payload_d)
        game.status = "Scheduled"
        game.claimed = False
        game.save()
        stalk.put(game.stats, priority=2000, ttr=400)
        print "Speculatively scheduled", game, "with", p0.name, "vs", p1.name


def maintain_bracket(match):
    """
    Updates the state of the bracket so that the speculative scheduler can
    determine which dependencies have already been fulfilled.

    @pre: The bracket state may have changed
    @post: Does a breadth first search down the dependency tree, looking
    for solvable dependencies. except it's not a dependency tree.
    it's a tournament bracket. which is jock-speak for dependency tree.
    """
    matchlist = [match]
    closed = set()
    while matchlist:
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
    if match.status == 'Complete':
        return

    # check if parent maintanence can get this match started
    if match.father is not None:
        match.p0 = {'win'  : match.father.winner,
                    'lose' : match.father.loser}[match.father_type]

    if match.mother is not None:
        match.p1 = {'win'  : match.mother.winner,
                    'lose' : match.mother.loser}[match.mother_type]

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
    p0l = match.p0.matches_lost.filter(tournament=match.tournament).count()
    if p0l >= match.losses_to_eliminate:
        match.winner = match.p1
        match.loser = match.p0
        match.status = 'Complete'
        match.save()
        print "********", match.winner.name, "doesn't need to play", \
            match.loser.name, "in an optional match"
        return
    p1l = match.p1.matches_lost.filter(tournament=match.tournament).count()
    if p1l >= match.losses_to_eliminate:
        match.winner = match.p0
        match.loser = match.p1
        match.status = 'Complete'
        match.save()
        print "********", match.winner.name, "doesn't need to play", \
            match.loser.name, "in an optional match"
        return

    match.status = 'Running'
    p0wins = match.games.filter(winner=match.p0).count()
    p1wins = match.games.filter(winner=match.p1).count()
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

    # if we made it to here, we're making games
    count = (match.wins_to_win * 2) - 1 - match.games.count()
    for i in xrange(count):
        game = get_game_from_pool(match)
        if game is None:
            #TODO update this with sked from thunderdome.sked
            # needs to be carefully done since game.tournament = true is important
            game = Game.objects.create()
            if i % 2 == 0:
                player_order = [match.p0, match.p1]
            else:
                player_order = [match.p1, match.p0]
            GameData(game=game, client=player_order[0]).save()
            GameData(game=game, client=player_order[1]).save()
            game.tournament = True
            payload_d = {'number'         : str(game.pk),
                         'status'         : "Scheduled",
                         'clients'        : list(),
                         'time_scheduled' : str(time.time()),
                         'tournament'     : True}

            for p in player_order:
                payload_d['clients'].append({'name' : p.name,
                                             'repo' : p.repo,
                                             'tag'  : p.current_version})
            game.stats = json.dumps(payload_d)
            game.status = "Scheduled"
            game.save()
            stalk.put(game.stats, priority=1000, ttr=400)
            print "Scheduled", game, player_order[0].name, "vs", player_order[1].name
        else:
            player_order = list(game.clients.all())
            print "Got", player_order[0].name, "vs", player_order[1].name, "from pool"
            game.claimed = True
            game.save()
        match.games.add(game)
    match.save()


def get_game_from_pool(match):
    """
    Picks a game from the game pool.

    @param: The match to find games for.
    """
    for game in Game.objects.filter(claimed=False).order_by('id'):
        #gd = game.gamedata_set.all()
        if game.status != "Failed":
	    gd = list(game.clients.all())
	    if gd[0].name == match.p0.name and gd[1].name == match.p1.name:
	        return game
	  #Uncomment if you don't care about who's player 1
	  #if gd[0].name == match.p1.name and gd[1].name == match.p0.name:
	      #return game
    return None

def finish():
    print "FFFFFFFFFFFFFFFFFFFF    IIIIIII    NNNNNNNNNN         NNNNNNN"
    print "FFFFFFFFFFFFFFFFFFFF    IIIIIII    NNNNNNNNNNN        NNNNNNN"
    print "FFFFFFFFFFFFFFFFFFFF    IIIIIII    NNNNNNNNNNNN       NNNNNNN"
    print "FFFFFFF                 IIIIIII    NNNNNNNNNNNNN      NNNNNNN"
    print "FFFFFFF                 IIIIIII    NNNNNNNNNNNNNN     NNNNNNN"
    print "FFFFFFF                 IIIIIII    NNNNNNNNNNNNNNN    NNNNNNN"
    print "FFFFFFFFFFFFF           IIIIIII    NNNNNNN NNNNNNNN   NNNNNNN"
    print "FFFFFFFFFFFFF           IIIIIII    NNNNNNN  NNNNNNNN  NNNNNNN"
    print "FFFFFFFFFFFFF           IIIIIII    NNNNNNN   NNNNNNNN NNNNNNN"
    print "FFFFFFF                 IIIIIII    NNNNNNN    NNNNNNNNNNNNNNN"
    print "FFFFFFF                 IIIIIII    NNNNNNN     NNNNNNNNNNNNNN"
    print "FFFFFFF                 IIIIIII    NNNNNNN      NNNNNNNNNNNNN"
    print "FFFFFFF                 IIIIIII    NNNNNNN       NNNNNNNNNNNN"
    print "FFFFFFF                 IIIIIII    NNNNNNN        NNNNNNNNNNN"
    print "FFFFFFF                 IIIIIII    NNNNNNN         NNNNNNNNNN"
    
    return

if __name__ == "__main__":
    for g in Game.objects.filter(claimed=False):
        g.claimed = True
        g.save()
    main()

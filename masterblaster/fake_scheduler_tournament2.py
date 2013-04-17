#!/usr/bin/env python
"""
Missouri S&T ACM SIG-Game Arena (Thunderdome)

A task process that starts the referees (who play the matches.)

@author: Matthew Nuckolls <mannr4@mst.edu>
"""

# Standard Imports
import json
import random

# Non-Django 3rd Party Imports

# My Imports
import bootstrap
from thunderdome.models import Match

grid = None


def main():
    global grid
    with open('grid.json', 'r') as f:
        grid = json.loads(f.read())
    championships = list(Match.objects.filter(root=True))
    needy = [x for x in championships if x.winner is None]
    while needy:
        maintain_bracket(needy[0])
        championships = list(Match.objects.filter(root=True))
        needy = [x for x in championships if x.winner is None]


def maintain_bracket(match):
    """
    Updates the state of the bracket so that the speculative scheduler can
    determine which dependencies have already been fulfilled.

    @pre: The bracket state may have changed
    @post: Does a breadth first search down the dependency tree, looking
    for solvable dependencies. except it's not a dependency tree.
    it's a tournament bracket. which is jock-speak for dependency tree.
    """
    matches = Match.objects \
        .filter(tournament=match.tournament) \
        .filter(status='Waiting') \
        .filter(father__winner__isnull=False) \
        .filter(mother__winner__isnull=False)
    for match in matches:
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

    ### Fakery starts here
    fake_games = list()
    for i in xrange(match.wins_to_win * 2 - 1):
        if random.random() < grid[match.p0.name][match.p1.name]:
            winner = 0
        else:
            winner = 1
        fake_games.append(winner)

    match.status = 'Running'
    p0wins = len([x for x in fake_games if x == 0])
    p1wins = len([x for x in fake_games if x == 1])
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


if __name__ == "__main__":
    main()

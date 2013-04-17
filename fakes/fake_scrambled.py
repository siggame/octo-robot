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
from build_fake_single_elim import build_it
grid = None
losses = None


def main():
    global grid
    global losses
    losses = dict()
    with open('grid.json', 'r') as f:
        grid = json.loads(f.read())
    with open('seeds.json', 'r') as f:
        seeds = json.loads(f.read())

    vals = seeds.values()
    random.shuffle(vals)
    for (k, v) in zip(seeds.keys(), vals):
        seeds[k] = v

    championship = build_it(seeds)
    while championship.winner is None:
        maintain_bracket(championship)
    print "%s, %s, %s" % (championship.winner,
                          championship.loser,
                          championship.mother.mother.mother.loser)


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
                if match.father not in closed:
                    matchlist.append(match.father)
                    closed.add(match.father)
            if match.p1 is None:
                if match.mother not in closed:
                    matchlist.append(match.mother)
                    closed.add(match.mother)
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
    if match.p0 == 'bye':
        match.winner = match.p1
        match.loser = match.p0
        match.status = 'Complete'
        return
    elif match.p1 == 'bye':
        match.winner = match.p0
        match.loser = match.p1
        match.status = 'Complete'
        return

    # handle the "maybe" matches.
    p0l = losses.get(match.p0, 0)
    if p0l >= match.losses_to_eliminate:
        match.winner = match.p1
        match.loser = match.p0
        match.status = 'Complete'
        return
    p1l = losses.get(match.p1, 0)
    if p1l >= match.losses_to_eliminate:
        match.winner = match.p0
        match.loser = match.p1
        match.status = 'Complete'
        return

    ### Fakery starts here
    fake_games = list()
    for i in xrange(match.wins_to_win * 2 - 1):
        if random.random() < grid[match.p0][match.p1]:
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
        if match.p1 not in losses:
            losses[match.p1] = 0
        losses[match.p1] += 1
        match.status = 'Complete'
        return
    if p1wins >= match.wins_to_win:
        match.winner = match.p1
        match.loser = match.p0
        if match.p0 not in losses:
            losses[match.p0] = 0
        losses[match.p0] += 1
        match.status = 'Complete'
        return

import sys

if __name__ == "__main__":
    if len(sys.argv) == 1:
        times = 1
    else:
        times = int(sys.argv[-1])
    for i in xrange(times):
        main()

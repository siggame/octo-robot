#!/usr/bin/env python
#
# Tournament matchmaker
# Andrew Underwood's algorithm
# Matt Nuckolls's implementation

from math import log, ceil

# My Imports
#import bootstrap
from thunderdome.models import Client, Match
from seeder import seed

tournament = 20133422

### clear old stuff
#for m in Match.objects.all():
#  m.delete()

### seed doods
seed()

try:
  Client.objects.get(name='bye')
except:
  Client.objects.create(name='bye', embargoed=True, eligible=False)


def seed_or_bye(n):
    try:
        result = Client.objects.get(seed=n)
    except:
        result = Client.objects.get(name='bye')
    return result


def pow2(exp):
    return 2 ** exp


def make_bye():
    try:
        Client.objects.get(name='bye')
    except:
        Client(name='bye').save()


def build_triple_elim():
    match_map = dict()

    def make_match(my_ID, mother_type, father_type, mother_ID, father_ID):
        m = Match.objects.create()
        m.mother = match_map[mother_ID]
        m.father = match_map[father_ID]
        m.mother_type = mother_type
        m.father_type = father_type
        match_map[my_ID] = m
        m.tournament = tournament
        m.save()

    eligible_count = Client.objects.filter(embargoed=False).filter(eligible=True).count()
    exp2 = int(ceil(log(eligible_count, 2)))
    bracket_size = pow2(exp2)
    print eligible_count
    print bracket_size

    # single elim
    for i in xrange(1, 1 + bracket_size / 2):
        m = Match.objects.create()
        m.p0 = seed_or_bye(i)
        m.p1 = seed_or_bye(bracket_size + 1 - i)
        match_map[(1, 1, i)] = m
        m.tournament = tournament
        m.save()

    for j in xrange(2, exp2 + 1):
        x = pow2(j)
        for i in xrange(1, 1 + bracket_size / x):
            make_match((1, j, i), 'win', 'win',
                       (1, j - 1, i),
                       (1, j - 1, bracket_size * 2 / x + 1 - i))
    # return

    # double elim
    for i in xrange(1, 1 + bracket_size / 4):
        make_match((2, 1, i), 'lose', 'lose',
                   (1, 1, i),
                   (1, 1, bracket_size / 2 + 1 - i))

    for i in xrange(1, 1 + bracket_size / 4):
        make_match((2, 2, i), 'win', 'lose',
                   (2, 1, bracket_size / 4 + 1 - i),
                   (1, 2, i))

    for j in xrange(3, exp2 + 1):
        x = bracket_size / pow2(j)
        for i in xrange(1, 1 + x):
            make_match((2, 2 * j - 3, i), 'win', 'win',
                       (2, 2 * j - 4, 2 * x + 1 - i),
                       (2, 2 * j - 4, i))
        for i in xrange(1, 1 + x):
            make_match((2, 2 * j - 2, i), 'win', 'lose',
                       (2, 2 * j - 3, x + 1 - i),
                       (1, j, i))

    # triple elim
    for i in xrange(1, 1 + bracket_size / 4):
        make_match((3, 1, i), 'lose', 'lose',
                   (2, 1, bracket_size / 4 + 1 - i),
                   (2, 2, i))

    for j in xrange(3, exp2 + 1):
        x = bracket_size / pow2(j)
        for i in xrange(1, 1 + x):
            make_match((3, 3 * j - 7, i), 'win', 'win',
                       (3, 3 * j - 8, 2 * x + 1 - i),
                       (3, 3 * j - 8, i))

        for i in xrange(1, 1 + x):
            make_match((3, 3 * j - 6, i), 'win', 'lose',
                       (3, 3 * j - 7, x + 1 - i),
                       (2, 2 * j - 3, i))

        for i in xrange(1, 1 + x):
            make_match((3, 3 * j - 5, i), 'win', 'lose',
                       (3, 3 * j - 6, x + 1 - i),
                       (2, 2 * j - 2, i))

    # championships
    single_winner = (1, exp2, 1)
    double_winner = (2, 2 * exp2 - 2, 1)
    triple_winner = (3, 3 * exp2 - 5, 1)

    make_match((4, 1, 1), 'win', 'win',
               double_winner, triple_winner)
    make_match((4, 2, 1), 'win', 'lose',
               (4, 1, 1), (4, 1, 1))
    make_match((5, 1, 1), 'win', 'win',
               (4, 2, 1), single_winner)
    make_match((5, 2, 1), 'win', 'lose',
               (5, 1, 1), (5, 1, 1))
    make_match((5, 3, 1), 'win', 'lose',
               (5, 2, 1), (5, 2, 1))
    make_match((5, 4, 1), 'win', 'lose',
               (5, 3, 1), (5, 3, 1))
    match_map[(5, 4, 1)].root = True
    match_map[(5, 4, 1)].save()


if __name__ == "__main__":
    build_triple_elim()

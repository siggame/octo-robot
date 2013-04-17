#!/usr/bin/env python
"""
Missouri S&T ACM SIG-Game Arena (Thunderdome)

A doodad to test the concept of scheduling games based on client
skill proximity

@author: Matthew Nuckolls <mannr4@mst.edu>
"""

import json
import random

tightness = 30
alpha = 0.2


def main():
    with open('grid.json', 'r') as f:
        grid = json.loads(f.read())
    clients = grid.keys()
    predict = defaultdict(lambda: 0.5)

    for i in xrange(12000):
        needy = random.choice(clients)
        fitness = lambda x: (1.5 - abs(0.5 - predict[(needy, x)])) ** tightness
        potentials = grid[needy].keys()
        partner = FP(potentials, fitness=fitness)
        if random.random() < grid[needy][partner]:
            predict[(needy, partner)] += alpha * (1 - predict[(needy, partner)])
            predict[(partner, needy)] -= alpha * predict[(partner, needy)]
        else:
            predict[(needy, partner)] -= alpha * predict[(needy, partner)]
            predict[(partner, needy)] += alpha * (1 - predict[(partner, needy)])
    for (k, v) in sorted(predict.items()):
        true = grid[k[0]][k[1]]
        print k, true, v


"""




test this. use the win percentages from MM10 grid.json to establish
'true' win percentages, run a simulation and see what falls out

Ok, I'm happy enough with the chooser. Now let's talk about this grid.


win prediction:
1.0 == I always win
0.0 == I always lose

do a fitness proportional selection for a partner
with f = spread_factor - abs(0.5 - WP)

0.5 <= spread_factor <= 1.0


archiver needs to update WP with every completed game. the winner needs to
have his win percentage increased against the guy he beat, with the amount
increased proportional to how small WP was. he can also have his WP increased
for everyone else, but probably with a smaller proportion. the loser needs
the same actions performed to his WP factors.

So we've got alpha_1, which is the factor by which the WP is changed in the
entry for the loser, and alpha_2, which is the factor by which the WP is
changed for everyone else



schedule most needy client

"""


###############################################
### stochastic_universal_sampling
###
### @description select n members of a population, with probability of
###              selection proportional to fitness
###
### Precondition:  None
### Postcondition: None
###
### @param population: the population of eligibles
### @param n: the number of selectees required
### @param fitness: a function that quantifies
###                 the value of an individual
###
### @return a list of selectees of length n
###
### @limitations all fitnesses must be non-negative
###############################################
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



"""


push to git during tournaments
We can fix this. There is a technical reason why we need to turn off git during
tournaments, but it's not insurmountable. We'll fix it.


fix the chess arena, megaminer seems to be fine
It's the same arena. A Bad Thing happened the day before megaminer, and we
had to scramble like crazy to ensure megaminer happened at all. Our manpower
pool is extremely small, so chess had to wait until after MegaMiner was over
before it could be repaired.

filtering
visualizer linked to a feed that serves up your gamelogs

better tournament structure, round robin suggested


game injection
Arena devs can inject games for you, in exchange for minor favors.

bracket displayed on screen


final 4 of Global Division
"""

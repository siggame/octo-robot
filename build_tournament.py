#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Some magic to get a standalone python program hooked in to django
import sys
sys.path = ['/srv/', '/srv/uard/'] + sys.path

from django.core.management import setup_environ
import settings

setup_environ(settings)

# Non-Django 3rd Party Imports
from time import sleep
import beanstalkc
import random

# My Imports
from thunderdome.models import Client, Game, GameData, Match

### assign seeds
clients = list(Client.objects.all())
clients.sort(reverse = True, key = lambda x: x.fitness())
i = 1
for client in clients:
    client.seed = i
    client.save()
    i += 1

### clear old stuff
print "clearing old matches"
for match in Match.objects.all():
    match.delete()
    
print "clearing old tournament games"
for game in Game.objects.filter(tournament=True):
    game.delete()

print "clearing old unclaimed games"
for game in Game.objects.filter(claimed=False):
    game.delete()

    
### build brackets
a = Match.objects.create()
a.p0 = Client.objects.get(seed=1)
a.p1 = Client.objects.get(seed=8)
a.save()

b = Match.objects.create()
b.p0 = Client.objects.get(seed=4)
b.p1 = Client.objects.get(seed=5)
b.save()

c = Match.objects.create()
c.p0 = Client.objects.get(seed=2)
c.p1 = Client.objects.get(seed=7)
c.save()

d = Match.objects.create()
d.p0 = Client.objects.get(seed=3)
d.p1 = Client.objects.get(seed=6)
d.save()

e = Match.objects.create()
e.father = a
e.mother = b
e.save()

f = Match.objects.create()
f.father = c
f.mother = d
f.save()

g = Match.objects.create()
g.father = e
g.mother = f
g.save()

h = Match.objects.create()
h.father_type = 'lose'
h.father = a
h.mother_type = 'lose'
h.mother = b
h.save()

i = Match.objects.create()
i.father_type = 'lose'
i.father = c
i.mother_type = 'lose'
i.mother = d
i.save()

j = Match.objects.create()
j.father = h
j.mother = i
j.save()

k = Match.objects.create()
k.father_type = 'lose'
k.father = e
k.mother_type = 'lose'
k.mother = f
k.save()

m = Match.objects.create()
m.father = g
m.mother = j
m.save()

n = Match.objects.create()
n.father = k
n.mother_type = 'lose'
n.mother = g
n.save()

p = Match.objects.create()
p.father = n
p.mother_type = 'lose'
p.mother = m
p.save()

q = Match.objects.create()
q.father = m
q.mother = p
q.save()

r = Match.objects.create()
r.father = q
r.mother_type = 'lose'
r.mother = q
r.root = True
r.save()

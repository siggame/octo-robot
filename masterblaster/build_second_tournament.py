#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####


TOURNEY_NUMBER = 1234

# My Imports
import bootstrap
from thunderdome.models import Client, Game, Match
from seeder import seed

#seed()

print "claiming all old tournament games"
for game in Game.objects.filter(tournament=True):
    game.claimed = True
    game.save()


try:
  c = Client.objects.get(name='bye')
except:
  Client(name='bye').save()


def seed_or_bye(n):
    try:
        result = Client.objects.get(seed=n)
    except:
        result = Client.objects.get(name='bye')
    return result

### single elim bracket
a = Match.objects.create()
a.p0 = seed_or_bye(1)
a.p1 = seed_or_bye(32)
a.tournament = TOURNEY_NUMBER
a.save()

b = Match.objects.create()
b.p0 = seed_or_bye(16)
b.p1 = seed_or_bye(17)
b.tournament = TOURNEY_NUMBER
b.save()

c = Match.objects.create()
c.p0 = seed_or_bye(8)
c.p1 = seed_or_bye(25)
c.tournament = TOURNEY_NUMBER
c.save()

d = Match.objects.create()
d.p0 = seed_or_bye(9)
d.p1 = seed_or_bye(24)
d.tournament = TOURNEY_NUMBER
d.save()

e = Match.objects.create()
e.p0 = seed_or_bye(4)
e.p1 = seed_or_bye(29)
e.tournament = TOURNEY_NUMBER
e.save()

f = Match.objects.create()
f.p0 = seed_or_bye(13)
f.p1 = seed_or_bye(20)
f.tournament = TOURNEY_NUMBER
f.save()

g = Match.objects.create()
g.p0 = seed_or_bye(5)
g.p1 = seed_or_bye(28)
g.tournament = TOURNEY_NUMBER
g.save()

h = Match.objects.create()
h.p0 = seed_or_bye(12)
h.p1 = seed_or_bye(21)
h.tournament = TOURNEY_NUMBER
h.save()

i = Match.objects.create()
i.p0 = seed_or_bye(2)
i.p1 = seed_or_bye(31)
i.tournament = TOURNEY_NUMBER
i.save()

j = Match.objects.create()
j.p0 = seed_or_bye(15)
j.p1 = seed_or_bye(18)
j.tournament = TOURNEY_NUMBER
j.save()

k = Match.objects.create()
k.p0 = seed_or_bye(7)
k.p1 = seed_or_bye(26)
k.tournament = TOURNEY_NUMBER
k.save()

l = Match.objects.create()
l.p0 = seed_or_bye(10)
l.p1 = seed_or_bye(23)
l.tournament = TOURNEY_NUMBER
l.save()

m = Match.objects.create()
m.p0 = seed_or_bye(3)
m.p1 = seed_or_bye(30)
m.tournament = TOURNEY_NUMBER
m.save()

n = Match.objects.create()
n.p0 = seed_or_bye(14)
n.p1 = seed_or_bye(19)
n.tournament = TOURNEY_NUMBER
n.save()

o = Match.objects.create()
o.p0 = seed_or_bye(6)
o.p1 = seed_or_bye(27)
o.tournament = TOURNEY_NUMBER
o.save()

p = Match.objects.create()
p.p0 = seed_or_bye(11)
p.p1 = seed_or_bye(22)
p.tournament = TOURNEY_NUMBER
p.save()


q = Match.objects.create()
q.father = a
q.mother = b
q.tournament = TOURNEY_NUMBER
q.save()

r = Match.objects.create()
r.father = c
r.mother = d
r.tournament = TOURNEY_NUMBER
r.save()

s = Match.objects.create()
s.father = e
s.mother = f
s.tournament = TOURNEY_NUMBER
s.save()

t = Match.objects.create()
t.father = g
t.mother = h
t.tournament = TOURNEY_NUMBER
t.save()

u = Match.objects.create()
u.father = i
u.mother = j
u.tournament = TOURNEY_NUMBER
u.save()

v = Match.objects.create()
v.father = k
v.mother = l
v.tournament = TOURNEY_NUMBER
v.save()

w = Match.objects.create()
w.father = m
w.mother = n
w.tournament = TOURNEY_NUMBER
w.save()

x = Match.objects.create()
x.father = o
x.mother = p
x.tournament = TOURNEY_NUMBER
x.save()


y = Match.objects.create()
y.father = q
y.mother = r
y.tournament = TOURNEY_NUMBER
y.save()

z = Match.objects.create()
z.father = s
z.mother = t
z.tournament = TOURNEY_NUMBER
z.save()

aa = Match.objects.create()
aa.father = u
aa.mother = v
aa.tournament = TOURNEY_NUMBER
aa.save()

ab = Match.objects.create()
ab.father = w
ab.mother = x
ab.tournament = TOURNEY_NUMBER
ab.save()


ac = Match.objects.create()
ac.father = y
ac.mother = z
ac.tournament = TOURNEY_NUMBER
ac.save()

ad = Match.objects.create()
ad.father = aa
ad.mother = ab
ad.tournament = TOURNEY_NUMBER
ad.save()


ae = Match.objects.create() # 31
ae.father = ac
ae.mother = ad
ae.tournament = TOURNEY_NUMBER
ae.save()


### double elim bracket
ba = Match.objects.create() #32
ba.father_type = 'lose'
ba.mother_type = 'lose'
ba.father = a
ba.mother = b
ba.tournament = TOURNEY_NUMBER
ba.save()

bb = Match.objects.create()
bb.father_type = 'lose'
bb.mother_type = 'lose'
bb.father = c
bb.mother = d
bb.tournament = TOURNEY_NUMBER
bb.save()

bc = Match.objects.create()
bc.father_type = 'lose'
bc.mother_type = 'lose'
bc.father = e
bc.mother = f
bc.tournament = TOURNEY_NUMBER
bc.save()

bd = Match.objects.create()
bd.father_type = 'lose'
bd.mother_type = 'lose'
bd.father = g
bd.mother = h
bd.tournament = TOURNEY_NUMBER
bd.save()

be = Match.objects.create()
be.father_type = 'lose'
be.mother_type = 'lose'
be.father = i
be.mother = j
be.tournament = TOURNEY_NUMBER
be.save()

bf = Match.objects.create()
bf.father_type = 'lose'
bf.mother_type = 'lose'
bf.father = k
bf.mother = l
bf.tournament = TOURNEY_NUMBER
bf.save()

bg = Match.objects.create()
bg.father_type = 'lose'
bg.mother_type = 'lose'
bg.father = m
bg.mother = n
bg.tournament = TOURNEY_NUMBER
bg.save()

bh = Match.objects.create()
bh.father_type = 'lose'
bh.mother_type = 'lose'
bh.father = o
bh.mother = p
bh.tournament = TOURNEY_NUMBER
bh.save()


bi = Match.objects.create() #40
bi.father = ba
bi.mother = bb
bi.tournament = TOURNEY_NUMBER
bi.save()

bj = Match.objects.create()
bj.father = bc
bj.mother = bd
bj.tournament = TOURNEY_NUMBER
bj.save()

bk = Match.objects.create()
bk.father = be
bk.mother = bf
bk.tournament = TOURNEY_NUMBER
bk.save()

bl = Match.objects.create()
bl.father = bg
bl.mother = bh
bl.tournament = TOURNEY_NUMBER
bl.save()


bm = Match.objects.create() #44
bm.father = bi
bm.mother = bj
bm.tournament = TOURNEY_NUMBER
bm.save()

bn = Match.objects.create()
bn.father = bk
bn.mother = bl
bn.tournament = TOURNEY_NUMBER
bn.save()

bo = Match.objects.create() #46
bo.father = bm
bo.mother = bn
bo.tournament = TOURNEY_NUMBER
bo.save()


ca = Match.objects.create() #47
ca.father_type = 'lose'
ca.mother_type = 'lose'
ca.father = q
ca.mother = r
ca.tournament = TOURNEY_NUMBER
ca.save()

cb = Match.objects.create()
cb.father_type = 'lose'
cb.mother_type = 'lose'
cb.father = s
cb.mother = t
cb.tournament = TOURNEY_NUMBER
cb.save()

cc = Match.objects.create()
cc.father_type = 'lose'
cc.mother_type = 'lose'
cc.father = u
cc.mother = v
cc.tournament = TOURNEY_NUMBER
cc.save()

cd = Match.objects.create()
cd.father_type = 'lose'
cd.mother_type = 'lose'
cd.father = w
cd.mother = x
cd.tournament = TOURNEY_NUMBER
cd.save()

ce = Match.objects.create() #51
ce.father = ca
ce.mother = cb
ce.tournament = TOURNEY_NUMBER
ce.save()

cf = Match.objects.create() #52
cf.father = cc
cf.mother = cd
cf.tournament = TOURNEY_NUMBER
cf.save()

cg = Match.objects.create() #53
cg.father = ce
cg.mother = cf
cg.tournament = TOURNEY_NUMBER
cg.save()

da = Match.objects.create() #54
da.father_type = 'lose'
da.mother_type = 'lose'
da.father = y
da.mother = z
da.tournament = TOURNEY_NUMBER
da.save()

db = Match.objects.create()
db.father_type = 'lose'
db.mother_type = 'lose'
db.father = aa
db.mother = ab
db.tournament = TOURNEY_NUMBER
db.save()


dc = Match.objects.create() #56
dc.father = da
dc.mother = db
dc.tournament = TOURNEY_NUMBER
dc.save()


ea = Match.objects.create() #57
ea.father_type = 'lose'
ea.mother_type = 'lose'
ea.father = ac
ea.mother = ad
ea.tournament = TOURNEY_NUMBER
ea.save()


fa = Match.objects.create() #59
fa.father = bo
fa.mother = cg
fa.tournament = TOURNEY_NUMBER
fa.save()

fb = Match.objects.create() #58 (yes I know)
fb.father = dc
fb.mother = ea
fb.tournament = TOURNEY_NUMBER
fb.save()

fc = Match.objects.create() #60
fc.father = fa
fc.mother = fb
fc.tournament = TOURNEY_NUMBER
fc.save()

fd = Match.objects.create() #61
fd.father = fc
fd.mother_type = 'lose'
fd.mother = ae
fd.tournament = TOURNEY_NUMBER
fd.save()


### triple elim bracket (ugh)
ga = Match.objects.create() #62
ga.father_type = 'lose'
ga.mother_type = 'lose'
ga.father = ba
ga.mother = bb
ga.tournament = TOURNEY_NUMBER
ga.save()

gb = Match.objects.create()
gb.father_type = 'lose'
gb.mother_type = 'lose'
gb.father = bc
gb.mother = bd
gb.tournament = TOURNEY_NUMBER
gb.save()

gc = Match.objects.create()
gc.father_type = 'lose'
gc.mother_type = 'lose'
gc.father = be
gc.mother = bf
gc.tournament = TOURNEY_NUMBER
gc.save()

gd = Match.objects.create()
gd.father_type = 'lose'
gd.mother_type = 'lose'
gd.father = bg
gd.mother = bh
gd.tournament = TOURNEY_NUMBER
gd.save()

ge = Match.objects.create()
ge.father = ga
ge.mother = gb
ge.tournament = TOURNEY_NUMBER
ge.save()

gf = Match.objects.create()
gf.father = gc
gf.mother = gd
gf.tournament = TOURNEY_NUMBER
gf.save()

gg = Match.objects.create() #68
gg.father = ge
gg.mother = gf
gg.tournament = TOURNEY_NUMBER
gg.save()

gh = Match.objects.create() #74
gh.father = gg
gh.mother_type = 'lose'
gh.mother = bo
gh.tournament = TOURNEY_NUMBER
gh.save()


gi = Match.objects.create() #69
gi.father_type = 'lose'
gi.mother_type = 'lose'
gi.father = bi
gi.mother = bj
gi.tournament = TOURNEY_NUMBER
gi.save()

gj = Match.objects.create() #70
gj.father_type = 'lose'
gj.mother_type = 'lose'
gj.father = bk
gj.mother = bl
gj.tournament = TOURNEY_NUMBER
gj.save()

gk = Match.objects.create() #71
gk.father = gi
gk.mother = gj
gk.tournament = TOURNEY_NUMBER
gk.save()

gl = Match.objects.create() #72
gl.father_type = 'lose'
gl.mother_type = 'lose'
gl.father = bm
gl.mother = bn
gl.tournament = TOURNEY_NUMBER
gl.save()

gm = Match.objects.create() #73
gm.father = gk
gm.mother = gl
gm.tournament = TOURNEY_NUMBER
gm.save()

gn = Match.objects.create() #75
gn.father = gh
gn.mother = gm
gn.tournament = TOURNEY_NUMBER
gn.save()

go = Match.objects.create() #76
go.father_type = 'lose'
go.mother_type = 'lose'
go.father = fb
go.mother = fa
go.tournament = TOURNEY_NUMBER
go.save()

gp = Match.objects.create() #86 (yes I know)
gp.father = gn
gp.mother = go
gp.tournament = TOURNEY_NUMBER
gp.save()


ha = Match.objects.create() #77
ha.father_type = 'lose'
ha.mother_type = 'lose'
ha.father = ca
ha.mother = cb
ha.tournament = TOURNEY_NUMBER
ha.save()

hb = Match.objects.create() #78
hb.father_type = 'lose'
hb.mother_type = 'lose'
hb.father = cc
hb.mother = cd
hb.tournament = TOURNEY_NUMBER
hb.save()

hc = Match.objects.create() #79
hc.father = ha
hc.mother = hb
hc.tournament = TOURNEY_NUMBER
hc.save()

hd = Match.objects.create() #80
hd.father_type = 'lose'
hd.mother_type = 'lose'
hd.father = ce
hd.mother = cf
hd.tournament = TOURNEY_NUMBER
hd.save()

he = Match.objects.create() #81
he.father = hc
he.mother = hd
he.tournament = TOURNEY_NUMBER
he.save()

hf = Match.objects.create() #82
hf.father = he
hf.mother_type = 'lose'
hf.mother = cg
hf.tournament = TOURNEY_NUMBER
hf.save()

ia = Match.objects.create() #83
ia.father_type = 'lose'
ia.mother_type = 'lose'
ia.father = da
ia.mother = db
ia.tournament = TOURNEY_NUMBER
ia.save()


ib = Match.objects.create() #84
ib.father = ia
ib.mother_type = 'lose'
ib.mother = dc
ib.tournament = TOURNEY_NUMBER
ib.save()

ic = Match.objects.create() #85
ic.father = ib
ic.mother_type = 'lose'
ic.mother = ea
ic.tournament = TOURNEY_NUMBER
ic.save()


ja = Match.objects.create() #87
ja.father = hf
ja.mother = ic
ja.tournament = TOURNEY_NUMBER
ja.save()

jb = Match.objects.create() #88
jb.father = gp
jb.mother = ja
jb.tournament = TOURNEY_NUMBER
jb.save()

jc = Match.objects.create() #89
jc.father = jb
jc.mother_type = 'lose'
jc.mother = fc
jc.tournament = TOURNEY_NUMBER
jc.save()

jd = Match.objects.create() #90
jd.father = jc
jd.mother_type = 'lose'
jd.mother = fd
jd.tournament = TOURNEY_NUMBER
jd.save()

### championships
ka = Match.objects.create() #91
ka.father = fd
ka.mother = jd
ka.tournament = TOURNEY_NUMBER
ka.save()

kb = Match.objects.create() #92
kb.father = ka
kb.mother_type = 'lose'
kb.mother = ka
kb.tournament = TOURNEY_NUMBER
kb.save()

kc = Match.objects.create() #93
kc.father = ae
kc.mother = kb
kc.tournament = TOURNEY_NUMBER
kc.save()

kd = Match.objects.create() #94
kd.father = kc
kd.mother_type = 'lose'
kd.mother = kc
kd.tournament = TOURNEY_NUMBER
kd.save()

ke = Match.objects.create() #95
ke.father = kd
ke.mother_type = 'lose'
ke.mother = kd
ke.root = True
ke.tournament = TOURNEY_NUMBER
ke.save()

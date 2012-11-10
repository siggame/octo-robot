#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####


# My Imports
import bootstrap
from thunderdome.models import Client, Game, Match
from seeder import seed

seed()

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
a.save()

b = Match.objects.create()
b.p0 = seed_or_bye(16)
b.p1 = seed_or_bye(17)
b.save()

c = Match.objects.create()
c.p0 = seed_or_bye(8)
c.p1 = seed_or_bye(25)
c.save()

d = Match.objects.create()
d.p0 = seed_or_bye(9)
d.p1 = seed_or_bye(24)
d.save()

e = Match.objects.create()
e.p0 = seed_or_bye(4)
e.p1 = seed_or_bye(29)
e.save()

f = Match.objects.create()
f.p0 = seed_or_bye(13)
f.p1 = seed_or_bye(20)
f.save()

g = Match.objects.create()
g.p0 = seed_or_bye(5)
g.p1 = seed_or_bye(28)
g.save()

h = Match.objects.create()
h.p0 = seed_or_bye(12)
h.p1 = seed_or_bye(21)
h.save()

i = Match.objects.create()
i.p0 = seed_or_bye(2)
i.p1 = seed_or_bye(31)
i.save()

j = Match.objects.create()
j.p0 = seed_or_bye(15)
j.p1 = seed_or_bye(18)
j.save()

k = Match.objects.create()
k.p0 = seed_or_bye(7)
k.p1 = seed_or_bye(26)
k.save()

l = Match.objects.create()
l.p0 = seed_or_bye(10)
l.p1 = seed_or_bye(23)
l.save()

m = Match.objects.create()
m.p0 = seed_or_bye(3)
m.p1 = seed_or_bye(30)
m.save()

n = Match.objects.create()
n.p0 = seed_or_bye(14)
n.p1 = seed_or_bye(19)
n.save()

o = Match.objects.create()
o.p0 = seed_or_bye(6)
o.p1 = seed_or_bye(27)
o.save()

p = Match.objects.create()
p.p0 = seed_or_bye(11)
p.p1 = seed_or_bye(22)
p.save()


q = Match.objects.create()
q.father = a
q.mother = b
q.save()

r = Match.objects.create()
r.father = c
r.mother = d
r.save()

s = Match.objects.create()
s.father = e
s.mother = f
s.save()

t = Match.objects.create()
t.father = g
t.mother = h
t.save()

u = Match.objects.create()
u.father = i
u.mother = j
u.save()

v = Match.objects.create()
v.father = k
v.mother = l
v.save()

w = Match.objects.create()
w.father = m
w.mother = n
w.save()

x = Match.objects.create()
x.father = o
x.mother = p
x.save()


y = Match.objects.create()
y.father = q
y.mother = r
y.save()

z = Match.objects.create()
z.father = s
z.mother = t
z.save()

aa = Match.objects.create()
aa.father = u
aa.mother = v
aa.save()

ab = Match.objects.create()
ab.father = w
ab.mother = x
ab.save()


ac = Match.objects.create()
ac.father = y
ac.mother = z
ac.save()

ad = Match.objects.create()
ad.father = aa
ad.mother = ab
ad.save()


ae = Match.objects.create() # 31
ae.father = ac
ae.mother = ad
ae.save()


### double elim bracket
ba = Match.objects.create() #32
ba.father_type = 'lose'
ba.mother_type = 'lose'
ba.father = a
ba.mother = b
ba.save()

bb = Match.objects.create()
bb.father_type = 'lose'
bb.mother_type = 'lose'
bb.father = c
bb.mother = d
bb.save()

bc = Match.objects.create()
bc.father_type = 'lose'
bc.mother_type = 'lose'
bc.father = e
bc.mother = f
bc.save()

bd = Match.objects.create()
bd.father_type = 'lose'
bd.mother_type = 'lose'
bd.father = g
bd.mother = h
bd.save()

be = Match.objects.create()
be.father_type = 'lose'
be.mother_type = 'lose'
be.father = i
be.mother = j
be.save()

bf = Match.objects.create()
bf.father_type = 'lose'
bf.mother_type = 'lose'
bf.father = k
bf.mother = l
bf.save()

bg = Match.objects.create()
bg.father_type = 'lose'
bg.mother_type = 'lose'
bg.father = m
bg.mother = n
bg.save()

bh = Match.objects.create()
bh.father_type = 'lose'
bh.mother_type = 'lose'
bh.father = o
bh.mother = p
bh.save()


bi = Match.objects.create() #40
bi.father = ba
bi.mother = bb
bi.save()

bj = Match.objects.create()
bj.father = bc
bj.mother = bd
bj.save()

bk = Match.objects.create()
bk.father = be
bk.mother = bf
bk.save()

bl = Match.objects.create()
bl.father = bg
bl.mother = bh
bl.save()


bm = Match.objects.create() #44
bm.father = bi
bm.mother = bj
bm.save()

bn = Match.objects.create()
bn.father = bk
bn.mother = bl
bn.save()

bo = Match.objects.create() #46
bo.father = bm
bo.mother = bn
bo.save()


ca = Match.objects.create() #47
ca.father_type = 'lose'
ca.mother_type = 'lose'
ca.father = q
ca.mother = r
ca.save()

cb = Match.objects.create()
cb.father_type = 'lose'
cb.mother_type = 'lose'
cb.father = s
cb.mother = t
cb.save()

cc = Match.objects.create()
cc.father_type = 'lose'
cc.mother_type = 'lose'
cc.father = u
cc.mother = v
cc.save()

cd = Match.objects.create()
cd.father_type = 'lose'
cd.mother_type = 'lose'
cd.father = w
cd.mother = x
cd.save()

ce = Match.objects.create() #51
ce.father = ca
ce.mother = cb
ce.save()

cf = Match.objects.create() #52
cf.father = cc
cf.mother = cd
cf.save()

cg = Match.objects.create() #53
cg.father = ce
cg.mother = cf
cg.save()

da = Match.objects.create() #54
da.father_type = 'lose'
da.mother_type = 'lose'
da.father = y
da.mother = z
da.save()

db = Match.objects.create()
db.father_type = 'lose'
db.mother_type = 'lose'
db.father = aa
db.mother = ab
db.save()


dc = Match.objects.create() #56
dc.father = da
dc.mother = db
dc.save()


ea = Match.objects.create() #57
ea.father_type = 'lose'
ea.mother_type = 'lose'
ea.father = ac
ea.mother = ad
ea.save()


fa = Match.objects.create() #59
fa.father = bo
fa.mother = cg
fa.save()

fb = Match.objects.create() #58 (yes I know)
fb.father = dc
fb.mother = ea
fb.save()

fc = Match.objects.create() #60
fc.father = fa
fc.mother = fb
fc.save()

fd = Match.objects.create() #61
fd.father = fc
fd.mother_type = 'lose'
fd.mother = ae
fd.save()


### triple elim bracket (ugh)
ga = Match.objects.create() #62
ga.father_type = 'lose'
ga.mother_type = 'lose'
ga.father = ba
ga.mother = bb
ga.save()

gb = Match.objects.create()
gb.father_type = 'lose'
gb.mother_type = 'lose'
gb.father = bc
gb.mother = bd
gb.save()

gc = Match.objects.create()
gc.father_type = 'lose'
gc.mother_type = 'lose'
gc.father = be
gc.mother = bf
gc.save()

gd = Match.objects.create()
gd.father_type = 'lose'
gd.mother_type = 'lose'
gd.father = bg
gd.mother = bh
gd.save()

ge = Match.objects.create()
ge.father = ga
ge.mother = gb
ge.save()

gf = Match.objects.create()
gf.father = gc
gf.mother = gd
gf.save()

gg = Match.objects.create() #68
gg.father = ge
gg.mother = gf
gg.save()

gh = Match.objects.create() #74
gh.father = gg
gh.mother_type = 'lose'
gh.mother = bo
gh.save()


gi = Match.objects.create() #69
gi.father_type = 'lose'
gi.mother_type = 'lose'
gi.father = bi
gi.mother = bj
gi.save()

gj = Match.objects.create() #70
gj.father_type = 'lose'
gj.mother_type = 'lose'
gj.father = bk
gj.mother = bl
gj.save()

gk = Match.objects.create() #71
gk.father = gi
gk.mother = gj
gk.save()

gl = Match.objects.create() #72
gl.father_type = 'lose'
gl.mother_type = 'lose'
gl.father = bm
gl.mother = bn
gl.save()

gm = Match.objects.create() #73
gm.father = gk
gm.mother = gl
gm.save()

gn = Match.objects.create() #75
gn.father = gh
gn.mother = gm
gn.save()

go = Match.objects.create() #76
go.father_type = 'lose'
go.mother_type = 'lose'
go.father = fb
go.mother = fa
go.save()

gp = Match.objects.create() #86 (yes I know)
gp.father = gn
gp.mother = go
gp.save()


ha = Match.objects.create() #77
ha.father_type = 'lose'
ha.mother_type = 'lose'
ha.father = ca
ha.mother = cb
ha.save()

hb = Match.objects.create() #78
hb.father_type = 'lose'
hb.mother_type = 'lose'
hb.father = cc
hb.mother = cd
hb.save()

hc = Match.objects.create() #79
hc.father = ha
hc.mother = hb
hc.save()

hd = Match.objects.create() #80
hd.father_type = 'lose'
hd.mother_type = 'lose'
hd.father = ce
hd.mother = cf
hd.save()

he = Match.objects.create() #81
he.father = hc
he.mother = hd
he.save()

hf = Match.objects.create() #82
hf.father = he
hf.mother_type = 'lose'
hf.mother = cg
hf.save()

ia = Match.objects.create() #83
ia.father_type = 'lose'
ia.mother_type = 'lose'
ia.father = da
ia.mother = db
ia.save()


ib = Match.objects.create() #84
ib.father = ia
ib.mother_type = 'lose'
ib.mother = dc
ib.save()

ic = Match.objects.create() #85
ic.father = ib
ic.mother_type = 'lose'
ic.mother = ea
ic.save()


ja = Match.objects.create() #87
ja.father = hf
ja.mother = ic
ja.save()

jb = Match.objects.create() #88
jb.father = gp
jb.mother = ja
jb.save()

jc = Match.objects.create() #89
jc.father = jb
jc.mother_type = 'lose'
jc.mother = fc
jc.save()

jd = Match.objects.create() #90
jd.father = jc
jd.mother_type = 'lose'
jd.mother = fd
jd.save()

### championships
ka = Match.objects.create() #91
ka.father = fd
ka.mother = jd
ka.save()

kb = Match.objects.create() #92
kb.father = ka
kb.mother_type = 'lose'
kb.mother = ka
kb.save()

kc = Match.objects.create() #93
kc.father = ae
kc.mother = kb
kc.save()

kd = Match.objects.create() #94
kd.father = kc
kd.mother_type = 'lose'
kd.mother = kc
kd.save()

ke = Match.objects.create() #95
ke.father = kd
ke.mother_type = 'lose'
ke.mother = kd
ke.root = True
ke.save()

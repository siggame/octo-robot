#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

seeds = None


class Match(object):
    def __init__(self):
        self.p1 = None
        self.p0 = None
        self.mother = None
        self.father = None
        self.winner = None
        self.loser = None
        self.losses_to_eliminate = 3
        self.wins_to_win = 4
        self.father_type = 'win'
        self.mother_type = 'win'
        self.status = 'Waiting'
        self.root = False


def seed_or_bye(i):
    return seeds.get(str(i), 'bye')


def build_it(s):
 global seeds
 seeds = s
 ### single elim bracket
 a = Match()
 a.p0 = seed_or_bye(1)
 a.p1 = seed_or_bye(32)

 b = Match()
 b.p0 = seed_or_bye(16)
 b.p1 = seed_or_bye(17)

 c = Match()
 c.p0 = seed_or_bye(8)
 c.p1 = seed_or_bye(25)

 d = Match()
 d.p0 = seed_or_bye(9)
 d.p1 = seed_or_bye(24)

 e = Match()
 e.p0 = seed_or_bye(4)
 e.p1 = seed_or_bye(29)

 f = Match()
 f.p0 = seed_or_bye(13)
 f.p1 = seed_or_bye(20)

 g = Match()
 g.p0 = seed_or_bye(5)
 g.p1 = seed_or_bye(28)

 h = Match()
 h.p0 = seed_or_bye(12)
 h.p1 = seed_or_bye(21)

 i = Match()
 i.p0 = seed_or_bye(2)
 i.p1 = seed_or_bye(31)

 j = Match()
 j.p0 = seed_or_bye(15)
 j.p1 = seed_or_bye(18)

 k = Match()
 k.p0 = seed_or_bye(7)
 k.p1 = seed_or_bye(26)

 l = Match()
 l.p0 = seed_or_bye(10)
 l.p1 = seed_or_bye(23)

 m = Match()
 m.p0 = seed_or_bye(3)
 m.p1 = seed_or_bye(30)

 n = Match()
 n.p0 = seed_or_bye(14)
 n.p1 = seed_or_bye(19)

 o = Match()
 o.p0 = seed_or_bye(6)
 o.p1 = seed_or_bye(27)

 p = Match()
 p.p0 = seed_or_bye(11)
 p.p1 = seed_or_bye(22)

 q = Match()
 q.father = a
 q.mother = b

 r = Match()
 r.father = c
 r.mother = d

 s = Match()
 s.father = e
 s.mother = f

 t = Match()
 t.father = g
 t.mother = h

 u = Match()
 u.father = i
 u.mother = j

 v = Match()
 v.father = k
 v.mother = l

 w = Match()
 w.father = m
 w.mother = n

 x = Match()
 x.father = o
 x.mother = p

 y = Match()
 y.father = q
 y.mother = r

 z = Match()
 z.father = s
 z.mother = t

 aa = Match()
 aa.father = u
 aa.mother = v

 ab = Match()
 ab.father = w
 ab.mother = x


 ac = Match()
 ac.father = y
 ac.mother = z

 ad = Match()
 ad.father = aa
 ad.mother = ab

 ae = Match() # 31
 ae.father = ac
 ae.mother = ad
 ae.root = True

 return ae

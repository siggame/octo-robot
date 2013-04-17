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

 ### double elim bracket
 ba = Match() #32
 ba.father_type = 'lose'
 ba.mother_type = 'lose'
 ba.father = a
 ba.mother = b

 bb = Match()
 bb.father_type = 'lose'
 bb.mother_type = 'lose'
 bb.father = c
 bb.mother = d

 bc = Match()
 bc.father_type = 'lose'
 bc.mother_type = 'lose'
 bc.father = e
 bc.mother = f

 bd = Match()
 bd.father_type = 'lose'
 bd.mother_type = 'lose'
 bd.father = g
 bd.mother = h

 be = Match()
 be.father_type = 'lose'
 be.mother_type = 'lose'
 be.father = i
 be.mother = j

 bf = Match()
 bf.father_type = 'lose'
 bf.mother_type = 'lose'
 bf.father = k
 bf.mother = l

 bg = Match()
 bg.father_type = 'lose'
 bg.mother_type = 'lose'
 bg.father = m
 bg.mother = n

 bh = Match()
 bh.father_type = 'lose'
 bh.mother_type = 'lose'
 bh.father = o
 bh.mother = p


 bi = Match() #40
 bi.father = ba
 bi.mother = bb

 bj = Match()
 bj.father = bc
 bj.mother = bd

 bk = Match()
 bk.father = be
 bk.mother = bf

 bl = Match()
 bl.father = bg
 bl.mother = bh


 bm = Match() #44
 bm.father = bi
 bm.mother = bj

 bn = Match()
 bn.father = bk
 bn.mother = bl

 bo = Match() #46
 bo.father = bm
 bo.mother = bn

 ca = Match() #47
 ca.father_type = 'lose'
 ca.mother_type = 'lose'
 ca.father = q
 ca.mother = r

 cb = Match()
 cb.father_type = 'lose'
 cb.mother_type = 'lose'
 cb.father = s
 cb.mother = t

 cc = Match()
 cc.father_type = 'lose'
 cc.mother_type = 'lose'
 cc.father = u
 cc.mother = v

 cd = Match()
 cd.father_type = 'lose'
 cd.mother_type = 'lose'
 cd.father = w
 cd.mother = x

 ce = Match() #51
 ce.father = ca
 ce.mother = cb

 cf = Match() #52
 cf.father = cc
 cf.mother = cd

 cg = Match() #53
 cg.father = ce
 cg.mother = cf

 da = Match() #54
 da.father_type = 'lose'
 da.mother_type = 'lose'
 da.father = y
 da.mother = z

 db = Match()
 db.father_type = 'lose'
 db.mother_type = 'lose'
 db.father = aa
 db.mother = ab


 dc = Match() #56
 dc.father = da
 dc.mother = db


 ea = Match() #57
 ea.father_type = 'lose'
 ea.mother_type = 'lose'
 ea.father = ac
 ea.mother = ad

 fa = Match() #59
 fa.father = bo
 fa.mother = cg

 fb = Match() #58 (yes I know)
 fb.father = dc
 fb.mother = ea

 fc = Match() #60
 fc.father = fa
 fc.mother = fb

 fd = Match() #61
 fd.father = fc
 fd.mother_type = 'lose'
 fd.mother = ae

 ### triple elim bracket (ugh)
 ga = Match() #62
 ga.father_type = 'lose'
 ga.mother_type = 'lose'
 ga.father = ba
 ga.mother = bb

 gb = Match()
 gb.father_type = 'lose'
 gb.mother_type = 'lose'
 gb.father = bc
 gb.mother = bd

 gc = Match()
 gc.father_type = 'lose'
 gc.mother_type = 'lose'
 gc.father = be
 gc.mother = bf

 gd = Match()
 gd.father_type = 'lose'
 gd.mother_type = 'lose'
 gd.father = bg
 gd.mother = bh

 ge = Match()
 ge.father = ga
 ge.mother = gb

 gf = Match()
 gf.father = gc
 gf.mother = gd

 gg = Match() #68
 gg.father = ge
 gg.mother = gf

 gh = Match() #74
 gh.father = gg
 gh.mother_type = 'lose'
 gh.mother = bo

 gi = Match() #69
 gi.father_type = 'lose'
 gi.mother_type = 'lose'
 gi.father = bi
 gi.mother = bj

 gj = Match() #70
 gj.father_type = 'lose'
 gj.mother_type = 'lose'
 gj.father = bk
 gj.mother = bl

 gk = Match() #71
 gk.father = gi
 gk.mother = gj

 gl = Match() #72
 gl.father_type = 'lose'
 gl.mother_type = 'lose'
 gl.father = bm
 gl.mother = bn

 gm = Match() #73
 gm.father = gk
 gm.mother = gl

 gn = Match() #75
 gn.father = gh
 gn.mother = gm

 go = Match() #76
 go.father_type = 'lose'
 go.mother_type = 'lose'
 go.father = fb
 go.mother = fa

 gp = Match() #86 (yes I know)
 gp.father = gn
 gp.mother = go

 ha = Match() #77
 ha.father_type = 'lose'
 ha.mother_type = 'lose'
 ha.father = ca
 ha.mother = cb

 hb = Match() #78
 hb.father_type = 'lose'
 hb.mother_type = 'lose'
 hb.father = cc
 hb.mother = cd

 hc = Match() #79
 hc.father = ha
 hc.mother = hb

 hd = Match() #80
 hd.father_type = 'lose'
 hd.mother_type = 'lose'
 hd.father = ce
 hd.mother = cf

 he = Match() #81
 he.father = hc
 he.mother = hd

 hf = Match() #82
 hf.father = he
 hf.mother_type = 'lose'
 hf.mother = cg

 ia = Match() #83
 ia.father_type = 'lose'
 ia.mother_type = 'lose'
 ia.father = da
 ia.mother = db

 ib = Match() #84
 ib.father = ia
 ib.mother_type = 'lose'
 ib.mother = dc

 ic = Match() #85
 ic.father = ib
 ic.mother_type = 'lose'
 ic.mother = ea

 ja = Match() #87
 ja.father = hf
 ja.mother = ic

 jb = Match() #88
 jb.father = gp
 jb.mother = ja

 jc = Match() #89
 jc.father = jb
 jc.mother_type = 'lose'
 jc.mother = fc

 jd = Match() #90
 jd.father = jc
 jd.mother_type = 'lose'
 jd.mother = fd

 ### championships
 ka = Match() #91
 ka.father = fd
 ka.mother = jd

 kb = Match() #92
 kb.father = ka
 kb.mother_type = 'lose'
 kb.mother = ka

 kc = Match() #93
 kc.father = ae
 kc.mother = kb

 kd = Match() #94
 kd.father = kc
 kd.mother_type = 'lose'
 kd.mother = kc

 ke = Match() #95
 ke.father = kd
 ke.mother_type = 'lose'
 ke.mother = kd
 ke.root = True

 return ke

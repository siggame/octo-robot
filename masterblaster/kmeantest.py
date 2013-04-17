import bootstrap
from thunderdome.models import Game
from utilities import kmeans

k = Game.objects.all()

c = kmeans.obtain_clusters(k, 10)

for i in xrange(len(c)):
    print c[i].feature

for i in xrange(len(c)):
    print c[i].rating

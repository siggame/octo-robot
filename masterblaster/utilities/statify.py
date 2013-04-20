import bootstrap
import json
from thunderdome.models import Game
from utilities import kmeans, gamelog_regepars
import urllib
from bz2 import BZ2Decompressor

games = Game.objects.filter(status='Complete')

for i in games:
    data = json.loads(i.stats)

    gamelog_url = data['gamelog_url']
    k = urllib.urlopen(gamelog_url)
    gamelog = BZ2Decompressor().decompress(k.read())
    game_stats = gamelog_regepars.get_stats(gamelog)

    print 'new ratings ', game_stats
    data['rating_stats'] = game_stats
    i.stats = json.dumps(data)
    i.save()

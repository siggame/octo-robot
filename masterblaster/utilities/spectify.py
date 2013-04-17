import bootstrap
import json
from thunderdome.models import Game
from utilities import kmeans

tourn_games = Game.objects.filter(tournament=True)
games = Game.objects.filter(status='Complete').filter(tournament=False)
clusters = kmeans.obtain_clusters(games, 8)

for i in tourn_games:
    stats = json.loads(i.stats)
    tempP = kmeans.convert_to_point(i)
    spect_rating = kmeans.nearest_cluster_center(tempP, clusters)[2]
    print spect_rating
    stats['spect_rating'] = spect_rating
    i.stats = json.dumps(stats)
    i.save()

from thunderdome.models import Game
import json

def results():
    g = Game.objects.all()
    num_games = 0
    for i in g:
        if i.winner is not None and i.loser is not None:
            try:
                stats = json.loads(i.stats)
            except:
                continue
            print stats['clients'][0]['name'], "vs", stats['clients'][1]['name'], "winner:", i.winner.name
            num_games += 1
    print "num games", num_games

if __name__ == "__main__":
    results()

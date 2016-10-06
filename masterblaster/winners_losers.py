from thunderdome.models import Game
import json

def results():
    num_games = 0
    for i in Game.objects.all():
        if i.winner is not None and i.loser is not None:
            try:
                stats = json.loads(i.stats)
            except:
                continue
            print "Winner:", i.winner.name, "Loser:", i.loser.name
            num_games += 1
    print "num games", num_games

if __name__ == "__main__":
    results()

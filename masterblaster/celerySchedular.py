import random
import urllib
import json
import time

from thunderdome.config import game_name, req_queue_len
from thunderdome.models import Client

import time

from celeryglad.tasks import playgame

current_games = []

def main():
    while True:
        print "scheduling"
        while len(current_games) < 5:
            # playgame.apply_async(('o','t','4'))
            schedule_a_game()
        print "sleeping"
        time.sleep(2)
        
        
def schedule_a_game():
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))
    if len(clients) < 2:
        print "only", len(clients), "client in the arena"
        return
    worst_client = min(clients, key=lambda x : x.last_game())
    clients.remove(worst_client)
    partner = random.choice(clients)
    players = [worst_client, partner]
    random.shuffle(players)
    print "Scheduling game: ", players[0], "vs", players[1]
    current_games.append(playgame.apply_async((players[0], players[1], "Celery Scheduler")))
        
if __name__ == "__main__":
    main()

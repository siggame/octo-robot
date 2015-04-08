#### Window Swiss Scheduler
#### Golman's algorithm
#### Brandon Phelps's implmentation


import random
import time

import beanstalkc

from thunderdome.config import game_name, req_queue_len
from thunderdome.models import Client, Game
from thunderdome.sked import sked
from utilities.webinteraction import update_clients

from collections import defaultdict, deque
from math import log

uncompleted_games = []
score_window = defaultdict(deque)

def main():
    try:
        stalk = beanstalkc.Connection()
    except:
        raise Exception("Beanstalk Error: Possible that beanstalkd is not running")

    print game_name
    req_tube = "game-requests-%s" % game_name
    req_queue_len = 10
    stalk.use(req_tube)
    while True:
        stats = stalk.stats_tube(req_tube)
        if stats['current-jobs-ready'] < req_queue_len:
            update_clients()
            schedule_a_game(stalk)
        else:
            time.sleep(1)
    stalk.close()

def update_window(max_size):
    for g in list(uncompleted_games):
        game_data = Game.objects.get(pk=g.pk)
        if game_data.status == "Complete":
            uncompleted_games.remove(g)
            
            # Update the score windows for both teams, giving the winner a 1
            score_window[game_data.winner.name].append(1)
            print "Winner: ", game_data.winner.name, score_window[game_data.winner.name]
            shrink(game_data.winner.name, max_size)
            score_window[game_data.loser.name].append(0)
            print "Loser: ", game_data.loser.name, score_window[game_data.loser.name]
            shrink(game_data.loser.name, max_size)

        elif game_data.status == "Failed":
            uncompleted_games.remove(g)

def shrink(team, max_size):
    while len(score_window[team]) > max_size:
        score_window[team].popleft()

def score(team):
    if score_window[team]:
        # Average win rate
        return sum(score_window[team]) / float(len(score_window[team]))
    # Played no games, assume 0.5 average wins
    return 0.5

def schedule_a_game(stalk):
    clients = list(Client.objects.exclude(name='bye').filter(embargoed=False).filter(missing=False))
    if len(clients) < 2: # takes two to tango
        print "only", len(clients), "clients in the aren"
        return
    
    # Updated completed game information
    update_window(int(log(len(clients), 2) - 1))
    # update_window(10)
    #for i in clients:
    #    print i.name, score(i.name)
    
    # Find the lease recently played team
    least_recent = min(clients, key=lambda x: x.last_game())
    clients.remove(least_recent)
    
    # Find opponent who minimizes absolute difference in score
    target_score = score(least_recent.name)
    random.shuffle(clients)
    partner = min(clients, key=lambda client: abs(target_score - score(client.name)))
    
    # Shuffle player order and schedule the game
    players = [least_recent, partner]
    random.shuffle(players)
    uncompleted_games.append(sked(players[0], players[1], stalk, "Window Swiss Scheduler"))

if __name__ == "__main__":
    main()

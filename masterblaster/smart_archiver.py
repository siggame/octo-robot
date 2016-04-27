#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####


# Standard Imports
import time
import urllib
import math
import gzip
import os
import urllib2
from copy import copy
from multiprocessing import Process
from datetime import datetime, timedelta
from bz2 import BZ2Decompressor
from collections import defaultdict

# Non-Django 3rd Party Imports
import beanstalkc
import json

# My Imports
from thunderdome.config import game_name
from thunderdome.models import Client, Game, GameData, Referee
from thunderdome.models import WinRatePrediction


import django
django.setup()

#from datatizer import add_gamelog_data

#from thunderdome.loggly_logging import log
from gviz_api import DataTable

import settings

# Rating Imports
#from utilities import gamelog_regepars
#from utilities import kmeans

stalk = None
tourny_time = True 

games = Game.objects.filter(tournament=False).filter(status='Complete')


# will not be using k-means clustering this competition
#if tourny_time:
#    print "Generating Clusters"
#    clusters = kmeans.obtain_clusters(games, 8)

print "Thunder birds are a go go!"


def main():
    result_tube = "game-results-%s" % game_name
    #p = Process(target=processing)
    #p.start()

    #CALEB: I commented out the global here to see if that fixes the memory
    #  leak if everything breaks comment it back in
    global stalk
    stalk = beanstalkc.Connection()
    stalk.watch(result_tube)

    while True:
        job = stalk.reserve()
        request = json.loads(job.body)
        try:
            game = Game.objects.get(id=int(request['number']))
        except:
            job.delete()
            continue
        game.stats = job.body
        game.status = request['status']
        if game.status in ["Complete", "Failed"]:
            if 'gamelog_url' in request:
                game.gamelog_url = request['gamelog_url']
            if 'completed' in request:
                game.completed = request['completed']
                #process_game_stats(game)
            #Recompute the scoreboard and throughput
            game.tied = request['tied']
            if game.tied or game.status == 'Failed':
                try:
                    game.tie_reason = request['tie_reason']
                except:
                    print "Warning: Unable to read tie_reason for game", game
                count = 0
                for guy in request['clients']:
                    if count > 0:
                        print "vs.",
                    print guy['name'],
                    count += 1
                print ":", game.tie_reason
            else:
                game.win_reason = request['win_reason']
                game.lose_reason = request['lose_reason']
                print request['winner']['name'], "beat", request['loser']['name'], "because", game.win_reason
            handle_completion(request, game)
        game.save()
        job.delete()
        del job.conn
        del job
        (r, c) = Referee.objects.get_or_create(
            blaster_id=request['blaster_id'],
            referee_id=request['referee_id'],
            defaults={'started': datetime.utcnow(),
                      'last_update': datetime.utcnow()})
        r.last_update = datetime.utcnow()
        r.games.add(game)
        r.save()
        print "Game", request['number'], "status", request['status']
        request.update({'reporter': 'archiver'})
        #log.info(json.dumps(request))


def processing():
    while True:
        start = datetime.now()
        compute_throughput()
        compute_scoreboard()
        td = datetime.now()-start
        delay = max(td * 2, timedelta(seconds=30)).total_seconds()
        print "Next run in %s secs" % delay
        time.sleep(delay)


def process_game_stats(game):
    global clusters
    if game.status == "Complete":
        data = json.loads(game.stats)
        gamelogurl = game.gamelog_url
        with gzip.open(urllib.urlretrieve(gamelogurl), 'rb') as j:
            game_log = j.read()

        game_stats = gamelog_regepars.get_stats(game_log)
        print 'GAME STATS ', game_stats
        data['rating_stats'] = game_stats
        game.stats = json.dumps(data)
        game.save()
        if 'tournament' in data:
            tempPoint = kmeans.convert_to_point(game)
            rating = kmeans.nearest_cluster_center(tempPoint, clusters)[2]
            data['spect_rating'] = rating
            game.stats = json.dumps(data)
            game.save()


def compute_throughput():
    refs = Referee.objects.all().order_by('pk')
    if refs.count() == 0:
        return
    formatted = dict()
    earliest_start = min([ref.started for ref in refs])
    step = (datetime.utcnow()-earliest_start)/50
    step = max([step, timedelta(minutes=5)])
    interval = step*6
    period = datetime.utcnow()-earliest_start+interval
    print "Computing rate table p:%s s:%s i:%s" % (period, step, interval)
    for ref in refs:
        table = ref.rate_table(period, step, interval)
        for (t, v) in table:
            t = t.replace(second=0, microsecond=0)
            try:
                formatted[t].append(v)
            except KeyError:
                formatted[t] = [v]
    struct =[[k] + v for (k, v) in sorted(formatted.iteritems())]
    desc = [('Time', 'datetime')]
    desc += [('%s/%s' % (ref.blaster_id, ref.referee_id), 'number')
             for ref in refs]
    dt = DataTable(desc, struct)
    try:
        path = os.path.join(settings.STATIC_ROOT, 'throughput.js')
        f = open(path, 'w')
        f.write(dt.ToJSCode('data'))
        f.close()
    except IOError:
        print "Couldn't write throughput"
        pass
    print "Throughput chart computed!"


def compute_scoreboard():
    clients = Client.objects.exclude(current_version="")
    # Build the speedy lookup table
    grid = dict()
    wl = dict()
    for c1 in clients:
        grid[c1] = dict()
        for c2 in clients:
            grid[c1][c2] = 0

    for c1 in clients:
        for c2 in clients:
            grid[c1][c2] = c1.games_won.filter(loser=c2).count()

    for c1 in clients:
        wins = 0
        total = 0
        for c2 in clients:
            wins += grid[c1][c2]
            total += grid[c1][c2] + grid[c2][c1]
        if total > 0:
            wl[c1] = (wins*1.0)/total
        else:
            wl[c1] = 0.0

    # Sort the clients by winningness
    clients = list(clients)
    clients.sort(reverse=True, key=lambda x: x.fitness())

    client_link = "<a href='view_client/%s'>%s</a>"

    desc = [('vs', 'string')]
    desc += [('embargoed', 'boolean')]
    desc += [('Wins', 'number')]
    desc += [('PCT', 'number')]
    desc += [('Elo', 'number')]
    desc += [(client_link % (client.pk, client.name), 'string') for client in clients]

    struct = []

    for client1 in clients:
        tmp = [client_link % (client1.pk, client1.name), client1.embargoed]
        tmp2 = []
        total = 0
        for client2 in clients:
            link = "<a href='matchup/%svs%s'>%s</a>" % (client1.pk,
                                                        client2.pk,
                                                        grid[client1][client2])
            tmp2.append(link)
            total += grid[client1][client2]
        tmp.append(total)
        tmp.append(round(wl[client1], 4))
        tmp.append(client1.rating)
        tmp += tmp2
        struct.append(tmp)
    struct.sort(reverse=True, key=lambda x: x[4])

    dt = DataTable(desc, struct)
    try:
        f = open(os.path.join(settings.STATIC_ROOT, 'scoreboard.js'), 'w')
        static = """
        function drawScoreboardTable() {
        %s
        var options = {
            title: 'Competitor Overview',
            allowHtml: true,
        };
        var table = new google.visualization.Table(document.getElementById('scoreboard_table'));
        table.draw(data, options);
        }
        drawScoreboardTable();
        """
        f.write(static % dt.ToJSCode('data'))
        f.close()
    except IOError:
        print "Couldn't write scoreboard"
        pass
    print "Scoreboard Computed!"
    pass


def handle_completion(request, game):
    if 'winner' in request:
        game.winner = Client.objects.get(name=request['winner']['name'])
    if 'loser' in request:
        game.loser = Client.objects.get(name=request['loser']['name'])

    if 'winner' in request and 'loser' in request:
        assign_elo(game.winner, game.loser)
        adjust_win_rate(game.winner, game.loser)


    #add_gamelog_data(game)

    # increment winner and losers game played
    #for client in [game.winner, game.loser]:
    #    try:
    #        stats = json.loads(client.stats)
    #    except ValueError:
    #        stats = defaultdict(int)
    #    stats['games-played'] = stats['games-played'] + 1
    #    client.stats = json.dumps(stats)

    clidict = dict()
    for client in request['clients']:
        clidict[client['name']] = client
    for gd in GameData.objects.filter(game=game):
        if gd.client == game.winner:
            gd.won = True
        gd.compiled = clidict[gd.client.name]['compiled']
        gd.version = clidict[gd.client.name]['tag']
        if not gd.compiled:
            gd.client.embargoed = True
            gd.client.embargo_reason = "Your client didn't compile"
        if 'noconnect' in clidict[gd.client.name]:
	    gd.client.embargoed = True
            gd.client.embargo_reason = "Your client didn't connect to the game"
        if 'gamservdied' in clidict[gd.client.name]:
	    gd.client.embargoed = True
            gd.client.embargo_reason = "Gameserver broke, please see an Arena Dev"
        #if 'discon' in clidict[gd.client.name]:
	    #gd.client.embargoed = True
            #gd.client.embargo_reason = "Your client disconnected from the game unexpectedly"
        try:
            stats = json.loads(gd.client.stats)
        except:
            stats = {}
        gd.client.last_game_played = game.pk
        gd.client.stats = json.dumps(stats)
        try:
            gd.output_url = clidict[gd.client.name]['output_url']
        except KeyError:
            pass
        gd.client.save()
        gd.save()


def assign_elo(winner, loser):
    delta = winner.rating - loser.rating
    exp = (-1 * delta) / 400
    odds = 1 / (1 + math.pow(10, exp))
    if winner.rating < 2100:
        k = 32
    elif winner.rating > 2400:
        k = 12
    else:
        k = 24
    modifier = k * (1 - odds)
    winner.rating += modifier
    loser.rating = max([1, loser.rating - modifier])
    winner.save()
    loser.save()


def adjust_win_rate(w, l, alpha=0.15):
    win_p, w_created = WinRatePrediction.objects.get_or_create(winner=w, loser=l)
    old_win = copy(win_p)
    lose_p, l_created = WinRatePrediction.objects.get_or_create(winner=l, loser=w)
    old_lose = copy(lose_p)
    win_p.prediction += alpha * (1 - win_p.prediction)
    lose_p.prediction -= alpha * lose_p.prediction
    print "Prediction Updated:", w.name, old_win.prediction, "to", win_p.prediction
    print "Prediction Updated:", l.name, old_lose.prediction, "to", lose_p.prediction
    win_p.save()
    lose_p.save()


if __name__ == "__main__":
    main()

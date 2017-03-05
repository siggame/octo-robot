#
# MS&T SIG-Game 
# Author: Brandon Phelps, Daniel Bolef

# Swiss Chess scheduler built for the CS5400 Chess AI tournament. 

import random
import urllib
import json
import time
import pprint
import math
import beanstalkc
import gc
import sys
import argparse
import decimal
from multiprocessing import Process

import django
django.setup()

from thunderdome.config import game_name, req_queue_len
from thunderdome.models import Client, Game
from thunderdome.sked import sked
from utilities import webinteraction as WI

import scheduler_validating as SV
import clean_database as CD
import embargo_shellai as ESAI
from scheduler_tournament import finish
from collections import defaultdict

uncompleted_games = []
competing_clients = []
current_round = 0
start_game = 0
include_humans = False
pullScores = False
eligible = True
max_rounds = 0
clientNum = 0
valid_list = []
round_games = []
stalk = None
class Player():
    def __init__(self, name, score=0.0, rating=0):
        self.name = name
        self.score = score
        self.rank = 0
        self.rating = rating
        self.past_competitors = [] # is a list of other Players that have been versed by self in the past
        self.color_pref = 0
        self.num_white = 0
        self.num_black = 0
        self.pref_power = 0
        self.buchholz = 0.0
        self.sumrate = 0
        self.recieved_bye = False
        self.pairing_number = 0
        
    def __str__(self):
        return str(self.name) + str(self.score)
    
    def __eq__(self, other):
        if self.name == other.name and self.pairing_number == other.pairing_number:
            return True
        return False

    def __cmp__(self, other):
        if self.pairing_number > other.pairing_number:
            return -1
        elif self.pairing_number < other.pairing_number:
            return 1
        else:
            return 0

class Found(Exception): pass

def main():
    global current_round
    global include_humans
    global iterative_swiss
    global max_rounds
    global start_game
    global monrad
    global dutch
    global pullScores
    global clientNum
    global competing_clients
    global round_games
    global stalk
    parser = argparse.ArgumentParser(description='Swiss Chess scheduler')
    parser.add_argument('--h', action='store_true', help='Whether to include humans, mainly for the chess tournament')
    parser.add_argument('--r', type=int, default=-1, help='Number of rounds to run')
    parser.add_argument('--g', type=int, default=1, help='Starting game number for pulling in precompleted games')
    parser.add_argument('--s', action='store_true', help='Pull scores in and start on specified round')
    parser.add_argument('--v', action='store_true', help='Reset visualization')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--eligible", help="Build a tournament with eligible clients only", action="store_true")
    group.add_argument("--everyone", help="Build a tournament with all clients", action="store_true")
    args = parser.parse_args()
    print args
    include_humans = args.h
    eligible = args.eligible
    start_game = args.g
    pullScores = args.s
    CD.main()
    #WI.update_clients() Should not update clients as this is a tournament
    print "Include humans", include_humans
    print "Removing non-eligible clients"
    if eligible:
        for i in Client.objects.all():
            if i.eligible == False:
                i.delete()
    if not include_humans:
        for i in Client.objects.all():
            if i.language == "Human":
                i.delete()
    ESAI.embargo_shellai()  #Embargo all shell ai clients
    print "Success!"
    print "Reseting scores"
    cli = Client.objects.filter(embargoed=False).filter(missing=False)
    for x in cli:
        clientNum += 1
        x.score = 0.0
        x.num_black = 0
        x.save()
    print "Success!"
    print "Unclaiming games"
    Game.objects.filter(claimed=True).update(claimed=False)
    print "Success!"
    if args.v:
        print "Reseting visualization"
        Game.objects.filter(been_vised=True).update(been_vised=False)
        print "Success!"
    print "Calculating number of rounds"
    round_calculate = clientNum
    while round_calculate > 1:
        round_calculate = round_calculate / 2
        max_rounds += 1
    max_rounds += 1 #Seems to make a big difference in accuracy of results
    if args.r != -1:
        max_rounds = args.r

    print "Playing with", max_rounds, "rounds"
    try:
        stalk = beanstalkc.Connection(port=11300)
    except:
        raise Exception("Beanstalk error:")
    print "Inital setup complete, beginning swiss algorithm specific setup"
    req_tube = "game-requests-%s" % game_name
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    while current_round <= max_rounds:
        if not uncompleted_games:
            if current_round == 0:
                competing_clients = monrad_setup(cli)
            else:
                print "Next Round:", current_round
                calc_tie_break()
                sort_players()
                for x in competing_clients:
                    print x.name, x.score
                while current_round > 1:
                    result = raw_input('Would you like to: continue (y), replay game (r) or abort (a): ')
                    if result == 'y':
                        break
                    elif result == 'a':
                        sys.exit()
                    elif result == 'r':
                        print "Games available for replay:"
                        for x in round_games:
                            print x
                        game_choice = -1
                        try:
                            game_choice = int(raw_input('What game would you like to replay? '))
                        except ValueError:
                            pass
                        found = False
                        for x in round_games:
                            if x == game_choice:
                                replay(game_choice)
                                round_games.remove(x)
                                found = True
                                break
                        if not found:
                            print "That game is not available for replay"
                        continue
                    else:
                        print "Invaild input"
                if current_round > 1:
                    replayedGames = False
                    while uncompleted_games:
                        time.sleep(1)
                        score_games()
                        replayedGames = True
                    if replayedGames:
                        result = raw_input('Did those darn kids break something else? (y/n) ')
                        if result == 'n':
                            print "Kool let's go then"
                            del round_games[:]
                        elif result == 'y':
                            print "Those darn whippersnappers"
                            continue
                        else:
                            print "I'm gonna take that as a yes"
                            continue
                    else:
                        del round_games[:]
                calc_tie_break()
                sort_players()
                update_standings(competing_clients)
                print "Beginning Round:", current_round
                monrad_schedule()
        else:
            score_games()
        time.sleep(1)
    while uncompleted_games:
        time.sleep(1)
        score_games()
    calc_tie_break()
    sort_players()
    for x in competing_clients:
        print x.name, x.score
    whippersnappers = True
    while whippersnappers:
        while True:  #Hold here until the user says continue
            result = raw_input('Would you like to: continue (y), replay game (r) or abort (a): ')
            if result == 'y':
                break
            elif result == 'a':
                sys.exit()
            elif result == 'r':
                print "Games available for replay:"
                for x in round_games:
                    print x
                game_choice = -1
                try:
                    game_choice = int(raw_input('What game would you like to replay? '))
                except ValueError:
                    pass
                found = False
                for x in round_games:
                    if x == game_choice:
                        replay(game_choice)
                        round_games.remove(x)
                        found = True
                        break
                if not found:
                    print "That game is not available for replay"
            else:
                print "Invaild input"
        replayedGames = False
        while uncompleted_games:
            time.sleep(1)
            score_games()
            replayedGames = True
        if replayedGames:
            result = raw_input('So did you guys manage to break more games? (y/n) ')
            if result == 'n':
                print "Good, lets get going shall we?"
                del round_games[:]
                whippersnappers = False
            elif result == 'y':
                print "*Tries to think of a movie reference to make fun of you, fails* Let's try this again"
                whippersnappers = True
            else:
                print "You're trying to crash me aren't you, well you can't (btw I'm taking that as a yes)"
                whippersnappers = True
        else:
            del round_games[:]
            whippersnappers = False
    calc_tie_break()
    sort_players()
    update_standings(competing_clients)
    tied = False
    for x in competing_clients:
        for c in competing_clients:
            if x.name == c.name:
                continue
            if x.score == c.score and x.buchholz == c.buchholz and x.sumrate == c.sumrate and x.num_black == c.num_black:
                tied = True
                print "There was a tie! Playing another round"
    first = True
    while tied:
        print "Next Round:", current_round
        calc_tie_break()
        sort_players()
        for x in competing_clients:
            print x.name, x.score
        if first:
            result = 'y'
            first = False
        else:
            result = raw_input('Would you like to: continue (y), replay game (r) or abort (a): ')
        if result == 'y':
            pass
        elif result == 'a':
            sys.exit()
        elif result == 'r':
            print "Games available for replay:"
            for x in round_games:
                print x
            game_choice = -1
            try:
                game_choice = int(raw_input('What game would you like to replay? '))
            except ValueError:
                pass
            found = False
            for x in round_games:
                if x == game_choice:
                    replay(game_choice)
                    round_games.remove(x)
                    found = True
                    break
            if not found:
                print "That game is not available for replay"
            continue
        else:
            print "Invalid input"
            continue
        replayedGames = False
        while uncompleted_games:
            time.sleep(1)
            score_games()
            replayedGames = True
        if replayedGames:
            result = raw_input('Your games are scored, we good? (y/n) ')
            if result == 'n':
                print "WOW"
                continue
            elif result == 'y':
                print "Good, let's get back on track"
                del round_games[:]
            else:
                print "All I wanted was y or n, now you have to answer more prompts"
                continue
        else:
            del round_games[:]
        calc_tie_break()
        sort_players()
        update_standings(competing_clients)
        print "Beginning Round:", current_round
        monrad_schedule(True)
        while uncompleted_games:
            time.sleep(1)
            score_games()
        calc_tie_break()
        sort_players()
        whippersnappers = True
        while whippersnappers:
            while True:  #Hold here until user says continue
                for x in competing_clients:
                    print x.name, x.score
                result = raw_input('Would you like to: continue (y), replay game (r) or abort (a): ')
                if result == 'y':
                    break
                elif result == 'a':
                    sys.exit()
                elif result == 'r':
                    print "Games available for replay:"
                    for x in round_games:
                        print x
                    game_choice = -1
                    try:
                        game_choice = int(raw_input('What game would you like to replay? '))
                    except ValueError:
                        pass
                    found = False
                    for x in round_games:
                        if x == game_choice:
                            replay(game_choice)
                            round_games.remove(x)
                            found = True
                            break
                    if not found:
                        print "That game is not available for replay"
                else:
                    print "Invalid input"
            replayedGames = False
            while uncompleted_games:
                time.sleep(1)
                score_games()
                replayedGames = True
            if replayedGames:
                result = raw_input('Games are scored, you need to replay any more? (y/n) ')
                if result == 'y':
                    print "Kool, let try that again"
                    whippersnappers = True
                elif result == 'n':
                    print "OK, gotta go fast *sanic noise*"
                    del round_games[:]
                    whippersnappers = False
                else:
                    print "You know I did list the valid choices. I'm assuming you wanted to replay more"
                    whippersnappers = True
            else:
                del round_games[:]
                whippersnappers = False
        calc_tie_break()
        sort_players()
        update_standings(competing_clients)
        tied = False
        for x in competing_clients:
            for c in competing_clients:
                if x.name == c.name:
                    continue
                if x.score == c.score and x.buchholz == c.buchholz and x.sumrate == c.sumrate and x.num_black == c.num_black:
                    tied = True
                    print "There was a tie! Playing another round"
    do_another = True
    first = True
    while do_another:
        for x in competing_clients:
            print x.name, x.score
        if first:
            result = 'y'
            first = False
        else:
            result = raw_input('Would you like to: continue (y), replay game (r) or abort (a): ')
        if result == 'y':
            pass
        elif result == 'a':
            sys.exit()
        elif result == 'r':
            print "Games available for replay:"
            for x in round_games:
                print x
            game_choice = -1
            try:
                game_choice = int(raw_input('What game would you like to replay? '))
            except ValueError:
                pass
            found = False
            for x in round_games:
                if x == game_choice:
                    replay(game_choice)
                    round_games.remove(x)
                    found = True
                    break
            if not found:
                print "That game is not available for replay"
            continue
        else:
            print "Invaild input"
            continue
        replayedGames = False
        while uncompleted_games:
            time.sleep(1)
            score_games()
            replayedGames = True
        if replayedGames:
            result = raw_input('Your games are scored, we good? (y/n) ')
            if result == 'n':
                print "WOW"
                continue
            elif result == 'y':
                print "Oh boy! I think we're almost done!"
                del round_games[:]
            else:
                print "All I wanted was y or n, now you have to answer more prompts"
                continue
        else:
            del round_games[:]
        calc_tie_break()
        sort_players()
        update_standings(competing_clients)
        print 'Current rankings:'
        for x in competing_clients:
            print x.name, x.score, x.buchholz, x.sumrate, x.num_black
        print "Just completed round", current_round - 1
        play_again = raw_input('Play another round?(y/n): ')
        if play_again == 'y':
            print "Current Round:", current_round
            monrad_schedule()
            while uncompleted_games:
                time.sleep(1)
                score_games()
            calc_tie_break()
            sort_players()
            for x in competing_clients:
                for c in competing_clients:
                    if x.name == c.name:
                        continue
                    if x.score == c.score and x.buchholz == c.buchholz and x.sumrate == c.sumrate and x.num_black == c.num_black:
                        print "There was a tie!"
                        tied = True
                    else:
                        tied = False
        elif play_again == 'n':
            do_another = False
        else:
            print "Invalid answer, please enter 'y' or 'n'"
    f = open('winner.txt', 'w')
    for i, x in enumerate(competing_clients):
        f.write(str(i))
        f.write(". ")
        f.write(x.name)
        f.write(' ')
        f.write(str(x.score))
        f.write(' ')
        f.write(str(x.buchholz))
        f.write(' ')
        f.write(str(x.sumrate))
        f.write(' ')
        f.write(str(x.num_black))
        f.write('\n')
    f.close()
    stalk.close()
    finish()

def compatible_players(p1, p2, should_print=True):
    if p1 in p2.past_competitors:
        if should_print:
            print "players", p1.name, "and", p2.name, "can't play because they fought before"
        return False
    return True

def score_games():
    '''go through the games and set the corresponding scores of each game'''
    global competing_clients
    global current_round
    global round_games
    for g in list(uncompleted_games):
        try:
            gameC = Game.objects.get(pk=g)
            game_clis = list(gameC.gamedata_set.all())
        except:
            pass
        if gameC.status == "Complete":
            if gameC.tied:
                print "Game %d: Draw!" % (g)
                for i, c in enumerate(game_clis):
                    for x in competing_clients:
                        if x.name == c.client.name:
                            if i == 0:
                                x.num_white += 1
                            elif i == 1:
                                x.num_black += 1
                        if x.name == c.client.name:
                            print "%s's score goes from %s to" % (x.name, str(x.score)),
                            x.score += 0.5
                            print x.score
            else:
                for i, c in enumerate(game_clis):
                    for x in competing_clients:
                        if x.name == gameC.winner.name and x.name == c.client.name:
                            print x.name, "is the winner of game", g, "and their score goes from", x.score, "to",
                            x.score += 1.0
                            print x.score
                        if x.name == c.client.name:
                            if i == 0:
                                x.num_white += 1
                            elif i == 1:
                                x.num_black += 1
            gameC.claimed = True
            gameC.save()
            #round_games.append(gameC.pk) #Shouldn't do here b/c it's done in schedule_game?
            for x in competing_clients:
                if x.name == game_clis[0].client.name:
                    for y in competing_clients:
                        if y.name == game_clis[1].client.name:
                            x.past_competitors.append(y)
                            y.past_competitors.append(x)
                            break
                    break
            uncompleted_games.remove(g)
        elif gameC.status == "Failed":            
            print "Game:", g, "failed, commiting suicide now."
            #sys.exit() # exit the game.
            #Attempt to reschedule the game
            replay(int(g))
            uncompleted_games.remove(g)
            #uncompleted_games.remove(g)
            #for x in Game.objects.all():
            #    x.claimed = False
            #    x.save()
            #for x in Client.objects.all():
            #    x.score = 0.0
            #    x.save()
            #current_round = 0
    calc_tie_break()
            
def update_standings(competing_clients):
    global current_round
    f = open("scores.txt", 'w')
    r = open("scores%s.txt" % (current_round), 'w')
    b = open("scores%sBackup.txt" % (current_round), 'w')
    for i in competing_clients:
        past = ""
        for k in i.past_competitors:
            past += str(k.name)
            past += "<>"
        this_client = Client.objects.get(name=i.name)
        f.write("%s+%s+%d+%d+%d+%d+%d+%d+%s\n" % (i.name, str(i.score), i.buchholz, i.sumrate, i.num_black, i.num_white, this_client.rating, current_round, past))
        r.write("%s+%s+%d+%d+%d+%d+%d+%d+%s\n" % (i.name, str(i.score), i.buchholz, i.sumrate, i.num_black, i.num_white, this_client.rating, current_round, past))
        b.write("%s+%s+%d+%d+%d+%d+%d+%d+%s\n" % (i.name, str(i.score), i.buchholz, i.sumrate, i.num_black, i.num_white, this_client.rating, current_round, past))
    f.close()    

def schedule_game(i, j):
    global start_game
    global round_games
    global stalk
    c1 = Client.objects.get(name=i.name)
    c2 = Client.objects.get(name=j.name)
    # first player is white
    c1name = i.name
    c2name = j.name
    # if a game is already computed, score the game instead of schedule
    games = Game.objects.all().filter(clients__name=c1name).filter(clients__name=c2name)
    score_game = False
    game_to_score = None
    for g in games:
        if g.status == "Complete" and not g.claimed and g.pk >= start_game:
            game_clients = list(g.gamedata_set.all())
            try:
                if game_clients[0].client.name == c1.name and game_clients[1].client.name == c2.name:
                    print "Found game", g, "already played, using that"
                    print game_clients[0].client.name, "vs", game_clients[1].client.name
                    round_games.append(g.pk)
                    if g.tied:
                        print "Draw!"
                        for k, c in enumerate(game_clients):
                            if c.client.name == i.name:
                                print "%s's score goes from %s to" % (i.name, str(i.score)),
                                i.score += 0.5
                                print i.score
                            else:
                                print "%s's score goes from %s to" % (j.name, str(j.score)),
                                j.score += 0.5
                                print j.score
                            if i.name == c.client.name:
                                if k == 0:
                                    i.num_white += 1
                                elif k == 1:
                                    i.num_black += 1
                            elif j.name == c.client.name:
                                if k == 0:
                                    j.num_white += 1
                                elif k == 1:
                                    j.num_black += 1

                    else:
                        for k, c in enumerate(game_clients):
                            if c.client.name == g.winner.name:
                                if c.client.name == i.name:
                                    print c.client.name, "won, their score goes from", i.score, "to",
                                    i.score += 1.0
                                    print i.score
                                else:
                                    print c.client.name, "won, their score goes from", j.score, "to",
                                    j.score += 1.0
                                    print j.score
                            if i.name == c.client.name:
                                if k == 0:
                                    i.num_white += 1
                                elif k == 1:
                                    i.num_black += 1
                            elif j.name == c.client.name:
                                if k == 0:
                                    j.num_white += 1
                                elif k == 1:
                                    j.num_black += 1
                    g.claimed = True
                    g.save()
                    score_game = True
                    i.past_competitors.append(j)
                    j.past_competitors.append(i)
                    break
            except:
                print "Found an invalid game, marking failed"
                g.status = 'Failed'
                g.save()
                    
    if not score_game:
        new_game = sked(c1, c2, stalk, "Tournament").pk
        uncompleted_games.append(new_game)
        round_games.append(new_game)
    else:
        i = calc_tie_break([i])
        j = calc_tie_break([j])
    for x in competing_clients:
        if x.name == i.name:
            x = i
        if x.name == j.name:
            x = j

def sort_players(clients=None):
    global current_round
    global competing_clients
    if clients is None:
        competing_clients = sorted(competing_clients, key=lambda x: x.rating, reverse=True)
        if current_round > 0:
            competing_clients = sorted(competing_clients, key=lambda x: x.num_black, reverse=True)
            competing_clients = sorted(competing_clients, key=lambda x: x.sumrate, reverse=True)
            competing_clients = sorted(competing_clients, key=lambda x: x.buchholz, reverse=True)
            competing_clients = sorted(competing_clients, key=lambda x: x.score, reverse=True)
    else:
        clients = sorted(clients, key=lambda x: x.rating, reverse=True)
        if current_round > 0:
            clients = sorted(clients, key=lambda x: x.num_black, reverse=True)
            clients = sorted(clients, key=lambda x: x.sumrate, reverse=True)
            clients = sorted(clients, key=lambda x: x.buchholz, reverse=True)
            clients = sorted(clients, key=lambda x: x.score, reverse=True)
        return clients
                
def monrad_setup(clients):
    global current_round
    global pullScores

    for i in clients:
        print i.name

    competing_clients = [Player(j.name, 0.0, j.rating) for j in clients]
    if pullScores:
        #scoresin = {}
        f = open('scores.txt', 'r')
        for line in f:
            #print "Client", count, "read in"
            scoresin = line.split("+")
            print "Reading in", scoresin[0]
            for i in competing_clients:
                if scoresin[0] == i.name:
                    client = Client.objects.get(name=i.name)
                    i.score = float(scoresin[1])
                    i.num_black = int(scoresin[4])
                    i.num_white = int(scoresin[5])
                    client.rating = int(scoresin[6])
                    client.save()
                    current_round = int(scoresin[7])
                    past_cli = str(scoresin[8]).split("<>")
                    for x in past_cli:
                        for k in competing_clients:
                            if x == k.name:
                                i.past_competitors.append(k)
        print "Setting round to", current_round
        f.close()
    else:
        current_round = 1
    print "Setup complete, beginning round", current_round
    return competing_clients


def monrad_schedule(tie_breaker=False):
    global current_round
    global clientNum
    global competing_clients
    to_schedule = []
    cli_on_hold = []
    a = []
    calc_tie_break()
    sort_players()
    hold = False
    for i, x in enumerate(competing_clients):
        if i % 2 == 0 and not hold:
            y = x
            odd = True
            continue
        else:
            misses = 0
            while True:
                odd = False
                if compatible_players(y, x) or tie_breaker:
                    x = recalc_colors(x)
                    y = recalc_colors(y)
                    if y.pref_power >= x.pref_power:
                        print y.name, "gets color preference over", x.name
                        if y.color_pref == 0:
                            a.append(y)
                            a.append(x)
                        else:
                            a.append(x)
                            a.append(y)
                    else:
                        print x.name, "gets color preference over", y.name
                        if x.color_pref == 0:
                            a.append(x)
                            a.append(y)
                        else:
                            a.append(y)
                            a.append(x)
                    to_schedule.append(a)
                    a = []
                    if len(cli_on_hold) >= 1:
                        sort_players(cli_on_hold)
                        y = cli_on_hold.pop(0)
                        if len(cli_on_hold) >= 1:
                            x = cli_on_hold.pop(0)
                            misses = 0
                        else:
                            break
                    else:
                        hold = False
                        break
                elif not compatible_players(y, x, False):
                    hold = True
                    misses += 1
                    cli_on_hold.append(x)
                    temp = cli_on_hold.pop(0)
                    x = temp
                    if misses >= len(cli_on_hold):
                        cli_on_hold.insert(0, temp)
                        break
    try_count_count = 0
    if len(cli_on_hold) == 0 and hold:
        odd = True
    elif len(cli_on_hold) > 0:
        odd = False
        hold = True
        try_count = 0
        while hold == True and try_count_count < clientNum:
            try_count += 1
            GO_BACK = to_schedule
            GO_BACK.reverse()
            try:
                if try_count > (clientNum * 50):
                    random.seed(os.urandom(100))
                    random.shuffle(GO_BACK)
                for wumbo in GO_BACK:
                    if try_count > (clientNum * 2):
                        if try_count % 2 == 1:
                            wumbo.reverse()
                    for z in wumbo:
                        if compatible_players(y, z):
                            for q in to_schedule:
                                if (wumbo[0] == q[0] and wumbo[1] == q[1]) or (wumbo[0] == q[1] and wumbo[1] == q[0]):
                                    to_schedule.remove(q)
                            for q in wumbo:
                                if z.name != q.name:
                                    cli_on_hold.append(q)
                            z = recalc_colors(z)
                            y = recalc_colors(y)
                            if y.pref_power >= z.pref_power:
                                print y.name, "gets color preference over", z.name
                                if y.color_pref == 0:
                                    a.append(y)
                                    a.append(z)
                                else:
                                    a.append(z)
                                    a.append(y)
                            else:
                                print z.name, "gets color preference over", y.name
                                if z.color_pref == 0:
                                    a.append(z)
                                    a.append(y)
                                else:
                                    a.append(y)
                                    a.append(z)
                            to_schedule.append(a)
                            a = []
                            raise Found

                if(try_count > (clientNum * 300)):
                   raise Found

            except Found:
                if len(cli_on_hold) == 1:
                    odd = True
                    hold = False
                    y = cli_on_hold.pop()
                elif len(cli_on_hold) > 1:
                    if try_count > (clientNum * 75):
                        random.seed(os.urandom(100))
                        random.shuffle(cli_on_hold)
                    else:
                        sort_players(cli_on_hold)
                    y = cli_on_hold.pop(0)
                    x = cli_on_hold.pop(0)
                    misses = 0
                    while True:
                        odd = False
                        if compatible_players(y, x):
                            x = recalc_colors(x)
                            y = recalc_colors(y)
                            if y.pref_power >= x.pref_power:
                                print y.name, "gets color preference over", x.name
                                if y.color_pref == 0:
                                    a.append(y)
                                    a.append(x)
                                else:
                                    a.append(x)
                                    a.append(y)
                            else:
                                print x.name, "gets color preference over", y.name
                                if x.color_pref == 0:
                                    a.append(x)
                                    a.append(y)
                                else:
                                    a.append(y)
                                    a.append(x)
                            to_schedule.append(a)
                            a = []
                            if len(cli_on_hold) >= 1:
                                y = cli_on_hold.pop(0)
                                if len(cli_on_hold) >= 1:
                                    x = cli_on_hold.pop(0)
                                    misses = 0
                                else:
                                    odd = True
                                    hold = False
                                    break
                            else:
                                hold = False
                                break
                        elif not compatible_players(y, x, False):
                            hold = True
                            misses += 1
                            cli_on_hold.append(x)
                            temp = cli_on_hold.pop(0)
                            x = temp
                            if misses > len(cli_on_hold):
                                cli_on_hold.insert(0, temp)
                                if try_count > (clientNum * 300):
                                    try_count = clientNum * 75
                                    try_count_count += 1
                                break
    if try_count_count >= clientNum:
        print "Giving up on that, random matchups until a valid matchup set is found"
        try_again = True
        try_count = 0
        possible_lists = []
        for p in permute(competing_clients):
            try_count += 1
            print "Try:", '%.2E' % decimal.Decimal(try_count)
            for x in to_schedule:
                to_schedule.remove(x)
            w = Process(target=try_matchup, args=(p,))
            w.start()
            if len(valid_list) > 0:
                break
        to_schedule = valid_list.pop(0)

    for x in to_schedule:
        schedule_game(x.pop(0), x.pop(0))
    if odd and len(to_schedule) > 0:
        print y.name, "gets a bye"
        y.score += 1
    current_round += 1
    
def recalc_colors(x):
    prelim_pref_x = x.num_white - x.num_black
    if prelim_pref_x <= 0:
        x.color_pref = 0
    else:
        x.color_pref = 1
    x.pref_power = abs(prelim_pref_x)
    print x.name, "has played", x.num_white, "white games and", x.num_black, "black games, and their preference power is", x.pref_power
    return x

def calc_tie_break(clients=None):
    global competing_clients
    if clients is None:
        for x in competing_clients:
            client = Client.objects.get(name=x.name)
            x.buchholz = 0
            x.sumrate = 0
            for c in competing_clients:
                if c in x.past_competitors:
                    past_client = Client.objects.get(name=c.name)
                    x.buchholz += past_client.score
                    x.sumrate += past_client.rating
            client.buchholz = x.buchholz
            client.sumrate = x.sumrate
            client.score = x.score
            client.num_black = x.num_black
            client.save()
    else:
        for x in clients:
            client = Client.objects.get(name=x.name)
            x.buchholz = 0
            x.sumrate = 0
            for c in competing_clients:
                if c in x.past_competitors:
                    past_client = Client.objects.get(name=c.name)
                    x.buchholz += past_client.score
                    x.sumrate += past_client.rating
            client.buchholz = x.buchholz
            client.sumrate = x.sumrate
            client.score = x.score
            client.num_black = x.num_black
            client.save()
            return x

def permute(xs, low=0):
    if low + 1 >= len(xs):
        yield xs
    else:
        for p in permute(xs, low + 1):
            yield p        
        for i in range(low + 1, len(xs)):        
            xs[low], xs[i] = xs[i], xs[low]
            for p in permute(xs, low + 1):
                yield p        
            xs[low], xs[i] = xs[i], xs[low]

def try_matchup(p):
    to_schedule = []
    a = []
    global valid_list
    for i, x in enumerate(p):
        if i % 2 == 0:
            y = x
            odd = True
            continue
        else:
            odd = False
            if not compatible_players(y, x):
                try_again = True
                break
            x = recalc_colors(x)
            y = recalc_colors(y)
            if y.pref_power >= x.pref_power:
                print y.name, "gets color preference over", x.name
                if y.color_pref == 0:
                    a.append(y)
                    a.append(x)
                else:
                    a.append(x)
                    a.append(y)
            else:
                print x.name, "gets color preference over", y.name
                if x.color_pref == 0:
                    a.append(x)
                    a.append(y)
                else:
                    a.append(y)
                    a.append(x)
            to_schedule.append(a)
            try_again = False
    if not try_again:
        valid_list.append(to_schedule)

def replay(game_number):
    #ALRIGHT people lets figure out how to unscore a game and then reschedule it
    global competing_clients
    game = Game.objects.get(pk=game_number)
    game_clients = list(game.gamedata_set.all())
    p0 = game_clients[0].client.name
    p1 = game_clients[1].client.name
    #remove clients from previously played list and decrimente black and white counts approprately
    if game.status == "Complete":
        for x in competing_clients:
            for y in competing_clients:
                if x.name == p0 and y.name == p1:
                    x.past_competitors.remove(y)
                    y.past_competitors.remove(x)
                    x.num_white -= 1
                    y.num_black -= 1
                    break
    #subtract scores
    if not game.tied and game.status == "Complete":
        for x in competing_clients:
            if x.name == game.winner.name:
                x.score -= 1
                break
    elif game.status == "Complete":
        for x in competing_client:
            if x.name == p0 or x.name == p1:
                x.score -= 0.5
    #make sure the game is not reused
    game.status = 'Failed'
    game.save()
    #reschedule the game
    for x in competing_clients:
        for y in competing_clients:
            if x.name == p0 and y.name == p1:
                print "Rescheduling game %d" % game_number
                schedule_game(x, y)
                return
        
if __name__ == "__main__":
    main()


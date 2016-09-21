#
# MS&T SIG-Game 
# Author: Brandon Phelps, Daniel Bolef

# Swiss Chess scheduler built for the CS5400 Chess AI tournament. 

#TO DO:
#Test game clients compare code
import random
import urllib
import json
import time
import pprint
import math
import csv
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
from scheduler_tournament import finish
from collections import defaultdict

uncompleted_games = []
competing_clients = []
current_round = 0
start_game = 0
monrad = False
dutch = False
include_humans = False
pullScores = False
eligible = True
max_rounds = 0
clientNum = 0
valid_list = []
scores_file = open('wins.txt', 'w')
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
    parser = argparse.ArgumentParser(description='Swiss Chess scheduler')
    parser.add_argument('--h', action='store_true', help='Whether to include humans, mainly for the swiss tournament')
    parser.add_argument('--r', type=int, default=-1, help='Number of rounds to run')
    parser.add_argument('--g', type=int, default=1, help='Starting game number for pulling in precompleted games')
    parser.add_argument('--s', action='store_true', help='Pull scores in and start on specified round')
    swissType = parser.add_mutually_exclusive_group(required=True)
    swissType.add_argument('--dutch', action='store_true', help='Run with Dutch Swiss (Currently broken)')
    swissType.add_argument('--monrad', action='store_true', help='Run with Monrad Swiss')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--eligible", help="Build a tournament with eligible clients only", action="store_true")
    group.add_argument("--everyone", help="Build a tournament with all clients", action="store_true")
    args = parser.parse_args()
    print args
    include_humans = args.h
    eligible = args.eligible
    start_game = args.g
    monrad = args.monrad
    dutch = args.dutch
    pullScores = args.s
    CD.main()
    WI.update_clients()
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
    print "Success!"
    print "Reseting scores"
    cli = Client.objects.filter(embargoed=False).filter(missing=False)
    for x in cli:
        clientNum += 1
        x.score = 0.0
        x.save()
    print "Success!"
    print "Unclaiming games"
    for x in Game.objects.all().filter(claimed=True):
        x.claimed = False
        x.save()
    print "Success!"
    print "Calculating number of rounds"
    round_calculate = clientNum
    while round_calculate > 1:
        round_calculate = round_calculate / 2
        max_rounds += 1
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
            print "Current Round:", current_round
            if args.dutch:
                schedule_volley(stalk, current_round)
            elif args.monrad:
                if current_round == 0:
                    competing_clients = monrad_setup(cli)
                else:
                    for x in competing_clients:
                        realClient = Client.objects.get(name=x.name)
                        x.score = realClient.score
                    update_standings(competing_clients)
                    monrad_schedule(competing_clients, stalk)
        else:
            score_games(competing_clients)
        time.sleep(1)
    while uncompleted_games:
        time.sleep(1)
        score_games(competing_clients)
    for x in competing_clients:
        realClient = Client.objects.get(name=x.name)
        x.score = realClient.score
    update_standings(competing_clients)
    for x in competing_clients:
        realClient = Client.objects.get(name=x.name)
        x.score = realClient.score
    competing_clients = calc_tie_break(competing_clients)
    competing_clients = sort_players(competing_clients)
    tied = False
    for x in competing_clients:
        for c in competing_clients:
            if x.name == c.name:
                continue
            if x.score == c.score and x.buchholz == c.buchholz and x.sumrate == c.sumrate and x.num_black == c.num_black:
                tied = True
                print "There was a tie! Playing another round"
    while tied:
        print "Current Round:", current_round
        if args.dutch:
            schedule_volley(stalk, current_round, True)
        elif args.monrad:
            monrad_schedule(competing_clients, stalk, True)
        while uncompleted_games:
            time.sleep(1)
            score_games(competing_clients)
        for x in competing_clients:
            realClient = Client.objects.get(name=x.name)
            x.score = realClient.score
        update_standings(competing_clients)
        for x in competing_clients:
            realClient = Client.objects.get(name=x.name)
            x.score = realClient.score
        competing_clients = calc_tie_break(competing_clients)
        competing_clients = sort_players(competing_clients)
        tied = False
        for x in competing_clients:
            for c in competing_clients:
                if x.name == c.name:
                    continue
                if x.score == c.score and x.buchholz == c.buchholz and x.sumrate == c.sumrate and x.num_black == c.num_black:
                    tied = True
                    print "There was a tie! Playing another round"
    do_another = True
    while do_another:
        print 'Current rankings:'
        for x in competing_clients:
            print x.name, x.score, x.buchholz, x.sumrate, x.num_black
        print "Just completed round", current_round - 1
        play_again = raw_input('Play another round?(y/n): ')
        if play_again == 'y':
            print "Current Round:", current_round
            if args.dutch:
                schedule_volley(stalk, current_round)
            elif args.monrad:
                monrad_schedule(competing_clients, stalk)
            while uncompleted_games:
                time.sleep(1)
                score_games(competing_clients)
            for x in competing_clients:
                realClient = Client.objects.get(name=x.name)
                x.score = realClient.score
            update_standings(competing_clients)
            for x in competing_clients:
                realClient = Client.objects.get(name=x.name)
                x.score = realClient.score
            competing_clients = calc_tie_break(competing_clients)
            competing_clients = sort_players(competing_clients)
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
    scores_file.close()
    stalk.close()
    finish()

def hasAWinner(brackScores):
    if not brackScores.keys():
        return False
    wins = max(brackScores.keys())
    
    if(wins >= math.ceil(math.log(len(competing_clients), 2))):
        print "@@@@@@@@"
        print "@@@@@@@@"
        print "Winner is"
        for i in brackScores[wins]:
            print i.name
        print "@@@@@@@@"
        print "@@@@@@@@"
        return True
    else:
        return False

def game_status(g_id):
    return Game.objects.get(pk=g_id).status

def schedule_volley(stalk, sRound):
    global competing_clients
    global uncompleted_games
    global current_round
    global include_humans
    if sRound == 0:
        # uncomment next line to validate each ai, break embargoes probably needs to be ran first. 
        # print "starting validation scheduling"
        # print "swiss mustn't have any failed games"
        # uncompleted_games.extend([i.pk for i in SV.validateSched(stalk)])
        while uncompleted_games:
            for c in list(uncompleted_games):
                if game_status(c) in ["Complete", "Failed"]:
                    uncompleted_games.remove(c)
            print("games to go: %d" % len(uncompleted_games))
            time.sleep(2)
        
        clients = list(Client.objects.exclude(name='bye').filter(embargoed=False))        

        if not include_humans:
            for i in list(clients):
                if i.language == "Human":
                    clients.remove(i)

        for i in list(clients):
            if i.missing:
                clients.remove(i)

        for i in clients:
            print i.name

        competing_clients = [Player(j.name, j.score, j.rating) for j in clients]
        
        # assign pairing numbers to each player
        # sort the competitors by rank and elo obtained during the competition
        # give numbers from 0 - len(competing_clients) these will be perminent and used
        # lower means higher rank
        # later in the scheduling
        # for now just give random numbers

        # for testing only
        # sort clients alphabetically
        #competing_clients.sort(lambda x, y: cmp(x.name.lower(), y.name.lower()))
        
        # sort clients by score ranking
        competing_clients.sort(key=lambda x: x.score, reverse=True)        
        # competing_clients = competing_clients[len(competing_clients)-9:]
        #print "sorted clients"
        #print("assigning pairing number")
        #for i, j in enumerate(competing_clients):
        #    print j.name, " is assigned", i
        #    j.pairing_number = i
    
    schedule_brackets(create_score_brackets(), sRound, stalk)
    scores_file.write("%d\n" % current_round)
    current_round += 1

def create_score_brackets():
    # returns a dictionary where the key is the score of the players
    # thus creating a seperate brackets
    score_brackets = defaultdict(list)
    for i in competing_clients:
        score_brackets[i.score].append(i)
    return score_brackets

def schedule_brackets(score_brackets, sRound, stalk):
    median_score = sRound/2.0
    #print("Current scores")
    #for i in score_brackets.keys():
    #    for j in score_brackets[i]:
    #        print j.name, j.score

    print "current number of players:", len(competing_clients)
    if len(competing_clients) % 2 != 0:
        print "need to give bye to lowest scorer of lowest group"
        # give lowest scoring person in the lowest score group a bye
        # make sure the player has not been given a bye before
        # 8.1
        l_bracket = min(score_brackets.keys())
        print "lowest score bracket:", l_bracket
        l_group = score_brackets[l_bracket]
        print "lowest score group"
        # for i in l_group:
        #    print i.name, i.rating
        def player_comparison(x, y):
            if x.recieved_bye:
                return 1
            elif y.recieved_bye:
                return -1
            else:
                return x.rating - y.rating
        l_group.sort(cmp=player_comparison)
        l_p = l_group.pop(0)
        print "bye given to:", l_p.name
        # give bye this round to l_p
        l_p.recieved_bye = True
        l_p.score += 1

    current_bracket = 0
    print "Median score bracket value", median_score
    while score_brackets:
        bracket = max(score_brackets.keys())
        temp = 0
        if bracket < median_score:
            bracket = min(score_brackets.keys())
            temp = 1
        m_group = score_brackets[bracket]
        del score_brackets[bracket]
        prepare_group(m_group, temp, score_brackets)
        # the current proposed pairings are as listed in 9.4
        if sRound != 0:
            #round one is special and thus color setup differently
            setup_group(m_group, score_brackets, temp)
        else:
            print "setup for round one"
            # for i in m_group:
            #    print i.name, i.pairing_number            
            # white = 0, black = 1
            # this is done as stated in 14.2 and what has been observed from swiss perfect
            first_player_color = 0 # for now default is white, this should be in argv
            pos = 0
            t = [None, None]
            while pos < len(m_group)/2:
                t[0], t[1] = m_group[pos], m_group[len(m_group)/2 + pos]
                if pos % 2 == 0:
                    if first_player_color == 0:
                        t[0], t[1] = m_group[pos], m_group[len(m_group)/2 + pos]
                    else:
                        t[0], t[1] = m_group[len(m_group)/2 + pos], m_group[pos]
                else:
                    if first_player_color == 0:
                        t[0], t[1] = m_group[len(m_group)/2 + pos], m_group[pos]
                    else:
                        
                        t[0], t[1] = m_group[pos], m_group[len(m_group)/2 + pos]
                m_group[pos], m_group[len(m_group)/2 + pos] = t[0], t[1]
                pos += 1
        schedule_group(m_group, temp, stalk)

def group_is_compatible(group):
    pos = 0
    print "Checking if group is compatible"
    for i in group:
        print i
    while pos < len(group)/2:
        if not compatible_players(group[pos], group[(len(group)/2) + pos]):
            print "group is not compatible because of", group[pos].name, "and", group[(len(group)/2)+pos].name
            return False
    return True

def compatible_players(p1, p2, should_print=True):
    if p1 in p2.past_competitors:
        if should_print:
            print "players", p1.name, "and", p2.name, "can't play because they fought before"
        return False
    return True

def prepare_group(group, sked_dir, score_brackets):
    """
    takes in a group and does checking and move players
    to appropriate other score groups based on 9.3

    This is effectivly just moving players around score groups thus
    making sure everyone is in their correct group
    """

    if not score_brackets.keys():
        return
    
    # if sked_dir == "down"
    if sked_dir == 0:
        max_brak = max(score_brackets.keys())
    else:
        max_brak = min(score_brackets.keys())
        
    #check for a player played everyone in group before
    for i in list(group):
        for c in i.past_competitors:
            if not i == c:
                break
        else:
            print "lists are equal"
            group.remove(i)
            score_brackets[max_brak].append(i)

    # check for color compatability
    #for i in list(group):
    #    for c in list(group):
    #        if 2 < i.color_pref + c.color_pref < -2:
    #            pass
    
    group.sort()
    # check for if group contains even number of players
    if len(group) % 2 != 0:
        if sked_dir == 0:
            # remove lowest 
            t = group.pop(0)
            print "moving player down", t.name
            score_brackets[max_brak].append(t)
        else:
            # remove highest
            t = group.pop(len(group)-1)
            print "moving player up", t.name
            score_brackets[max_brak].append(t)
    # the proposed pairings are now constructed and ready to be scrutinized
    return

def setup_group(group, score_brackets, sched_dir):
    """
    sets up the group for scheduling
    by making sure that the pairings are compatible, if not
    then makes the pairings compatible
    """
    # schedule direction 0 means downward
    print "setting up pairings"
    print "current pairings are"
    #pos = 0
    #while pos < len(group)/2:
    #    print group[pos].name, "vs", group[(len(group)/2) + pos].name
    #    pos += 1
    pos = 0
    
    if sched_dir == 0:
        pass
    while pos < len(group)/2:
        # print "checking", group[pos].name, group[(len(group)/2) + pos].name
        if not compatible_players(group[pos], group[(len(group)/2) + pos]):
            # a pairing is not compatible, find a new pairing for the higher player
            temp_group = list(group)
            temp_group.remove(group[(len(group)/2) + pos])
            while temp_group:
                j = min(temp_group)
                temp_group.remove(j)
                print "trying player", j.name, j.pairing_number
                if compatible_players(group[pos], j):
                    group[group.index(j)], group[(len(group)/2) + pos] = group[(len(group)/2) + pos], j
                    break
            else:
                print "no compatible players found in this group"
                exit()
        pos += 1
    
    # color checking and setting
    pos = 0
    while pos < len(group)/2:
        t = [group[pos], group[(len(group)/2) + pos]]
        # print t[0].name, ":", t[0].color_pref, "vs", t[1].name, ":", t[1].color_pref
        #if t[0].color_pref == 0 and t[1].color_pref == 0:
        #    random.shuffle(t) 
        if t[0].pref_power == 0:
            if t[1].pref_power > 0:
                t[0], t[1] = t[1], t[0]
        elif t[1].pref_power == 0:
            if t[0].pref_power < 0:
                t[0], t[1] = t[1], t[0]
        elif math.fabs(t[0].pref_power) == math.fabs(t[1].pref_power):
            if t[0].pref_power < 0:
                t[0], t[1] = t[1], t[0]
        else:
            white = min(t, key =lambda x:x.pref_power) 
            black = max(t, key=lambda x:x.pref_power) 
            # who ever has the higher magnitude color pref gets to pick the color they need
            if math.fabs(white.pref_power) > math.fabs(black.pref_power):
                if white.pref_power < 0:
                    t = (black, white)
                elif white.pref_power > 0:
                    t = (white, black)
            elif math.fabs(white.pref_power) < math.fabs(black.pref_power):
                if black.pref_power < 0:
                    t = (white, black)
                elif black.pref_power > 0:
                    t = (black, white)
        
        group[pos], group[(len(group)/2) + pos] = t[0], t[1]
        # print t[0].name, ":", t[0].pref_power, "vs", t[1].name, ":", t[1].pref_power
        pos += 1

def schedule_group(group, bracket_type, stalk):
    # takes in a group which is a list of clients which are to be paired for games
    # group needs to be "prepared" before getting scheduled based off 9.4
    global competing_clients
    try:
        print "Group contains", len(group), "players", group[0].score
    except IndexError:
        print "group is empty"

    
    # schedule down
    pos = 0
    while pos < len(group)/2:
        i = group[pos]
        j = group[(len(group)/2) + pos]
        i,j = schedule_game(i, j, stalk)
        pos += 1


def score_games(competing_clients):
    '''go through the games and set the corresponding scores of each game'''
    global current_round
    global monrad
    global dutch
    for g in list(uncompleted_games):
        if game_status(g) == "Complete":
            try:
                gameC = Game.objects.get(pk=g)
                game_clis = list(gameC.clients.all())
            except:
                pass
            if gameC.tied:
                print "Game %d: Draw!" % (g)
                #c_iterator = game_clients.clients.iterator()
                #c1 = c_iterator.next()
                #c2 = c_iterator.next()
                
                #for i in game_clients.clients.iterator():
                for i, c in enumerate(game_clis):
                    if monrad:
                        for x in competing_clients:
                            if x.name == c.name:
                                if i == 0:
                                    x.num_white += 1
                                elif i == 1:
                                    x.num_black += 1
                    print "%s's score goes from %s to" % (c.name, str(c.score)),
                    c.score += 0.5
                    c.save()
                    print c.score
                    scores_file.write("%s\n" % c.name)
                    scores_file.flush()
            else:
                for i, c in enumerate(game_clis):
                    if monrad:
                        for x in competing_clients:
                            if x.name == c.name:
                                if i == 0:
                                    x.num_white += 1
                                elif i == 1:
                                    x.num_black += 1
                    if c.name == gameC.winner.name:
                        print c.name, "is the winner of game", g, "and their score goes from", c.score, "to",
                        c.score += 1.0
                        c.save()
                        print c.score
                        scores_file.write("%s\n" % c.name)
                        scores_file.flush()
                    #else:
                        #print c.name, "is the loser of game", g, "and their score goes from", c.score, "to"
                        #c.score -= 1
                        #c.save()
                        #print c.score
                        #scores_file.write("%s\n" % c.name)
                        #scores_file.flush()
            gameC.claimed = True
            gameC.save()
            uncompleted_games.remove(g)
        elif game_status(g) == "Failed":            
            print "Game:", g, "Failed, commiting suicide now."
            exit() # exit the game.
            # during competition just restart swiss
            uncompleted_games.remove(g)
            for x in Game.objects.all():
                x.claimed = False
                x.save()
            for x in Client.objects.all():
                x.score = 0.0
                x.save()
            current_round = 0
    return competing_clients
            
def update_standings(competing_clients):
    global current_round
    competing_clients = calc_tie_break(competing_clients)
    competing_clients = sort_players(competing_clients)
    f = open("scores.txt", 'w')
    for i in competing_clients:
        past = ""
        for k in i.past_competitors:
            past += str(k.name)
            past += "<>"
        f.write("%s+%d+%d+%d+%d+%d+%d+%s\n" % (i.name, i.score, i.buchholz, i.sumrate, i.num_black, i.num_white, current_round, past))
    f.close()    

def print_scoreBrackets(brackets):
    for i, j in brackets.items():
        for c in j:
            print c

def schedule_game(i, j, stalk):
    global start_game
    global monrad
    global dutch
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
                print c1.name, "vs.", c2.name, "found:", game_clients[0].client.name, game_clients[1].client.name, g.pk, game_clients[0].client.name == c1.name, game_clients[1].client.name == c2.name
                if game_clients[0].client.name == c1.name and game_clients[1].client.name == c2.name:
                    print g.pk
                    print "Found game", g, "already played, using that"
                    print game_clients[0].name, "vs", game_clients[1].name
                    if g.tied:
                        print "Draw!"
                        for k, c in enumerate(game_clients):
                            print "%s's score goes from %s to" % (c.client.name, str(c.client.score)),
                            c.client.score += 0.5
                            c.client.save()
                            print c.client.score
                            if monrad:
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
                                print c.client.name, "won, their score goes from", c.client.score, "to",
                                c.client.score += 1.0
                                c.client.save()
                                print c.client.score
                            if monrad:
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
                    score_game = True
                    break
            except:
                print "Found an invalid game, marking failed"
                g.status = 'Failed'
                g.save()
                    

    if not score_game:
        uncompleted_games.append(sked(c1, c2, stalk, "Tournament").pk)
    if dutch:
        i.pref_power -= 1
        j.pref_power += 1
    i.past_competitors.append(j)
    j.past_competitors.append(i)
    return i,j

def sort_players(competing_clients):
    global current_round
    competing_clients = sorted(competing_clients, key=lambda x: x.rating, reverse=True)
    if current_round > 0:
        competing_clients = sorted(competing_clients, key=lambda x: x.num_black, reverse=True)
        competing_clients = sorted(competing_clients, key=lambda x: x.sumrate, reverse=True)
        competing_clients = sorted(competing_clients, key=lambda x: x.buchholz, reverse=True)
        competing_clients = sorted(competing_clients, key=lambda x: x.score, reverse=True)
    return competing_clients
                
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
                    client = Client.objects.get(name=scoresin[0])
                    client.score = float(scoresin[1])
                    client.save()
                    i.score = float(scoresin[1])
                    i.num_black = int(scoresin[4])
                    i.num_white = int(scoresin[5])
                    current_round = int(scoresin[6])
                    past_cli = str(scoresin[7]).split("<>")
                    for x in past_cli:
                        for k in competing_clients:
                            if x == k.name:
                                i.past_competitors.append(k)
        print "Setting round to", current_round
        f.close()
    else:
        print "Setup complete, beginning round 1"
        current_round = 1
    return competing_clients


def monrad_schedule(competing_clients, stalk, tie_breaker=False):
    global current_round
    global clientNum
    to_schedule = []
    cli_on_hold = []
    a = []
    for x in competing_clients:
        realClient = Client.objects.get(name=x.name)
        x.score = realClient.score
    competing_clients = calc_tie_break(competing_clients)
    competing_clients = sort_players(competing_clients)
    for x in competing_clients:
        print x.name, x.score
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
            print "Try:", try_count, try_count_count
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










    
        """
        #while try_again:
            try_count += 1
            print "Try:", '%.2E' % decimal.Decimal(try_count)
            for x in to_schedule:
                to_schedule.remove(x)
            #random.seed(os.urandom(100))
            #random.shuffle(competing_clients)
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
                    a = []
                    try_again = False
            if not try_again:
                break
        """
    for x in to_schedule:
        schedule_game(x.pop(0), x.pop(0), stalk)
    if odd and len(to_schedule) > 0:
        c = Client.objects.get(name=y.name)
        print c.name, "gets a bye"
        c.score += 1
        c.save()
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

def calc_tie_break(competing_clients):
    for x in competing_clients:
        x.buchholz = 0
        x.sumrate = 0
        for c in competing_clients:
            if c in x.past_competitors:
                x.buchholz += c.score
                x.sumrate += c.rating
    return competing_clients

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

if __name__ == "__main__":
    main()


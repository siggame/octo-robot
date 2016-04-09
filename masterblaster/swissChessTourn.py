#
# MS&T SIG-Game 
# Author: Brandon Phelps, Daniel Bolef

# Chess swiss scheduler built for Dr. Tauritz chess AI competition and tournament. 


#TO DO:
#Confirm winner output functions
#Fix match ups
#Handle ties
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

import django
django.setup()

from thunderdome.config import game_name, req_queue_len
from thunderdome.models import Client, Game
from thunderdome.sked import sked
from utilities import webinteraction as WI

import scheduler_validating as SV
import clean_database as CD

from collections import defaultdict

uncompleted_games = []
competing_clients = []
current_round = 0

iterative_swiss = True
include_humans = False
max_rounds = 0
scores_file = open('wins.txt', 'w')
class Player():
    def __init__(self, name, score=0, rating=0):
        self.name = name
        self.score = score
        self.rank = 0
        self.rating = rating
        self.past_competitors = [] # is a list of other Players that have been versed by self in the past
        self.past_colors = []
        self.color_pref = 0
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

def main():
    global current_round
    global include_humans
    global iterative_swiss
    global max_rounds
    clientNum = 0
    parser = argparse.ArgumentParser(description='Swiss Chess scheduler')
    parser.add_argument('--h', action='store_true', help='Whether to include humans, mainly for the swiss tournament')
    parser.add_argument('--i', action='store_true', help='Schedule rounds iteratively, reseting after a winner has been found')
    parser.add_argument('--r', type=int, default=-1, help="Number of rounds to run, if iterative this is ignored")
    args = parser.parse_args()
    print args
    include_humans = args.h
    iterative_swiss = args.i
    CD.main()
    cli = Client.objects.all()
    gam = Game.objects.all()
    for x in cli:
        if not include_humans and x.language == 'Human':
            clientNum -= 1
        clientNum += 1
        x.score = 0.0
        x.save()
    
    for x in gam:
        x.swissUsed = False
        x.save()

    while clientNum > 1:
        clientNum = clientNum / 2
        max_rounds += 1
    if args.r != -1:
        max_rounds = args.r
        
    print "Include humans", include_humans
    print "Playing with", max_rounds, "rounds"
    try:
        stalk = beanstalkc.Connection(port=11300)
    except:
        raise Exception("Beanstalk error:")
    
    req_tube = "game-requests-%s" % game_name
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    while current_round <= max_rounds:
        # stats = stalk.stats_tube(req_tube)
        if not uncompleted_games:
            print "Current Round:", current_round
            if current_round > 0 and hasAWinner(create_score_brackets()):
                if iterative_swiss:
                    current_round = 0
            schedule_volley(stalk, current_round)
        else:
            score_games()
        time.sleep(1)
    stalk.close()           
    tied = False
    winner_score = 0
    win_file = open('wins.csv', 'w')
    for x in cli:
        line = (x.name, x.score, '\n')
        l = str(line)
        win_file.write(l)
        if x.score > winner_score:
            winner = x.name
            winner_score = x.score
            tied = False
        elif x.score == winner_score:
            tied = True
    if tied:
        print "There was a tie. Ties are bad."
    else:
        print "And the winner is,", winner, "!!!!!!!!!"
    
    scores_file.close()
    win_file.close()
    
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
        WI.update_clients()
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

        competing_clients = [Player(j.name, 0, j.rating) for j in clients]
        
        # assign pairing numbers to each player
        # sort the competitors by rank and elo obtained during the competition
        # give numbers from 0 - len(competing_clients) these will be perminent and used
        # lower means higher rank
        # later in the scheduling
        # for now just give random numbers

        # for testing only
        # sort clients alphabetically
        #competing_clients.sort(lambda x, y: cmp(x.name.lower(), y.name.lower()))
        
        # sort clients by elo ranking
        competing_clients.sort(key=lambda x: x.rating, reverse=True)        
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

def compatible_players(p1, p2):
    if p1 in p2.past_competitors:
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
        if t[0].color_pref == 0:
            if t[1].color_pref > 0:
                t[0], t[1] = t[1], t[0]
        elif t[1].color_pref == 0:
            if t[0].color_pref < 0:
                t[0], t[1] = t[1], t[0]
        elif math.fabs(t[0].color_pref) == math.fabs(t[1].color_pref):
            if t[0].color_pref < 0:
                t[0], t[1] = t[1], t[0]
        else:
            white = min(t, key =lambda x:x.color_pref) 
            black = max(t, key=lambda x:x.color_pref) 
            # who ever has the higher magnitude color pref gets to pick the color they need
            if math.fabs(white.color_pref) > math.fabs(black.color_pref):
                if white.color_pref < 0:
                    t = (black, white)
                elif white.color_pref > 0:
                    t = (white, black)
            elif math.fabs(white.color_pref) < math.fabs(black.color_pref):
                if black.color_pref < 0:
                    t = (white, black)
                elif black.color_pref > 0:
                    t = (black, white)
        
        group[pos], group[(len(group)/2) + pos] = t[0], t[1]
        # print t[0].name, ":", t[0].color_pref, "vs", t[1].name, ":", t[1].color_pref
        pos += 1

def schedule_group(group, bracket_type, stalk):
    # takes in a group which is a list of clients which are to be paired for games
    # group needs to be "prepared" before getting scheduled based off 9.4
    global competing_clients
    try:
        print "Group contains", len(group), "players", group[0].score
    except IndexError:
        print "group is empty"

    games = Game.objects.all()
    
    # schedule down
    pos = 0
    while pos < len(group)/2:
        i = group[pos]
        j = group[(len(group)/2) + pos]
        c1 = Client.objects.get(name=i.name)
        c2 = Client.objects.get(name=j.name)
        # first player is white

        # if a game is already computed, score the game instead of schedule
        score_game = False
        game_to_score = None
        for g in games:
            if g.status == 'Complete' and not g.swissUsed:
                current_game = Game.objects.get(pk=g.pk)
                game_clients = list(current_game.clients.all())
                if game_clients[0].name == i.name and game_clients[1].name == j.name:
                    score_game = True
                    print "Found game already played, using that"
                    print game_clients[0].name, "vs", game_clients[1].name
                    if g.tied:
                        print "Tie!"
                        for c in game_clients:
                            if c.name == i.name:
                                print sys.stdout.write(c.name)
                                print "'s score goes from", c.score, "to",
                                c.score += 0.5
                                c.save()
                                print c.score
                            if c.name == j.name:
                                print sys.stdout.write(c.name)
                                print "'s score goes from", c.score, "to",
                                c.score += 0.5
                                c.save()
                                print c.score

                    else:
                        for c in game_clients:
                            if c.name == g.winner.name:
                                print c.name, "won, their score goes from", c.score, "to",
                                c.score += 1
                                c.save()
                                print c.score
                            #if c.name != g.winner.name:
                                #print c.name, "lost, their score goes from", c.score, "to",
                                #c.score -= 1
                                #c.save()
                                #print c.score

                    g.swissUsed = True
                    break

        if not score_game:
            uncompleted_games.append(sked(c1, c2, stalk, "Swiss sked").pk)
            i.color_pref -= 1
            j.color_pref += 1
            i.past_competitors.append(j)
            j.past_competitors.append(i)
        pos += 1


def score_games():
    '''go through the games and set the corresponding scores of each game'''
    
    global competing_clients
    global current_round
    for g in list(uncompleted_games):
        if game_status(g) == "Complete":
            try:
                gameC = Game.objects.get(pk=g)
                game_clis = list(gameC.clients.all())
            except:
                pass
            if gameC.tied:
                print "Tie!"
                game_clients = Game.objects.get(pk=g)
                #c_iterator = game_clients.clients.iterator()
                #c1 = c_iterator.next()
                #c2 = c_iterator.next()
                
                for i in game_clients.clients.iterator():
                    for c in game_clis:
                        print sys.stdout.write(c.name)
                        print "'s score goes from", c.score, "to",
                        c.score += 0.5
                        c.save()
                        print c.score
                        scores_file.write("%s\n" % c.name)
                        scores_file.flush()
            else:
                for c in game_clis:
                    if c.name == gameC.winner.name:
                        print c.name, "is the winner of game", g, "and their score goes from", c.score, "to"
                        c.score += 1
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
            gameC.swissUsed = True
            gameC.save()
            uncompleted_games.remove(g)
        elif game_status(g) == "Failed":            
            print "Game:", g, "Failed attempting restart."
            print "Printing out standing"
            update_standings()
            #exit() # exit the game after outputing the stats so a manual swiss can be created.
            # during competition just restart swiss
            uncompleted_games.remove(g)
            for x in Game.objects.all():
                x.swissUsed = False
                x.save()
            for x in Client.objects.all():
                x.score = 0.0
                x.save()
            current_round = 0
            
def update_standings():
    f = open("scores.txt", 'w')
    for i in competing_clients:
        print i.name, i.score
        f.write("%s %d" % (i.name, i.score))
    f.close()    

def print_scoreBrackets(brackets):
    for i, j in brackets.items():
        for c in j:
            print c
     
if __name__ == "__main__":
    main()


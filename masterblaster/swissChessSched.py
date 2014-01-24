#
# MS&T SIG-Game 
# Author: Brandon Phelps

# Chess swiss scheduler built for Dr. Tauritz chess AI competition and tournament. 

import random
import urllib
import json
import time
import pprint

import beanstalkc
import gc

from thunderdome.config import game_name, req_queue_len
from thunderdome.models import Client, Game

from thunderdome.sked import sked

import scheduler_validating as SV

from collections import defaultdict

uncompleted_games = []
competing_clients = []
current_round = 0

class Player():
    def __init__(self, name, score=0, rating=0):
        self.name = name
        self.score = score
        self.rank = 0
        self.rating = rating
        self.color_preference = 0
        self.past_competitors = []
        self.past_colors = []
        self.color_pref = 0
        self.recieved_bye = False
        self.pairing_number = 0

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name) + str(self.score)

    def __cmp__(self, other):
        if self.recieved_bye:
            return -1
        elif other.recieved_bye:
            return 1
        else:
            if self.rating < other.rating:
                return -1
            elif self.rating > other.rating:
                return 1
            else:
                return 0

def main():
    try:
        stalk = beanstalkc.Connection()
    except:
        raise Exception("Beanstalk error:")
    
    req_tube = "game-requests-%s" % game_name
    stalk = beanstalkc.Connection()
    stalk.use(req_tube)
    while True:
        stats = stalk.stats_tube(req_tube)
        if not uncompleted_games:
            schedule_volley(stalk, current_round)
        else:
            score_games()
        time.sleep(5)
    stalk.close()           
    
def game_status(g_id):
    return Game.objects.get(pk=g_id).status

def schedule_volley(stalk, sRound):
    global competing_clients
    global uncompleted_games
    global current_round
    if sRound == 0:
        update_clients()
        #uncompleted_games.extend([i.pk for i in SV.validateSched(stalk)])
        while uncompleted_games:
            for c in list(uncompleted_games):
                if game_status(c) in ["Complete", "Failed"]:
                    uncompleted_games.remove(c)
            print("games to go: %d" % len(uncompleted_games))
            time.sleep(2)

        
        competing_clients = [Player(j.name) for j in list(Client.objects.exclude(name='bye').filter(embargoed=False))]
        # assign pairing numbers to each player
        # sort the competitors by rank and rating obtained during the competition
        # give numbers from 0 - len(competing_clients) these will be perminent and used
        # lower means higher rank
        # later in the scheduling
        # for now just give random numbers
        print("assigning pairing number")
        for i, j in enumerate(competing_clients):
            print j, " is assigned", i
            j.pairing_number = i
            
    score_brackets = defaultdict(list)
    for i in competing_clients:
        score_brackets[i.score].append(i)

    schedule_brackets(score_brackets, sRound, stalk)
    current_round += 1

def schedule_brackets(score_brackets, sRound, stalk):
    median_score = sRound/2.0
    print("Current scores")
    for i in score_brackets.keys():
        for j in score_brackets[i]:
            print j.name, j.score

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
        for i in l_group:
            print i.name, i.rating
        def player_comparison(x, y):
            if x.recieved_bye:
                return 1
            elif y.recieved_bye:
                return -1
            else:
                return x.rating - y.rating
        l_p = l_group.sort(cmp=player_comparison).pop(0)
        print "bye given to:", l_p.name
        # give bye this round to l_p
        l_p.recieved_bye = True
        l_p.score += 1

    current_bracket = 0
    print "Median score bracket value", median_score

    def prepare_group(group, sked_dir):
        """
        takes in a group and does checking and move players
        to appropriate other score groups based on 9.3
        """
        #check if the player has already played everyone in the group
        def player_rating_cmp(x, y):
            return y.rating - x.rating
        group.sort(cmp=player_rating_cmp)
        players_to_move = []
        if not score_brackets.keys():
            return

        # if sked_dir == "down"
        if sked_dir == 0:
            max_brak = max(score_brackets.keys())
        else:
            max_brak = min(score_brackets.keys())

        def player_equal(x, y):
            if x.name == y.name:
                return True
            else:
                return False
        #check for a player played everyone in group before
        for i in list(group):
            for c in i.past_competitors:
                if not player_equal(i, c):
                    break
            else:
                print "lists are equal"
                group.remove(i)
                score_brackets[max_brak].append(i)

        # check for if group contains even number of players
        if len(group) % 2 != 0:
            if sked_dir == 0:
                t = group.pop(0)
                print "moving player down", t.name
                score_brackets[max_brak].append(t)
            else:
                t = group.pop(len(group)-1)
                print "moving player up", t.name
                score_brackets[max_brak].append(t)

        if sked_dir == 0:
            print "checking for conflicts scheduling down"
            group.sort(key = lambda x: x.pairing_number)
            pos = 0
            while not group_is_compatible(group):
                # make correct pairing for highest player
                temp_group = list(group)
                i = temp_group.pop(pos)
                curent_part = temp_group.pop((len(temp_group)/2) + pos)
                if not compatible_players(i, curent_part):
                    temp_group.sort(key = lambda x: x.pairing_number)
                    j = temp_group.pop(0)
                    while temp_group:
                        temp_group.sort(key = lambda x: x.pairing_number)
                        j = temp_group.pop(0)
                        if compatible_players(i, j):
                            break
                    else:
                        # a player could not be found
                        pass
                    # a player is found and needs switching
                    cur_index = group.index(curent_part)
                    j_index = group.index(j)
                    group[cur_index], group[j_index] = group[j_index], group[cur_index]
                else:
                    pass

    
    while score_brackets:
        bracket = max(score_brackets.keys())
        temp = 0
        if bracket < median_score:
            bracket = min(score_brackets.keys())
            temp = 1
        m_group = score_brackets[bracket]
        del score_brackets[bracket]

        if bracket != median_score:
            prepare_group(m_group, temp)
        schedule_group(m_group, temp, stalk)

def group_is_compatible(group):
    pos = 0
    print "Checking if group is compatible"
    for i in group:
        print i
    while pos < len(group)/2:
        if not compatible_players(group[pos], group[(len(group)/2) + pos]):
            return False
    return True


def compatible_players(p1, p2):
    if p1 in p2.past_competitors:
        return False
    if p1.color_preference < -2 and p2.color_preference > 2:
        return False

def schedule_group(group, bracket_type, stalk):
    group.sort(key=lambda x: x.pairing_number)
    print "Group contains", len(group), "players"
    pos = 0
    while pos < len(group)/2:
        i = group[pos]
        j = group[(len(group)/2) + pos]
        c1 = Client.objects.get(name=i.name)
        c2 = Client.objects.get(name=j.name)
        # first player is white
        uncompleted_games.append(sked(c1, c2, stalk, "Swiss sked").pk)
        i.color_pref -= 1
        j.color_pref += 1
        i.past_competitors.append(j)
        j.past_competitors.append(i)
        pos += 1

def score_games():
    global competing_clients
    for g in list(uncompleted_games):
        if game_status(g) == "Complete":
            uncompleted_games.remove(g)
            for c in competing_clients:
                                
                if c.name == Game.objects.get(pk=g).winner.name:
                    c.score += 1
                    print c.name, "is winner of", g, "and now has a score of", c.score
                    break
        elif game_status(g) == "Failed":
            print "Game:", g, "Failed aborting automated swiss, switch to manual swiss."
            print "Printing out standing"
            for i in competing_clients:
                print i.name, i.score
            f = open("scores.txt", 'w')
            
            f.close()
            exit()
       
def print_scoreBrackets(brackets):
    for i, j in brackets.items():
        for c in j:
            print c
     
def update_clients():
    print 'updating clients'
    api_url = "http://megaminerai.com/api/repo/tags/?competition=%s" % game_name
    try:
        f = urllib.urlopen(api_url)
        data = json.loads(f.read())
        f.close()
    except:
        print "couldn't read updated clients is website up? is the right api_url: %s" % api_url

    for block in data:
        if block['tag'] is None:
            block['tag'] = ''
        if Client.objects.filter(name=block['name']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['name'])
        if client.current_version != block['tag']:
            client.embargoed = False # only place an embargo can be broken
            client.current_version = block['tag']
            client.save()


def makeClient(block):
    '''Make a client object from the provided API data block'''
    client = Client.objects.create()
    client.name = block['name']
    client.current_version = block['tag']
    client.repo = block['path']
    client.embargoed = False # True # odd so the first client obtained from the api is embargoed?
    client.eligible = True # tournament eligible
    client.seed = 0
    client.save()
    return client


if __name__ == "__main__":
    main()


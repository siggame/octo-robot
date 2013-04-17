import sys
import time
import os 
import string
import cStringIO

from copy import copy

from time import sleep

import sexpdata

from objects import Fish, Tile, Animation, Player
from statgetters import *


class GameStatus():

    def __init__(self):
        self.info = ''
        self.fish = []
        self.tile = []
        self.animation = []
        self.stats = []
        self.player = []

    def add_info(self, info):
        if info[0] == 'animations':
            self.add_animations(info[1:])
            return
        #print info
        for j in info:
            if j[0] == 'game':
                self.stats = copy(j[1:])

            elif j[0] == 'Fish':
                for i in j[1:]:
                    self.fish.append(Fish(i))
            elif j[0] == 'Tile':
                for i in j[1:]:
                    self.tile.append(Tile(i))
            elif j[0] == 'Player':
                for i in j[1:]:
                    self.player.append(Player(i))

    def add_animations(self, anim_list):
        for i in anim_list:
            self.animation.append(Animation(i))

    def remove_object(self, name, id_num):
        if name == 'Fish':
            for i in self.fish:
                if i.stats[0] == id_num:
                    self.fish.remove(i)

        elif name == 'Tile':
            for i in self.tile:
                if i.stats[0] == id_num:
                    self.tile.remove(i)

    def add_object(self, name, obj):
        if name == 'Fish':
            self.fish.append(obj)
        elif name == 'tile':
            self.tile.append(obj)

    def print_info(self):
        print "GAME!"
        print self.stats
        print "FISH!"
        for i in self.fish:
            print i.stats
        print "TILE!"
        for i in self.tile:
            print i.stats
        print "ANIMATION!"
        for i in self.animation:
            print i.stats

    def replace_object(self, name, obj):
        if name == 'Tile':
            for i in self.tile:
                if i.stats[0] == obj.stats[0]:
                    index = self.tile.index(i)
                    self.tile.remove(i)
                    self.tile.insert(index, obj)


def remove_dups(info_list):
    ids_seen = []

    for i in info_list:
        if i not in ids_seen:
            ids_seen.append(i)

    return ids_seen


def update_game_state(current_state, next_state, boold):

    for i in next_state.tile:
        current_state.replace_object('Tile', i)


def build_game_states(game_turns):

    game_states = [copy(game_turns[0]), copy(game_turns[1])]

    for i in xrange(1, len(game_turns) - 1):     
        current_game_state = copy(game_states[i])

        next_game_state = copy(game_turns[i + 1])

        update_game_state(current_game_state, next_game_state)

        game_states.append(copy(current_game_state))

    return game_states


def parse_info(parsed_log):

    game_turns = []

    tempG = GameStatus()

    for i in parsed_log:
        
        if i[0] == 'status':
            tempG = GameStatus()
            tempG.add_info(i[1:])
        
            game_turns.append(tempG)
        elif i[0] == 'animations':
            
            game_turns[len(game_turns)-2].add_info(i)
            
    return game_turns    
    
    
def parse_game_turns(gamelog):
    gamelog = '(' + gamelog + ')'
    parsed_log = sexpdata.loads(gamelog)
    game_turns = parse_info(parsed_log)
    
    return game_turns

def parse_game_log(gamelog):
    
    gamelog = '(' + gamelog + ')'
    
    parsed_log = sexpdata.loads(gamelog)
    
    game_turns = parse_info(parsed_log)

    game_states = build_game_states(game_turns)

    return game_turns, game_states



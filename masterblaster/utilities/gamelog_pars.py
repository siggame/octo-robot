import sys
import time
import os

import string
import cStringIO

from objects import Player, Players, Fish, Tile
from statgetters import *
#from grapher import *


class GameStatus():
  info = ''
  turn_number = 0
  deaths = 0

  fish = []
  tiles = []

  def __init__(self):
    self.info = ''
    self.turn_number = ''
    self.deaths = ''
    self.fish = []
    self.tiles = []

  def add_info(self, c):
    self.info = self.info + c
    
  def parse_info(self):
    temp_stat = parse_till_paren('game', self.info)
   
    self.turn_number = int(temp_stat.strip().split(' ')[0])
    self.deaths = parse_count('death', self.info)
    self.fish = parse_object_stats('Fish', self.info)
    self.tiles = parse_object_stats('Tile', self.info)

  def print_info(self):    
    print 'Turn number: ', self.turn_number, ' deaths: ', self.deaths

def parse_till_paren(search_word, k):
  build_word = False
  build_stats = False

  paren_stop = False
  current_word = ''
  stats = ''

  for c in k:
    if paren_stop and c == ')':
      return stats
    if c =='\"' and not build_word:
      build_word = True
    elif build_word:
      if c == '\"':
        build_word = False
      else:
        current_word = current_word + c
      
    if build_stats:
      stats = stats + c
  
    if not build_word:
      if current_word == search_word:
        build_stats = True
        paren_stop = True

def parse_gamelog(gamelog):
  k = gamelog
  build_word = False
  build_status = False

  current_word = ''

  game_status = ''
  anim_found = False
  paren_count = 0
  
  game_statuses = []
  
  game_statuses.append(GameStatus())

  for c in k:
    if c == '(':
      paren_count = paren_count + 1
    if c == ')':
      paren_count = paren_count - 1
    
    if anim_found and paren_count == 0:
      build_status = False
      anim_found = False
      #game_statuses[len(game_statuses)-1].print_info()
      game_statuses[len(game_statuses)-1].parse_info()
      game_statuses.append(GameStatus())
      

    if c == '\"' and not build_word:
      build_word = True
    elif build_word:
      if c =='\"':
        build_word = False
        #print current_word
      else:
        current_word = current_word + c

    if build_status:
      game_statuses[len(game_statuses)-1].add_info(c)

    if not build_word:
      if current_word == 'Status' or current_word == 'status':
        build_status = True
      if current_word == 'animations':
        anim_found = True
      current_word = ''
    
    #sys.stdout.write('%s' % c)
    #sys.stdout.flush()
    #if c == ')':
    #  sys.stdout.write('%d' % paren_count)
    #  sys.stdout.flush()

  game_statuses.pop()
  #for gameStas in game_statuses:
  #  gameStas.print_info()

  return game_statuses

def parse_object_stats(search_word, k):

  build_word = False
  build_stats = False
  collect_stats = False
  object_stat_collect = False

  current_word = ''
  stats = '' 

  objects = []
  
  paren_fal = False

  if search_word == 'Creature':
    objects.append(Creature())
  elif search_word == 'Plant':
    objects.append(Plant())

  for c in k:
    if c == '(':
      paren_fal = False
    elif c == ')':
      if paren_fal and object_stat_collect:
        break
      paren_fal = True
      
    if not object_stat_collect:
      if c =='\"' and not build_word:
        build_word = True
      elif build_word:
        if c == '\"':
          build_word = False
        else:
          current_word = current_word + c

      if not build_word:
        #print current_word

        if current_word == search_word:
          build_stats = True
        current_word = ''

      if build_stats:
        object_stat_collect = True
        
    else:
      if c =='(' and not collect_stats:
        collect_stats = True
      elif c == ')' and collect_stats:
        collect_stats = False
        objects[len(objects)-1].parse_info()

        if search_word == 'Creature':
          objects.append(Creature())
        elif search_word == 'Plant':
          objects.append(Plant())
  
      elif collect_stats:
        objects[len(objects)-1].add_info(c)

  objects.pop()
  return objects

def parse_count(search_word, k):
  return k.count(search_word)

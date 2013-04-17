from copy import copy


class Fish():
  stats = []

  def __init__(self, info):
    self.stats = copy(info)

class Tile():
  stats = []

  def __init__(self, info):
    self.stats = copy(info)

class Animation():
  stats = []  
  def __init__(self, info):
    self.stats = copy(info)

class Player():
  stats = []
  def __init__(self, info):
    self.stats = copy(info)

class Players():
  
  info = ''
  players = []
  winner = -1
  def __init__(self):
    self.players = [Player(), Player()]
    self.winner = -1

  def add_info(self, c):
    self.info = self.info + c
  
  def parse_info(self):
    paren1 = False
    paren2 = False
    paren_count = 0
    
    for c in self.info:
      if c == '(':
        if not paren1 and not paren2:
          paren1 = True
        paren_count = paren_count + 1

      elif c == ')':
        if paren1 and not paren2:
          paren2 = True
          paren1 = False
        paren_count = paren_count - 1

      
      if paren1 and paren_count == 1 and c != '(':
        self.players[0].add_info(c)
      elif paren2 and paren_count == 1 and c != '(':
        self.players[1].add_info(c)

    self.players[0].parse_info()
    self.players[1].parse_info()

  def print_info(self):
    print self.players[0].print_info()
    print self.players[1].print_info()

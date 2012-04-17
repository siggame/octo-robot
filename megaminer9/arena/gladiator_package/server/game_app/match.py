from base import *
from matchUtils import *
from objects import *
import networking.config.config
from collections import defaultdict
from networking.sexpr.sexpr import *
import os
import itertools
import scribe
import random
import copy

Scribe = scribe.Scribe

def loadClassDefaults(cfgFile = "config/defaults.cfg"):
  cfg = networking.config.config.readConfig(cfgFile)
  for className in cfg.keys():
    for attr in cfg[className]:
      setattr(eval(className), attr, cfg[className][attr])

class Match(DefaultGameWorld):
  def __init__(self, id, controller):
    self.id = int(id)
    self.controller = controller
    DefaultGameWorld.__init__(self)
    self.scribe = Scribe(self.logPath())
    self.addPlayer(self.scribe, "spectator")
    self.turnNumber = -1
    self.playerID = -1
    self.gameNumber = id
    self.round = -1
    self.victoriesNeeded = self.victories

  def addPlayer(self, connection, type="player"):
    connection.type = type
    if len(self.players) >= 2 and type == "player":
      return "Game is full"
    if type == "player":
      self.players.append(connection)
      try:
        self.addObject(Player, [connection.screenName, self.startTime, 0, self.startEnergy])
      except TypeError:
        raise TypeError("Someone forgot to add the extra attributes to the Player object initialization")
    elif type == "spectator":
      self.spectators.append(connection)
      #If the game has already started, send them the ident message
      if (self.turn is not None):
        self.sendIdent([connection])
    return True

  def removePlayer(self, connection):
    if connection in self.players:
      if self.turn is not None:
        winner = self.players[1 - self.getPlayerIndex(connection)]
        self.declareWinner(winner, 'Opponent Disconnected')
      self.players.remove(connection)
    else:
      self.spectators.remove(connection)

  def start(self):
    if len(self.players) < 2:
      return "Game is not full"
    if self.winner is not None or self.turn is not None:
      return "Game has already begun"    
   
    self.turn = self.players[-1]
    self.turnNumber = -1

    self.shipordering = ["maxAttacks", "maxMovement", "maxHealth", "type", "cost", "radius", "range",
                     "damage", "selfDestructDamage", "maxMovement", "maxAttacks", "maxHealth"]

    self.typeordering = ["type", "cost", "radius", "range", "damage", "selfDestructDamage",
                         "maxMovement", "maxAttacks", "maxHealth"]
    self.warpGate = [cfgUnits["Warp Gate"][value] for value in self.shipordering]
    self.spawnableTypes = cfgUnits.keys()
    self.spawnableTypes.remove("Warp Gate")
    self.spawnableTypes.remove("Mine")
    self.shipChain = []

    self.nextRound()
    self.nextTurn()
    return True

  def nextRound(self):
    #Handles logic for starting a new round
    self.round += 1

    print "YOU ARE ENTERING A NEW ROUND", self.round, 'Score:', [player.victories for player in self.objects.players]

    #first get rid of all shiptypes and ships available that round, then put into a new subset of available ship types
    for obj in self.objects.values():
      if isinstance(obj, ShipType) or isinstance(obj, Ship):
        self.removeObject(obj)

    for player in self.objects.players:
      #Give players energy initially each round
      player.energy = self.startEnergy
      player.time = self.startTime
      player.warping = []
      player.warpGate = self.addObject(Ship, [player.id, (player.id * 2 - 1) * (self.mapRadius)/2, 0] + self.warpGate)
    # Get the set of ships to be used this round
    using = set()
    while len(using) < self.shipsPerRound:
      # Add another use for all ships if you run out
      if len(self.shipChain) == 0:
        self.shipChain += self.spawnableTypes
      # randomly select a new ship that is not already in use
      choice = random.choice([shipType for shipType in self.shipChain if shipType not in using])
      # add to the set and remove from the chain
      using.add(choice)
      self.shipChain.remove(choice)
    print sorted(using)
    for shipType in using:
      self.addObject(ShipType, [cfgUnits[shipType][value] for value in self.typeordering])
    return True

  def nextTurn(self):
    self.turnNumber+=1
    if self.turn == self.players[0]:
      self.turn = self.players[1]
      self.playerID = 1
    elif self.turn == self.players[1]:
      self.turn = self.players[0]
      self.playerID = 0
    else:
      return "Game is over." 

    for obj in self.objects.values():
      obj.nextTurn()
    self.checkRoundWinner()

    if self.winner is None:
      self.sendStatus([self.turn] +  self.spectators)
    else:
      self.sendStatus(self.spectators)
    self.animations = ["animations"]
    return True

  def declareRoundWinner(self, winners, message):
    self.animations.append(['round-victory', -17, message])
    self.sendStatus(self.spectators)
    for winner in winners:
      winner.victories += 1
    self.checkWinner()
    if self.winner is None:
      self.turnNumber = 0
      self.nextRound()

  def smartEnd(self):
    player1 = self.objects.players[0]
    player2 = self.objects.players[1]
    #Find the energy of the lowest type cost of that rouond
    cost = min([shipType.cost for shipType in self.objects.shipTypes])
    if self.turnNumber >= self.turnLimit:
      return True
    if player1.energy < cost:
      if len([ship for ship in self.objects.ships if ship.owner == 0]) < 2:
        if len(player1.warping) == 0: 
          if player1.warpGate.health < player2.warpGate.health:
            return True
    if player2.energy < cost:
      if len([ship for ship in self.objects.ships if ship.owner == 1]) < 2:
        if len(player2.warping) == 0: 
          if player2.warpGate.health < player1.warpGate.health:
            return True
    return False
  
  def checkRoundWinner(self):
    player1 = self.objects.players[0]
    player2 = self.objects.players[1]
    
    # Descruction round end
    if player1.warpGate.health <= 0 and player2.warpGate.health <= 0:
      self.declareRoundWinner([player1, player2], "Draw due to mutual warp gate destruction")
    elif player2.warpGate.health <= 0:
      self.declareRoundWinner([player1], player1.playerName + " wins by warp gate destruction")
    elif player1.warpGate.health <= 0:
      self.declareRoundWinner([player2], player2.playerName + " wins by warp gate destruction")
    # End by turn limit
    elif self.smartEnd():
      if player1.warpGate.health > player2.warpGate.health:
        self.declareRoundWinner([player1], player1.playerName + " wins by warp gate shield integrity")
      elif player1.warpGate.health < player2.warpGate.health:
        self.declareRoundWinner([player2], player2.playerName + " wins by warp gate shield integrity")
      else:
        # score
        scores = [player1.energy, player2.energy]
        for ship in self.objects.ships:
          scores[ship.owner] += ship.cost
        # includes warping in ships
        for player in self.objects.players:
          for ship in player.warping:
            scores[ship.owner] += cfgUnits[ship.type]["cost"]
        if scores[0] > scores[1]:
          self.declareRoundWinner([player1], player1.playerName + " wins by total living army value")
        elif scores[0] < scores[1]:
          self.declareRoundWinner([player2], player2.playerName + " wins by total living army value")
        else:
          self.declareRoundWinner([player1, player2], "Draw by because you are twins")

  def checkWinner(self):
    player1 = self.objects.players[0]
    player2 = self.objects.players[1]
    # Strictly player 1 victory
    if player1.victories >= self.victories and player1.victories > player2.victories:
      self.declareWinner(self.players[0], player1.playerName + " has won the game %i-%i"%(player1.victories, player2.victories))
    # Strictly player 2 victory
    elif player2.victories >= self.victories and player2.victories > player1.victories:
      self.declareWinner(self.players[1], player2.playerName + " has won the game %i-%i"%(player2.victories, player1.victories))
    # Tied last round
    elif player1.victories > self.victories and player2.victories > self.victories:
      self.declareWinner(random.choice(self.players), "The game is a tie")

  def declareWinner(self, winner, reason=''):
    print "Game", self.id, "over"
    self.winner = winner
    self.sendStatus(self.spectators)
    msg = ["game-winner", self.id, self.winner.user, self.getPlayerIndex(self.winner), reason]
    self.scribe.writeSExpr(msg)
    self.scribe.finalize()
    self.removePlayer(self.scribe)

    for p in self.players + self.spectators:
      p.writeSExpr(msg)

    self.sendStatus([self.turn])
    self.playerID ^= 1
    self.sendStatus([self.players[self.playerID]])
    self.playerID ^= 1
    self.turn = None
    
  def logPath(self):
    return "logs/" + str(self.id) + ".glog"

  @derefArgs(ShipType, None, None)
  def warpIn(self, object, x, y):
    return object.warpIn(x, y, )

  @derefArgs(Player, None)
  def talk(self, object, message):
    return object.talk(message, )

  @derefArgs(Ship, None, None)
  def move(self, object, x, y):
    return object.move(x, y, )

  @derefArgs(Ship)
  def selfDestruct(self, object):
    return object.selfDestruct()

  @derefArgs(Ship, Ship)
  def attack(self, object, target):
    return object.attack(target, )


  def sendIdent(self, players):
    if len(self.players) < 2:
      return False
    list = []
    for i in itertools.chain(self.players, self.spectators):
      list += [[self.getPlayerIndex(i), i.user, i.screenName, i.type]]
    for i in players:
      i.writeSExpr(['ident', list, self.id, self.getPlayerIndex(i)])

  def getPlayerIndex(self, player):
    try:
      playerIndex = self.players.index(player)
    except ValueError:
      playerIndex = -1
    return playerIndex

  def sendStatus(self, players):
    for i in players:
      i.writeSExpr(self.status(i))
      if i.type != "player":
        i.writeSExpr(self.animations)
    return True


  def status(self, connection):
    msg = ["status"]

    msg.append(["game", self.turnNumber, self.playerID, self.gameNumber, self.round, self.victoriesNeeded, self.mapRadius])

    typeLists = []
    typeLists.append(["Player"] + [i.toList() for i in self.objects.values() if i.__class__ is Player])
    typeLists.append(["Ship"] + [i.toList() for i in self.objects.values() if i.__class__ is Ship and 
                     (not i.isStealthed or i.owner == self.playerID or connection.type != "player")])
    typeLists.append(["ShipType"] + [i.toList() for i in self.objects.values() if i.__class__ is ShipType])

    msg.extend(typeLists)

    return msg


loadClassDefaults()


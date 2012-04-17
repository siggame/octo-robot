import math
import networking.config.config
#Initializes the cfgUnits file
#Initializes the cfgUnits file
cfgUnits = networking.config.config.readConfig("config/units.cfg")
for key in cfgUnits.keys():
  cfgUnits[key]['type'] = key

def distance(fromX, fromY, toX, toY):
  return int(math.ceil(math.sqrt((fromX-toX)**2 + (fromY-toY)**2)))

def inRange(x1, y1, rad1, x2, y2, rad2):
  return distance(x1, y1, x2, y2) <= rad1 + rad2

class ShipDescription:
  def __init__(self, game, id, type, cost, radius, range, damage, selfDestructDamage, maxMovement, maxAttacks, maxHealth):
    self.game = game
    self.id = id
    self.type = type
    self.cost = cost
    self.radius = radius
    self.range = range
    self.damage = damage
    self.selfDestructDamage = selfDestructDamage
    self.maxMovement = maxMovement
    self.maxAttacks = maxAttacks
    self.maxHealth = maxHealth

  def toList(self):
    value = [
      self.id,
      self.type,
      self.cost,
      self.radius,
      self.range,
      self.damage,
      self.selfDestructDamage,
      self.maxMovement,
      self.maxAttacks,
      self.maxHealth,
      ]
    return value

  def nextTurn(self):
    pass

class Player:
  def __init__(self, game, id, playerName, time, victories, energy):
    self.game = game
    self.id = id
    self.playerName = playerName
    self.time = time
    self.victories = victories
    self.energy = energy
    self.warping = []
    self.warpGate = 0

  def toList(self):
    value = [
      self.id,
      self.playerName,
      self.time,
      self.victories,
      self.energy,
      ]
    return value

  def nextTurn(self):
    #Ships warp in at the beginning of that player's turn
    if self.game.playerID == self.id:
      for warp in self.warping:
        #Uses a list of ship values in the config to get all of the ships stats
        shipStats = [cfgUnits[warp[0]][value] for value in self.game.shipordering]
        #Adds the ship with the retreived stats to the game
        self.game.addObject(Ship, [self.id, warp[1], warp[2]] + shipStats)
      self.warping = []

  def talk(self, message):
    # Ensure I can't make my opponent talk
    if self.game.playerID == self.id:
      self.game.animations.append(['player-talk', self.id, message])
    else:
      return "You can't speak for your opponent"
    return True


class Ship(ShipDescription):
  def __init__(self, game, id, owner, x, y, attacksLeft, movementLeft, health, type, cost, radius, range, damage, selfDestructDamage, maxMovement, maxAttacks, maxHealth):
    self.game = game
    self.id = id
    self.type = type
    self.cost = cost
    self.radius = radius
    self.range = range
    self.damage = damage
    self.selfDestructDamage = selfDestructDamage
    self.maxMovement = maxMovement
    self.maxAttacks = maxAttacks
    self.maxHealth = maxHealth
    self.owner = owner
    self.x = x
    self.y = y
    self.attacksLeft = attacksLeft
    self.movementLeft = movementLeft
    self.health = health
    self.isStealthed = self.type == "Stealth"
    self.targeted = set()

  def toList(self):
    value = [
      self.id,
      self.type,
      self.cost,
      self.radius,
      self.range,
      self.damage,
      self.selfDestructDamage,
      self.maxMovement,
      self.maxAttacks,
      self.maxHealth,
      self.owner,
      self.x,
      self.y,
      self.attacksLeft,
      self.movementLeft,
      self.health,
      ]
    return value
    
  def allInRange(self, owner, range = None):
    result = []
    if range == None:
      range = self.range
    for ship in self.game.objects.ships:
      if ship.owner == owner and inRange(self.x, self.y, range, ship.x, ship.y, ship.radius):
        result.append(ship)
    return result

  def nextTurn(self):
    #Healing other ships in range of support ship      
    self.targeted = set()
    #Healing other ships in range of engineering ship      
    if self.owner == self.game.playerID and self.type == "Support":
      for healed in self.allInRange(self.owner):
        if healed.id != self.id:
          healed.health += int(healed.maxHealth * self.damage / 100.0)
          if healed.health > healed.maxHealth:
            healed.health = healed.maxHealth
          
    if self.owner == self.game.playerID:
      if self.movementLeft == -1 and self.attacksLeft == -1:
        self.movementLeft = 0
        self.attacksLeft = 0
      else:
        self.movementLeft = self.maxMovement
        if self.type != "Mine Layer":
          self.attacksLeft = self.maxAttacks
        else:
          # For Mine Layer's, you get 1 attack if you have any mines left, otherwise you get 0 attacks
          self.attacksLeft = min(1, self.maxAttacks)
      if self.type == "Stealth":
        if self.isStealthed == False:
          self.game.animations.append(['stealth', self.id])
          self.isStealthed = True
                    
  def move(self, x, y):
    #moved is the distance they've moved, where they were to where they're going
    moved = distance(self.x, self.y, x, y)
    if self.owner != self.game.playerID:
      return "You cannot move your oppenent's %s %i "%(self.type,self.id)
    #if they're trying to move outside the map
    elif distance(0, 0, x, y) + self.radius > self.game.mapRadius:
      return "We're deep in Space, corner of No and Where. You take extra care to not move your %s %i out of the map."%(self.type,self.id)
    #check if they can't move that far
    elif self.movementLeft < moved:
      return "You cannot move your %s %i %i spaces away."%(self.type,self.id,moved)#think of something clever here
    #have to move somewhere..yeah.
    elif moved == 0:
      return "Must move your %s %i somewhere"%(self.type,self.id)
    
    #successful move, yay!
    self.game.animations.append(['move', self.id, self.x, self.y, x, y]) #move animation for those visualizer guys
    self.x = x
    self.y = y
    self.movementLeft -= moved

    return True

  def selfDestruct(self):
    if self.type == "Warp Gate":
      return "You cannot explode your Warp Gate"
    elif self.owner != self.game.playerID:
      return "You can't make your opponenet's %s %i self destuct"%(self.type,self.id)
    for target in self.allInRange(self.owner^1, self.radius):   
      target.health -= self.selfDestructDamage
      if target.health <= 0:
        self.game.removeObject(target)
    self.game.removeObject(self)
    self.game.animations.append(['self-destruct', self.id])
    return True

  def attack(self, target):
    if self.owner != self.game.playerID:
       return "You cannot make your enemy's %s %i attack"%(self.type,self.id)
    if self.attacksLeft <= 0:
      return "Your %s %i has no attacks left"%(self.type,self.id)
    if target.id in self.targeted:
      return "You have already commanded %s %i to attack %s %i"%(self.type,self.id,target.type,target.id)
    if self.type == "Mine Layer":
      #Adding a new mine to the game
      shipStats = [cfgUnits["Mine"][value] for value in self.game.shipordering]
      self.game.addObject(Ship, [self.game.playerID, self.x, self.y] + shipStats)
      self.maxAttacks -= 1
      self.attacksLeft -= 1
      self.targeted.add(self.id)
      return True
    #Whenever the EMP attacks any target it will use an EMP
    if self.type == 'EMP':
      self.maxAttacks -= 1
      self.attacksLeft -= 1
      foe = self.owner^1
      for ship in self.allInRange(foe):
        if ship.type != "Mine":
          ship.attacksLeft = -1
          ship.movementLeft = -1
          self.game.animations.append(['attack',self.id,ship.id])
    elif target.owner == self.owner:
      return "No friendly fire. Your %s %i cannot attack your %s %i "%(self.type,self.id,target.type,target.id)
    elif not self.inRange(target):
      return "%s %i's target, %s %i, is too far away"%(self.type, self.id,target.type,target.id)
    elif target.isStealthed:
      return "HACKER! You cannot attack %i when it is stealthed!"%(target.id)
    else:
      #Factor in damage buff for Support ships neat opponent
      modifier = 1
      for unit in self.game.objects.ships:
        if unit.owner == self.owner and unit.type == "Support":
          if unit.inRange(target):
            #Increment the damage modifier for each radar in range
            modifier+= (unit.damage / 100.0)
      self.game.animations.append(['attack', self.id, target.id])
      target.health-= int(self.damage*modifier)
      self.attacksLeft -= 1
      if target.health <= 0:
        self.game.removeObject(target)
      self.targeted.add(target.id)
      if self.type == 'Stealth':
        self.isStealthed = False
        self.game.animations.append(['de-stealth',self.id])
    return True
    
  def inRange(self, target):
    return inRange(self.x, self.y, self.range, target.x, target.y, target.radius)

class ShipType(ShipDescription):
  def __init__(self, game, id, type, cost, radius, range, damage, selfDestructDamage, maxMovement, maxAttacks, maxHealth):
    self.game = game
    self.id = id
    self.type = type
    self.cost = cost
    self.radius = radius
    self.range = range
    self.damage = damage
    self.selfDestructDamage = selfDestructDamage
    self.maxMovement = maxMovement
    self.maxAttacks = maxAttacks
    self.maxHealth = maxHealth

  def toList(self):
    value = [
      self.id,
      self.type,
      self.cost,
      self.radius,
      self.range,
      self.damage,
      self.selfDestructDamage,
      self.maxMovement,
      self.maxAttacks,
      self.maxHealth,
      ]
    return value

  def nextTurn(self):
    pass

  def warpIn(self, x, y):
    player = self.game.objects.players[self.game.playerID]
    if distance(0, 0, x, y) + self.radius > self.game.mapRadius:
      return "Warping in that ship to %i, %i would be lost in space...forever"%(x, y)
    elif player.energy < self.cost:
      return "You need to not be poor to buy that %s"%(self.type)
    elif distance(player.warpGate.x, player.warpGate.y, x, y) + self.radius > player.warpGate.radius:
      return "You must spawn that %s closer to your Warp Gate"%(self.type)
    else:
      #spawn the unit with its stats, from units.cfg in config directory
      #Add unit to queue to be warped in at the beginning of this player's next turn
      player.warping.append([self.type, x, y])
      player.energy -= self.cost
    return True


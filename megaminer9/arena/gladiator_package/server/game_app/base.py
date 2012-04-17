from ObjectHolder import ObjectHolder
class GameWorld(object):
  """
  Base class for a game world object
  """
  def __init__(self):
    self.nextid = 0
    self.maxid = 2147483647
    self.turnNumber = 0
    self.players = []
    self.spectators = []
    self.turn = None #the player whose turn it is;
             #None before and after the game.
    self.winner = None #the player who won the game;
               #None before and during the game
    self.objects = ObjectHolder() #key: object's id
                #value: instance of the object
    self.animations = ["animations"]

  def addObject(self, objType, arguments=[]):
    """
    Used to create new objects
    """
    id = self.nextid
    self.nextid+=1
    self.animations.append(["add", id])
    self.objects[id] = objType(*([self, id]+arguments))
    return self.objects[id]

  def removeObject(self, oldObject):
    self.animations += [["remove", oldObject.id]]
    del self.objects[oldObject.id]

DefaultGameWorld = GameWorld

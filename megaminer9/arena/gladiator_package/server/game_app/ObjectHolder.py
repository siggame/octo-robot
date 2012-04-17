import objects

class ObjectHolder(dict):
  def __init__(self, *args, **kwargs):
    dict.__init__(self, *args, **kwargs)
    self.shipDescriptions = []
    self.shipTypes = []
    self.players = []
    self.ships = []

  def __setitem__(self, key, value):
    if key in self:
      self.__delitem__(key)
    dict.__setitem__(self, key, value)
    if isinstance(value, objects.ShipDescription):
      self.shipDescriptions.append(value)
    if isinstance(value, objects.ShipType):
      self.shipTypes.append(value)
    if isinstance(value, objects.Player):
      self.players.append(value)
    if isinstance(value, objects.Ship):
      self.ships.append(value)

  def __delitem__(self, key):
    value = self[key]
    dict.__delitem__(self, key)
    if value in self.shipDescriptions:
      self.shipDescriptions.remove(value)
    if value in self.shipTypes:
      self.shipTypes.remove(value)
    if value in self.players:
      self.players.remove(value)
    if value in self.ships:
      self.ships.remove(value)

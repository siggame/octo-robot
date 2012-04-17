from networking.sexpr.sexpr import *
import bz2
import os

class Scribe:
  """
  A mock connection that joins every game as a 
  spectator and creates game logs.
  """
  def __init__(self, logPath):
    self.messages = [] #A list of messages this player has received
    self.user = "Scribe"
    self.screenName = "Scribe"
    self.logPath = logPath
    if (not os.path.exists("logs/")):
      os.mkdir("logs/")
    if (os.path.exists(self.logPath)):
      os.remove(self.logPath)
    self.log = bz2.BZ2File(self.logPath+".part", "w")
    self.writeSExpr(["gameName", "Space"])

  def writeSExpr(self, message):
    self.log.write(sexpr2str(message))

  def finalize(self):
    self.log.close()
    os.rename(self.logPath+".part", self.logPath)


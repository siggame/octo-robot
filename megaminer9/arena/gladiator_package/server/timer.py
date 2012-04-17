import aspects

from game_app.match import Match
from twisted.internet import reactor
from time import time
games = []

def install():
  def wrapNextTurn(func):
    def inner(self):
      # Gets the time that the player returned their message
      currentTime = time()
      # If this isn't the first time, calculate the time elapsed
      try: timeSpent = currentTime - self.turnStartTime
      except AttributeError: timeSpent = 0
      # Make certain this game is tracked by the timeout tick
      if self not in games:
        games.append(self)
      # determine who's turn it is
      justWent, aboutToGo = (0, 1) if self.turn == self.players[0] else (1, 0)
      # charge the player that just went for the time they took
      self.objects.players[justWent].time -= timeSpent
      if self.objects.players[justWent].time <= 0:
        self.declareWinner(self.players[aboutToGo], 'Player %d ran out of time'%(justWent + 1))
        games.remove(self)
      # calls the turn update
      result = func(self)
      # gives the player who is about to go some more time
      self.objects.players[aboutToGo].time += self.timeInc
      # records the start of the turn
      self.turnStartTime = time()
      return result
    return inner

  aspects.wrap_function(Match.nextTurn, wrapNextTurn)

  def tick():
    currentTime = time()
    for i in games:
      p = i.objects.players
      if len(i.players) > 1:
        elapsed = currentTime - i.turnStartTime
        if i.turn == i.players[0]:
          if p[0].time < elapsed:
            i.declareWinner(i.players[1], 'Player 1 ran out of time')
        elif i.turn == i.players[1]:
          if p[1].time < elapsed:
            i.declareWinner(i.players[0], 'Player 2 ran out of time')
        else:
          games.remove(i)
      else:
        games.remove(i)

    reactor.callLater(1, tick)

  reactor.callWhenRunning(reactor.callLater, 1, tick)


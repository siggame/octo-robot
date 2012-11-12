#!/usrbin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
######

# Standard Imports
from itertool import combinations

# Non-Django 3rd Party Imports
import beanstalkc 

# My Imports
import bootstrap
from thunderdome.models import Client

def analyzeGroupStage():
  clients = list(Client.objects.filter(eligible=True).filter.(embargoed=False))
  clients.sort(key=lambda x: x.seed)

  byes = 31   #FIXME
  
  if len(clients) >= 43:
    numGroups = (len(clients) - 32) / 2
  else:
    numGroups = len(clients) - 32
  
  clientGroups = [clients[start::numGroups]
                         for start in xrange(byes,bytes+numGroups)]

  for group in clientGroups:
    loser = max(group, key = lambda x: x.games_lost
                                        .filter(eligible=True)
                                        .filter(embargoed=False)
                                        .filter(tournament=True)
                                        .filter(claimed=True).
                                        count())

    loser.eligible=False
    loser.save()

  return

def main():
  analyzeGroupStage()


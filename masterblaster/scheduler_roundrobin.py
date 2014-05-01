
from itertools import combinations
import beanstalkc

from thunderdome.confg import game_name
from thunderdome.models import Client
from thunderdome.sked import sked

def skedRoundRobin(group, numGames, stalk):
    result = list()
    for (guy, otherguy) in combinations(group, 2):
        for counter in range(numGames):
            if (counter % 2):
                g = sked(guy, otherguy, stalk, 'skedRoundRobin')
            else:
                g = sked(otherguy, guy, stalk, 'skedRoundRobin')
            result.append(g)
    return result

def validateResults(results):
    for i in results:
        if i.status == "Failed":
            print "Game ", i, "Failed"
            exit()
        elif i.status != "Complete":
            return False
            

def main():
    stalk = beanstalkc.Connection()
    req_tube = "game-requests-%s" % game_name
    stalk.use(req_tube)
    clients = Client.objects.filter(eligible=True).filter(embargoed=False)[:10]
    results = skedRoundRobin(clients, 2, stalk)
    temp = validateResults(results)
    while not temp:
        temp = validateResults(results)
    

if __name__ == "__main__":
    main()
